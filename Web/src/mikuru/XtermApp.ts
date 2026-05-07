// mikuru/XtermApp.ts — Mikuru 打字生存小游戏（xterm 版）
// 与 Engine/mikuru.py 对齐：100ms engine_tick / 500ms ai_tick / 1000ms clock
// UI 也用 ANSI 自绘到 xterm，2x2 grid（RADAR / STATUS / OPS / TERMINAL）

import type { Terminal } from "@xterm/xterm";
import { MikuruState } from "./state";
import { MIKURU_ART } from "./types";
import { aiTick, engineTick } from "./physics";
import { dispatchCommand } from "./commands";
import { wrap, padRightVisible, RESET, visibleWidth } from "../tui/render/ansi";

const ENGINE_INTERVAL_MS = 100;
const AI_INTERVAL_MS = 500;
const CLOCK_INTERVAL_MS = 1000;
const HIT_FLASH_MS = 100;

// 颜色对应 mikuru.py 中的 markup
const C = {
  player: "magenta",   // bold magenta
  melee: "red",
  ranged: "yellow",
  freeze: "cyan",
  proj: "yellow",
  attack: "white",
  fire_ball: "red",
  ice_ball: "cyan",
  classified: "magenta",
  beam: "cyan",
  border: "green",
  fg: "green",
} as const;

const OPS_LINES: ReadonlyArray<string> = [
  wrap("> TACTICS <", { bold: true, fg: "white" }),
  `${wrap("wasd", { fg: "white" })}        : Move`,
  `${wrap("attack", { fg: "white" })}      : Homing      (DMG:10)`,
  `${wrap("fire ball", { fg: "white" })}   : Burst       (DMG:25)`,
  `${wrap("ice ball", { fg: "white" })}    : Freeze      (DMG:5/2s)`,
  `${wrap("mikuru beam", { fg: "white" })} : Ultimate    (Cost:10)`,
  `${wrap("classified", { fg: "white" })}  : Heavy Shot  (DMG:40, CD:5s)`,
  `${wrap("tea time", { fg: "white" })}    : Heal        (HP+20, CD:8s)`,
];

export class MikuruXtermApp {
  private state = new MikuruState();
  private rafId: number | null = null;
  private lastT = 0;
  private accE = 0;
  private accAi = 0;
  private accC = 0;
  private hitFlashUntil = 0;
  private exitTimer: ReturnType<typeof setTimeout> | null = null;

  private input = "";
  private feedback: Array<{ text: string; color: string }> = [{ text: "Ready.", color: "white" }];
  private gameOverVictory = false;

  private removeKey: (() => void) | null = null;
  private removeResize: (() => void) | null = null;

  constructor(private term: Terminal, private onExit: () => void) {}

  start(): void {
    this.term.write("\x1b[?1049h\x1b[?25l\x1b[H\x1b[2J");
    const onKey = this.term.onKey((e) => this.handleKey(e.domEvent, e.key));
    const onResize = this.term.onResize(() => this.refresh());
    this.removeKey = () => onKey.dispose();
    this.removeResize = () => onResize.dispose();

    this.lastT = performance.now();
    this.rafId = requestAnimationFrame(this.frame);
  }

