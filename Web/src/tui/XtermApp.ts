// XtermApp.ts — 终端层主组合（xterm.js 版）
// 对应 main.py 的 NagatoInterface
// 关键变化：用 xterm.js + ANSI 序列代替 Canvas/DOM 自绘
// 全量重绘：每帧 cursor home + 清屏 + 写新 frame；alt screen 防止 scrollback 堆积

import type { Terminal } from "@xterm/xterm";

import type { GameEngine } from "../core/engine";
import { renderStatusBar } from "./render/status-bar";
import { renderPanel } from "./render/panel";
import { renderOptionsBody } from "./render/options";
import { renderInputBar } from "./render/input-bar";
import { wrapToWidth, padRightVisible, RESET, wrap } from "./render/ansi";
import { LogBuffer } from "./log-buffer";

const MIKURU_TRIGGER = "可不只是乌龟啊";
const REBOOT_SCENES = new Set(["c1b_morning_reboot", "c4a_loop_start"]);

export type ExitCode = "GAME_CLEARED" | string;

export interface AppCallbacks {
  exit(code: ExitCode): void;
  playBootMusic(seconds: number): void;
  playSceneBgm(sceneId: string): void;
}

export class XtermApp {
  private input = "";
  private cursorOn = true;
  private cursorTimer: ReturnType<typeof setInterval> | null = null;

  private waitOptionsHint: string | null = null;
  private waitingEnterAfterC4aFinal = false;
  private isPlaying = false;
  private lastSceneId: string | null = null;
  private scrollOffset = 0; // 从 log 底部往上偏移的"行数"
  private lastFrame = "";
  private logScrollbar: LogScrollbarState | null = null;
  private scrollbarEl: HTMLDivElement | null = null;
  private scrollbarThumbEl: HTMLDivElement | null = null;

  private logBuffer: LogBuffer;
  private removeKey: (() => void) | null = null;
  private removeResize: (() => void) | null = null;

  constructor(
    private term: Terminal,
    private engine: GameEngine,
    private initialSceneId: string | null,
    private isEnteredMikuru: boolean,
    private cb: AppCallbacks,
  ) {
    this.logBuffer = new LogBuffer({
      onChanged: () => this.refresh(),
      onLineWritten: (line) => this.handleLineWritten(line),
      onComplete: () => this.handleLogComplete(),
    });
  }

  start(): void {
    // alt screen + 隐藏光标（xterm 自己的光标）
    this.term.write("\x1b[?1049h\x1b[?25l\x1b[H\x1b[2J");
    const onKey = this.term.onKey((e) => this.handleKey(e.domEvent, e.key));
    const onResize = this.term.onResize(() => {
      this.lastFrame = "";
      this.refresh();
    });
    this.removeKey = () => onKey.dispose();
    this.removeResize = () => onResize.dispose();
    this.cursorTimer = setInterval(() => {
      this.cursorOn = !this.cursorOn;
      this.refresh();
    }, 500);

    if (!this.isEnteredMikuru) this.cb.playBootMusic(3.3);
    this.refreshUiForNewScene();
  }

  unmount(): void {
    if (this.cursorTimer) clearInterval(this.cursorTimer);
    this.cursorTimer = null;
    this.removeKey?.();
    this.removeResize?.();
    this.removeKey = null;
    this.removeResize = null;
    this.scrollbarEl?.remove();
    this.scrollbarEl = null;
    this.scrollbarThumbEl = null;
    // 退出 alt screen + 显示光标
    this.term.write("\x1b[?25h\x1b[?1049l");
  }

  // ── 状态机分支（main.py 1:1） ──
  private refreshUiForNewScene(): void {
    const scene = this.engine.current_scene();
    if (REBOOT_SCENES.has(scene.id)) this.cb.playBootMusic(3.3);
    else this.cb.playSceneBgm(this.engine.state.current_scene_id);

    this.isPlaying = true;
    this.scrollOffset = 0;
    this.logBuffer.playScene(scene, this.engine.state.location);

    // 学姐特化（main.py:165-170）
    if (
      this.isEnteredMikuru &&
      this.initialSceneId === "c3b_store_revisit" &&
      this.lastSceneId === null
    ) {
      this.logBuffer.flush();
    }
  }

  private handleLogComplete(): void {
    this.isPlaying = false;
    const sid = this.engine.state.current_scene_id;
    if (sid === "c4a_final") {
      this.waitOptionsHint = "【 请按回车键继续 】";
      this.waitingEnterAfterC4aFinal = true;
      this.input = "";
      this.refresh();
      return;
    }
    if (this.engine.state.game_over) {
      this.waitOptionsHint = "【 请按回车键继续 】";
      this.input = "";
      this.refresh();
      return;
    }
    const pending = this.engine.state.pending_scene;
    if (pending) {
      this.engine.state.pending_scene = null;
      this.engine._enter_scene(pending);
      this.lastSceneId = this.engine.state.current_scene_id;
      this.refreshUiForNewScene();
      return;
    }
    this.waitOptionsHint = null;
    this.input = "";
    this.refresh();
    if (sid === "mikuru_game") this.cb.exit("mikuru_game");
  }

  private handleLineWritten(line: string): void {
    if (line.includes(MIKURU_TRIGGER) && !this.isEnteredMikuru) {
      queueMicrotask(() => this.cb.exit(this.engine.state.current_scene_id));
    }
  }

  // ── 输入处理 ──
  private handleKey(e: KeyboardEvent, key: string): void {
    if (this.engine.state.game_over && !this.isPlaying) {
      // 等回车进 GAME_CLEARED
      if (e.key === "Enter") {
        this.cb.exit("GAME_CLEARED");
        return;
      }
      return;
    }
    if (this.waitingEnterAfterC4aFinal) {
      if (e.key === "Enter") {
        this.waitingEnterAfterC4aFinal = false;
        this.waitOptionsHint = null;
        const pending = this.engine.state.pending_scene;
        this.engine.state.pending_scene = null;
        if (pending) {
          this.lastSceneId = pending;
          this.engine._enter_scene(pending);
          this.refreshUiForNewScene();
        }
      }
      return;
    }

    // 滚动键（main.py:316-337）
    if (e.key === "ArrowUp") {
      this.scrollOffset += 1;
      this.refresh();
      return;
    }
    if (e.key === "ArrowDown") {
      this.scrollOffset = Math.max(0, this.scrollOffset - 1);
      this.refresh();
      return;
    }
    if (e.key === "PageUp") {
      this.scrollOffset += 10;
      this.refresh();
      return;
    }
    if (e.key === "PageDown") {
      this.scrollOffset = Math.max(0, this.scrollOffset - 10);
      this.refresh();
      return;
    }

    if (e.key === "Enter") {
      const raw = this.input.trim();
      this.input = "";
      this.scrollOffset = 0;
      this.refresh();
      if (raw === "") return;
      this.processCommand(raw);
      return;
    }
    if (e.key === "Backspace") {
      this.input = this.input.slice(0, -1);
      this.refresh();
      return;
    }
    // xterm 的 onKey 把可打印字符放在 e.key 是单字符 + key 是该字符
    if (key && key.length === 1 && e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
      this.input += key;
      this.refresh();
    }
  }

  private processCommand(raw: string): void {
    if (raw.toLowerCase() === "skip" && this.isPlaying) {
      this.logBuffer.flush();
      return;
    }
    if (this.isPlaying) return;

    // 玩家输入回显（components.py 等价：绿色 prompt + 玩家输入）
    this.logBuffer.pushLine(`${wrap("kyon@SOS:~$", { fg: "green", bold: true })} ${raw}`);

    const [entries, isCommand] = this.engine.process_input(raw);
    if (
      this.engine.state.current_scene_id !== this.lastSceneId &&
      !isCommand
    ) {
      this.refreshUiForNewScene();
    } else {
      if (isCommand) {
        this.logBuffer.pushEntriesImmediately(entries);
      } else {
        this.isPlaying = true;
        this.logBuffer.playAppend(entries);
      }
    }
    this.lastSceneId = this.engine.state.current_scene_id;
  }

  // ── 全量重绘 ──
  refresh(): void {
    const cols = this.term.cols;
    const rows = this.term.rows;
    if (cols < 4 || rows < 6) return;

    const frame = this.composeFrame(cols, rows);
    if (frame === this.lastFrame) return;
    this.lastFrame = frame;
    // cursor home → write 全屏；alt screen 下原位覆盖
    this.term.write(`\x1b[H${frame}`);
    this.updateScrollbarOverlay(cols, rows);
  }