  unmount(): void {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId);
    this.rafId = null;
    if (this.exitTimer) clearTimeout(this.exitTimer);
    this.removeKey?.();
    this.removeResize?.();
    this.term.write("\x1b[?25h\x1b[?1049l");
  }

  // ── 输入 ──
  private handleKey(e: KeyboardEvent, key: string): void {
    if (e.key === "Enter") {
      const raw = this.input;
      this.input = "";
      this.handleInput(raw);
      return;
    }
    if (e.key === "Backspace") {
      this.input = this.input.slice(0, -1);
      return;
    }
    if (key && key.length === 1 && e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
      this.input += key;
    }
  }

  private handleInput(raw: string): void {
    dispatchCommand(this.state, raw, {
      exit: () => this.exitNow(),
      showFeedback: (t, c) => this.pushFb(t, c),
      onKill: (n) => this.handleKill(n),
    });
  }

  private pushFb(text: string, color: string): void {
    this.feedback.push({ text, color });
    while (this.feedback.length > 3) this.feedback.shift();
  }

  private handleKill(count: number): void {
    this.state.kill_count += count;
    if (!this.state.beam_ready) {
      this.state.beam_charge = Math.min(10, this.state.beam_charge + count);
      if (this.state.beam_charge === 10) this.state.beam_ready = true;
    }
  }

  private onPlayerHit(damage: number): void {
    this.state.player_hp -= damage;
    this.hitFlashUntil = performance.now() + HIT_FLASH_MS;
    if (this.state.player_hp <= 0) this.gameOver(false);
  }

  private gameOver(victory: boolean): void {
    this.state.game_active = false;
    this.gameOverVictory = victory;
    this.feedback = [{ text: "Game over. Type 'quit' to exit.", color: "yellow" }];
    this.exitTimer = setTimeout(() => this.exitNow(), 3000);
  }

  private exitNow(): void {
    this.unmount();
    this.onExit();
  }

  // ── RAF 循环 ──
  private frame = (now: number): void => {
    const dt = now - this.lastT;
    this.lastT = now;
    this.accE += dt;
    this.accAi += dt;
    this.accC += dt;

    // 自适应 map_w / map_h（基于 RADAR 区域字符尺寸）
    const cols = this.term.cols;
    const rows = this.term.rows;
    const radarLayout = this.layout(cols, rows).radar;
    this.state.map_w = Math.max(10, radarLayout.w - 4); // border + .box padding 0 1
    this.state.map_h = Math.max(4, radarLayout.h - 2);
    this.state.px = Math.max(0, Math.min(this.state.map_w - 5, this.state.px));
    this.state.py = Math.max(0, Math.min(this.state.map_h - 3, this.state.py));

    while (this.accE >= ENGINE_INTERVAL_MS) {
      engineTick(this.state, {
        onPlayerHit: (d) => this.onPlayerHit(d),
        onKill: (n) => this.handleKill(n),
        showFeedback: (t, c) => this.pushFb(t, c),
      });
      this.accE -= ENGINE_INTERVAL_MS;
    }
    while (this.accAi >= AI_INTERVAL_MS) {
      aiTick(this.state, {
        onPlayerHit: (d) => this.onPlayerHit(d),
        onKill: (n) => this.handleKill(n),
        showFeedback: (t, c) => this.pushFb(t, c),
      });
      this.accAi -= AI_INTERVAL_MS;
    }
    while (this.accC >= CLOCK_INTERVAL_MS) {
      this.tickClock();
      this.accC -= CLOCK_INTERVAL_MS;
    }

    if (this.state.beam_active_frames > 0) this.state.beam_active_frames -= 1;

    this.refresh();
    this.rafId = requestAnimationFrame(this.frame);
  };

  private tickClock(): void {
    if (!this.state.game_active) return;
    if (this.state.classified_cd > 0) this.state.classified_cd -= 1;
    if (this.state.teatime_cd > 0) this.state.teatime_cd -= 1;
    this.state.time_elapsed += 1;
    if (this.state.time_elapsed >= this.state.victory_time) this.gameOver(true);
  }

  // ── 布局 ──
  private layout(cols: number, rows: number) {
    // #crt-monitor: width/height 96%, border double；内部 2x2 grid: 5fr/2fr, 2fr/1fr
    const outerW = Math.max(16, Math.floor(cols * 0.96));
    const outerH = Math.max(8, Math.floor(rows * 0.96));
    const outerX = Math.max(0, Math.floor((cols - outerW) / 2));
    const outerY = Math.max(0, Math.floor((rows - outerH) / 2));
    const gridX = outerX + 1;
    const gridY = outerY + 1;
    const gridW = Math.max(4, outerW - 2);
    const gridH = Math.max(4, outerH - 2);
    const colL = Math.floor(gridW * 5 / 7);
    const colR = gridW - colL;
    const rowT = Math.floor(gridH * 2 / 3);
    const rowB = gridH - rowT;
    return {
      outer:    { x: outerX,      y: outerY,      w: outerW, h: outerH },
      radar:    { x: gridX,       y: gridY,       w: colL,   h: rowT },
      status:   { x: gridX + colL, y: gridY,       w: colR,   h: rowT },
      ops:      { x: gridX,       y: gridY + rowT, w: colL,   h: rowB },
      terminal: { x: gridX + colL, y: gridY + rowT, w: colR,   h: rowB },
    };
  }

  // ── 绘制 ──
  private refresh(): void {
    const cols = this.term.cols;
    const rows = this.term.rows;
    if (cols < 16 || rows < 8) return;
    const lay = this.layout(cols, rows);
    const grid = makeBlankGrid(cols, rows);
    const inFlash = performance.now() < this.hitFlashUntil;
    const borderC = inFlash ? "red" : "green";

    drawDoubleBox(grid, lay.outer.x, lay.outer.y, lay.outer.w, lay.outer.h, borderC);
    drawBox(grid, lay.radar.x, lay.radar.y, lay.radar.w, lay.radar.h, " RADAR ", borderC);
    drawBox(grid, lay.status.x, lay.status.y, lay.status.w, lay.status.h, " STATUS ", borderC);
    drawBox(grid, lay.ops.x, lay.ops.y, lay.ops.w, lay.ops.h, " OPS MANUAL ", borderC);
    drawBox(grid, lay.terminal.x, lay.terminal.y, lay.terminal.w, lay.terminal.h, " TERMINAL ", borderC);

    // RADAR
    this.drawRadar(grid, lay.radar.x + 2, lay.radar.y + 1);
    // STATUS
    this.drawStatus(grid, lay.status.x + 2, lay.status.y + 1, lay.status.w - 4);
    // OPS
    for (let i = 0; i < OPS_LINES.length; i++) {
      writeAnsi(grid, lay.ops.x + 2, lay.ops.y + 1 + i, OPS_LINES[i], lay.ops.w - 4);
    }
    // TERMINAL
    this.drawTerminal(grid, lay.terminal.x + 2, lay.terminal.y + 1, lay.terminal.w - 4, lay.terminal.h - 2);

    // game over 横幅覆盖
    if (!this.state.game_active) {
      const lines = this.gameOverVictory
        ? [">>> MISSION ACCOMPLISHED <<<", "SURVIVED 3 MINUTES!"]
        : [">>> SYSTEM FAILURE <<<", "MIKURU DEFEATED."];
      const color = this.gameOverVictory ? "green" : "red";
      const cx = lay.radar.x + Math.floor(lay.radar.w / 2);
      const cy = lay.radar.y + Math.floor(lay.radar.h / 2) - 1;
      for (let i = 0; i < lines.length; i++) {
        const styled = wrap(lines[i], { bold: true, fg: color });
        const startX = cx - Math.floor(visibleWidth(lines[i]) / 2);
        writeAnsi(grid, startX, cy + i, styled, lay.radar.w - 2);
      }
    }

    const frame = grid.map((row) => row.join("") + RESET + "\x1b[K").join("\r\n");
    this.term.write(`\x1b[H${frame}`);
  }

  private drawRadar(grid: string[][], originX: number, originY: number): void {
    const s = this.state;
    if (!s.game_active) return;

    // 玩家
    for (let i = 0; i < MIKURU_ART.length; i++) {
      const row = MIKURU_ART[i];
      for (let j = 0; j < row.length; j++) {
        const yy = originY + s.py + i;
        const xx = originX + s.px + j;
        if (inBounds(grid, xx, yy)) grid[yy][xx] = wrap(row[j], { fg: C.player, bold: true });
      }
    }
    // 敌人
    for (const e of s.enemies) {
      const color = e.freeze > 0 ? C.freeze : (e.type === "ranged" ? C.ranged : C.melee);
      const sym = e.type === "ranged" ? "<R>" : "<M>";
      for (let j = 0; j < sym.length; j++) {
        const xx = originX + e.x + j;
        const yy = originY + e.y;
        if (inBounds(grid, xx, yy)) grid[yy][xx] = wrap(sym[j], { fg: color, bold: true });
      }
    }
    // 敌方弹幕
    for (const p of s.enemy_projectiles) {
      const xx = originX + p.x;
      const yy = originY + p.y;
      if (inBounds(grid, xx, yy)) {
        const ch = p.vx !== 0 ? "-" : "|";
        grid[yy][xx] = wrap(ch, { fg: C.proj, bold: true });
      }
    }
    // 我方弹幕
    for (const p of s.player_projectiles) {
      const xx = originX + p.x;
      const yy = originY + p.y;
      if (inBounds(grid, xx, yy)) {
        let ch = "*"; let color: string = C.attack;
        if (p.type === "attack") { ch = ">"; color = C.attack; }
        else if (p.type === "fire ball") { ch = "@"; color = C.fire_ball; }
        else if (p.type === "classified") { ch = "!"; color = C.classified; }
        else { ch = "*"; color = C.ice_ball; }
        grid[yy][xx] = wrap(ch, { fg: color, bold: true });
      }
    }
    // 激光
    if (s.beam_active_frames > 0) {
      const beamY = s.py + 1;
      for (let x = s.px + 5; x < s.map_w; x++) {
        const yy = originY + beamY;
        const xx = originX + x;
        if (inBounds(grid, xx, yy)) grid[yy][xx] = wrap("=", { fg: C.beam, bold: true });
        if (x % 2 === 0) {
          if (inBounds(grid, xx, yy - 1)) grid[yy - 1][xx] = wrap("+", { fg: C.beam });
          if (inBounds(grid, xx, yy + 1)) grid[yy + 1][xx] = wrap("+", { fg: C.beam });
        }
      }
    }
  }

  private drawStatus(grid: string[][], originX: number, originY: number, w: number): void {
    const s = this.state;
    const m = Math.floor(s.time_elapsed / 60);
    const ss = s.time_elapsed % 60;
    const beamText = s.beam_ready ? wrap("READY!", { fg: "white", bold: true }) : `${s.beam_charge}/10`;
    const bar = `<${"#".repeat(s.beam_charge)}${"-".repeat(10 - s.beam_charge)}>`;
    const lines: string[] = [
      wrap("OP: Mikuru", { bold: true, fg: "green" }),
      wrap(`HP: ${s.player_hp}/100`, { bold: true, fg: "green" }),
      wrap("===========================", { fg: "green" }),
      wrap(`TIME: ${pad2(m)}:${pad2(ss)}`, { bold: true, fg: "green" }),
      wrap(`FOES: ${s.enemies.length}`, { bold: true, fg: "green" }),
      wrap(`KILL: ${s.kill_count}`, { bold: true, fg: "green" }),
      wrap("===========================", { fg: "green" }),
      wrap("BEAM:", { bold: true, fg: "green" }),
      wrap(bar, { fg: "green" }),
      beamText,
      wrap("===========================", { fg: "green" }),
      wrap("SKILL CD:", { bold: true, fg: "green" }),
      wrap(`classified: ${s.classified_cd.toFixed(1)}s`, { fg: "green" }),
      wrap(`tea time : ${s.teatime_cd.toFixed(1)}s`, { fg: "green" }),
      wrap("===========================", { fg: "green" }),
      wrap("Messages:", { bold: true, fg: "green" }),
    ];
    for (const f of this.feedback) lines.push(wrap(f.text, { fg: f.color }));
    for (let i = 0; i < lines.length; i++) {
      writeAnsi(grid, originX, originY + i, lines[i], w);
    }
  }

  private drawTerminal(grid: string[][], originX: number, originY: number, w: number, h: number): void {
    const cy = originY + Math.floor(h / 2);
    const label = "root@Mikuru:~#";
    const lx = originX + Math.floor((w - label.length) / 2);
    writeAnsi(grid, lx, cy - 1, wrap(label, { bold: true, fg: "green" }), w);
    const inputStr = this.input;
    const ix = originX + Math.max(0, Math.floor((w - inputStr.length) / 2));
    writeAnsi(grid, ix, cy + 1, wrap(inputStr, { fg: "white" }), w);
    // 下划线
    for (let x = originX; x < originX + w; x++) {
      if (inBounds(grid, x, cy + 2)) grid[cy + 2][x] = wrap("─", { fg: "green" });
    }
  }
}