  private composeFrame(cols: number, rows: number): string {
    // 高度划分对应 components.py：status 2 行 / inputbar 3 行 / 中间给 log+options
    // StatusBar.compose() 实际 yield 3 个 Horizontal，第三行为空。
    const statusRows = 3;
    const inputRows = 3;
    const mid = Math.max(3, rows - statusRows - inputRows);
    const logRows = Math.max(3, Math.floor(mid * 0.7));
    const optionsRows = Math.max(2, mid - logRows);
    const panelWidth = Math.max(2, cols - 2); // #log-container/#console-container: margin 0 1

    const out: string[] = [];

    // status bar
    for (const line of renderStatusBar(cols)) {
      out.push(line);
    }
    while (out.length < statusRows) out.push("");

    // log panel — 边框占 2 行，内部 logRows-2
    const logInner = logRows - 2;
    const logTextWidth = Math.max(1, panelWidth - 2 - 2 - TEXTUAL_SCROLLBAR_WIDTH);
    const wrappedLog: string[] = [];
    for (const ansiLine of this.logBuffer.lines) {
      // panel 内宽 = cols - 2(border) - 2(padding)；RichLog 右侧保留 scrollbar gutter
      for (const seg of wrapToWidth(ansiLine, logTextWidth)) {
        wrappedLog.push(seg);
      }
    }
    const totalLogLines = wrappedLog.length;
    const visible = Math.min(logInner, totalLogLines);
    const scroll = Math.max(0, Math.min(this.scrollOffset, totalLogLines - visible));
    const start = Math.max(0, totalLogLines - visible - scroll);
    const visibleLogLines = wrappedLog.slice(start, start + visible);
    while (visibleLogLines.length < logInner) visibleLogLines.push("");
    const logBody = addScrollbarGutter(visibleLogLines, logTextWidth);
    this.logScrollbar = {
      total: totalLogLines,
      visible,
      scroll,
      row: statusRows + 1,
      rows: logInner,
      col: 3 + logTextWidth,
      cols: TEXTUAL_SCROLLBAR_WIDTH,
    };
    const logPanel = renderPanel(logBody.join("\n"), panelWidth, {
      borderColor: "dark_green",
      titleColor: "dark_green",
    });
    out.push(...logPanel.slice(0, logRows).map((line) => withHorizontalMargin(line, cols)));
    while (out.length < statusRows + logRows) out.push("");

    // options panel
    // 剧情还在打字机播放中时不渲染当前场景的选项——原版 (main.py) 在
    // _on_log_complete 之前不调用 render_options，玩家会先看完剧情再看到
    // 选项；这里没有显式 clear，要主动按 isPlaying gating。
    let optionsBody: string[];
    if (this.waitOptionsHint) {
      optionsBody = [this.waitOptionsHint];
    } else if (this.isPlaying) {
      optionsBody = [];
    } else {
      const scene = this.engine.current_scene();
      const available = scene.choices.filter((c) => this.engine._choice_available(c));
      optionsBody = renderOptionsBody(available, scene.commands, scene.hint);
    }
    const optionsInner = optionsRows - 2;
    while (optionsBody.length < optionsInner) optionsBody.push("");
    if (optionsBody.length > optionsInner) {
      optionsBody = optionsBody.slice(0, optionsInner);
    }
    const optionsPanel = renderPanel(optionsBody.join("\n"), panelWidth, {
      borderColor: "dark_green",
      titleColor: "dark_green",
    });
    out.push(...optionsPanel.slice(0, optionsRows).map((line) => withHorizontalMargin(line, cols)));
    while (out.length < statusRows + logRows + optionsRows) out.push("");

    // input bar — Textual InputBar 高度为 3，顶部有深绿色 border
    out.push(wrap("─".repeat(cols), { fg: "dark_green" }));
    const inputLine = renderInputBar({ value: this.input, cursorOn: this.cursorOn });
    out.push(padRightVisible(" " + inputLine, cols));
    out.push("");
    while (out.length < rows) out.push("");

    // 每行用 \x1b[K 清到行末再换行；末行不补换行
    return out
      .slice(0, rows)
      .map((l) => `${l}${RESET}\x1b[K`)
      .join("\r\n");
  }