// ── Grid 工具 ──
function makeBlankGrid(cols: number, rows: number): string[][] {
  const g: string[][] = [];
  for (let y = 0; y < rows; y++) {
    const row: string[] = [];
    for (let x = 0; x < cols; x++) row.push(" ");
    g.push(row);
  }
  return g;
}

function inBounds(grid: string[][], x: number, y: number): boolean {
  return y >= 0 && y < grid.length && x >= 0 && x < grid[0].length;
}

function drawDoubleBox(grid: string[][], x0: number, y0: number, w: number, h: number, color: string): void {
  const wrap_ = (ch: string) => wrap(ch, { fg: color, bold: true });
  for (let i = 0; i < w; i++) {
    if (inBounds(grid, x0 + i, y0)) grid[y0][x0 + i] = wrap_("═");
    if (inBounds(grid, x0 + i, y0 + h - 1)) grid[y0 + h - 1][x0 + i] = wrap_("═");
  }
  for (let j = 0; j < h; j++) {
    if (inBounds(grid, x0, y0 + j)) grid[y0 + j][x0] = wrap_("║");
    if (inBounds(grid, x0 + w - 1, y0 + j)) grid[y0 + j][x0 + w - 1] = wrap_("║");
  }
  if (inBounds(grid, x0, y0)) grid[y0][x0] = wrap_("╔");
  if (inBounds(grid, x0 + w - 1, y0)) grid[y0][x0 + w - 1] = wrap_("╗");
  if (inBounds(grid, x0, y0 + h - 1)) grid[y0 + h - 1][x0] = wrap_("╚");
  if (inBounds(grid, x0 + w - 1, y0 + h - 1)) grid[y0 + h - 1][x0 + w - 1] = wrap_("╝");
}

function drawBox(grid: string[][], x0: number, y0: number, w: number, h: number, title: string, color: string = "green"): void {
  const wrap_ = (ch: string) => wrap(ch, { fg: color, bold: true });
  const top = wrap_("━");
  const bot = wrap_("━");
  const ver = wrap_("┃");
  for (let i = 0; i < w; i++) {
    if (inBounds(grid, x0 + i, y0)) grid[y0][x0 + i] = top;
    if (inBounds(grid, x0 + i, y0 + h - 1)) grid[y0 + h - 1][x0 + i] = bot;
  }
  for (let j = 0; j < h; j++) {
    if (inBounds(grid, x0, y0 + j)) grid[y0 + j][x0] = ver;
    if (inBounds(grid, x0 + w - 1, y0 + j)) grid[y0 + j][x0 + w - 1] = ver;
  }
  if (inBounds(grid, x0, y0)) grid[y0][x0] = wrap_("┏");
  if (inBounds(grid, x0 + w - 1, y0)) grid[y0][x0 + w - 1] = wrap_("┓");
  if (inBounds(grid, x0, y0 + h - 1)) grid[y0 + h - 1][x0] = wrap_("┗");
  if (inBounds(grid, x0 + w - 1, y0 + h - 1)) grid[y0 + h - 1][x0 + w - 1] = wrap_("┛");
  // 标题嵌入顶边
  if (title) {
    const tx = x0 + Math.max(2, Math.floor((w - title.length) / 2));
    writeAnsi(grid, tx, y0, wrap(title, { fg: color, bold: true }), w);
  }
}

function writeAnsi(grid: string[][], x: number, y: number, ansiText: string, maxW: number): void {
  if (y < 0 || y >= grid.length) return;
  // 简化：把 ANSI 字符串按 visibleWidth 切分逐字符 — 但 ANSI 含转义 不能拆。
  // 这里直接把整段 ansiText 放在 (x, y) 这个格子；后续格子留空。
  // 因为 grid 单元是 string，xterm 渲染时会按字符宽度走。
  if (x < 0 || x >= grid[0].length) return;
  grid[y][x] = ansiText + RESET;
  // 用空字符串占用 maxW-1 个格子（避免被边框覆盖）
  // 注意：我们用空字符串而不是空格，这样它在 join 时不会输出空格遮盖背景
  const occupy = Math.min(maxW - 1, visibleWidth(ansiText) - 1);
  for (let i = 1; i <= occupy; i++) {
    if (x + i >= grid[0].length) break;
    grid[y][x + i] = "";
  }
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : `${n}`;
}