  private updateScrollbarOverlay(cols: number, rows: number): void {
    const state = this.logScrollbar;
    const host = this.term.element?.parentElement;
    const screen = this.term.element?.querySelector<HTMLElement>(".xterm-screen");
    if (!state || !host || !screen || state.total <= state.visible || state.rows <= 0) {
      if (this.scrollbarEl) this.scrollbarEl.style.display = "none";
      return;
    }
    if (!this.scrollbarEl) {
      this.scrollbarEl = document.createElement("div");
      this.scrollbarEl.className = "sos-textual-scrollbar";
      const track = document.createElement("div");
      track.className = "sos-textual-scrollbar-track";
      const thumb = document.createElement("div");
      thumb.className = "sos-textual-scrollbar-thumb";
      this.scrollbarEl.append(track, thumb);
      this.scrollbarThumbEl = thumb;
      host.appendChild(this.scrollbarEl);
    }

    // 用 boundingClientRect 拿"显示尺寸"——main.ts 里给 .xterm 套了 CSS scale
    // 让 canvas 撑满 terminal viewport，scrollbar 也必须按缩放后的 cell 尺寸定位。
    // 同时 .xterm 上有 translate(padX, padY) 让 canvas 居中在 terminal viewport
    // 内，scrollbar 的 left/top 是相对 host(.sos-terminal-viewport) 的——必须把
    // canvas 在 host 内的偏移加进去，否则 scrollbar 整体偏左/偏上。
    const rect = screen.getBoundingClientRect();
    const hostRect = host.getBoundingClientRect();
    const offsetX = rect.left - hostRect.left;
    const offsetY = rect.top - hostRect.top;
    const screenW = rect.width || parseCssPx(screen.style.width, rect.width);
    const screenH = rect.height || parseCssPx(screen.style.height, rect.height);
    const cellW = screenW / cols;
    const cellH = screenH / rows;
    const top = offsetY + state.row * cellH;
    const height = state.rows * cellH;
    const left = offsetX + state.col * cellW;
    const width = state.cols * cellW;

    const maxScroll = Math.max(1, state.total - state.visible);
    const topPosition = Math.max(0, state.total - state.visible - state.scroll);
    const thumbH = Math.max(cellH, height * (state.visible / state.total));
    const thumbTop = (height - thumbH) * (topPosition / maxScroll);

    this.scrollbarEl.style.display = "block";
    this.scrollbarEl.style.left = `${left}px`;
    this.scrollbarEl.style.top = `${top}px`;
    this.scrollbarEl.style.width = `${width}px`;
    this.scrollbarEl.style.height = `${height}px`;
    if (this.scrollbarThumbEl) {
      this.scrollbarThumbEl.style.top = `${thumbTop}px`;
      this.scrollbarThumbEl.style.height = `${thumbH}px`;
      // Textual ansi-dark 的 scrollbar 是用 █ 字符堆叠出来的——每个 cell 是
      // 一块。CSS 用 repeating-linear-gradient 在 thumb 上按 cellH 画水平分隔。
      this.scrollbarThumbEl.style.backgroundImage = `repeating-linear-gradient(to bottom, rgba(225,226,210,0.85) 0, rgba(225,226,210,0.85) ${cellH - 1}px, rgba(0,0,0,0.55) ${cellH - 1}px, rgba(0,0,0,0.55) ${cellH}px)`;
    }
  }
}

interface LogScrollbarState {
  total: number;
  visible: number;
  scroll: number;
  row: number;
  rows: number;
  col: number;
  cols: number;
}

function parseCssPx(value: string, fallback: number): number {
  const n = Number.parseFloat(value);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function addScrollbarGutter(
  lines: string[],
  textWidth: number,
): string[] {
  return lines.map((line) => `${padRightVisible(line, textWidth)}${" ".repeat(TEXTUAL_SCROLLBAR_WIDTH)}`);
}

function withHorizontalMargin(line: string, width: number): string {
  return padRightVisible(` ${line}`, width);
}

const TEXTUAL_SCROLLBAR_WIDTH = 2;
