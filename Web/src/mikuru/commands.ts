// commands.ts — Mikuru 命令派发
// 与 mikuru.py:418-501 1:1

import type { MikuruState } from "./state";

export interface CommandCallbacks {
  exit(): void;
  showFeedback(text: string, color: string): void;
  onKill(count: number): void;
}

export function dispatchCommand(s: MikuruState, raw: string, cb: CommandCallbacks): void {
  const val = raw.trim().toLowerCase();

  if (!s.game_active) {
    if (val === "quit") cb.exit();
    else cb.showFeedback("Game over. Type 'quit' to exit.", "yellow");
    return;
  }

  // 纯 wasd 字符串：逐字符移动
  if (val.length > 0 && /^[wasd]+$/.test(val)) {
    for (const ch of val) {
      if (ch === "w") s.py = Math.max(0, s.py - 1);
      else if (ch === "s") s.py = Math.min(s.map_h - 3, s.py + 1);
      else if (ch === "a") s.px = Math.max(0, s.px - 1);
      else if (ch === "d") s.px = Math.min(s.map_w - 5, s.px + 1);
    }
    cb.showFeedback(`Move:[${val.toUpperCase()}]`, "cyan");
    return;
  }

  if (val === "attack" || val === "fire ball" || val === "ice ball") {
    const px_start = s.px + 5;
    const py_start = s.py + 1;
    s.player_projectiles.push({
      float_x: px_start,
      float_y: py_start,
      x: px_start,
      y: py_start,
      vx: 2.0,
      vy: 0.0,
      type: val,
      damage: val === "attack" ? 10 : val === "fire ball" ? 25 : 5,
      freeze: val === "ice ball" ? 4 : 0,
    });
    cb.showFeedback(`Cast:${val.toUpperCase()}!`, "cyan");
    return;
  }

  if (val === "mikuru beam") {
    if (s.beam_ready) {
      s.beam_active_frames = 3;
      const killed = s.enemies.length;
      s.enemies.length = 0;
      s.enemy_projectiles.length = 0;
      s.player_projectiles.length = 0;
      cb.onKill(killed);
      s.beam_charge = 0;
      s.beam_ready = false;
      cb.showFeedback("MIKURU BEAM!!!", "#33ff33");
    } else {
      cb.showFeedback("Beam charging!", "red");
    }
    return;
  }

  if (val === "classified") {
    if (s.classified_cd === 0) {
      const px_start = s.px + 5;
      const py_start = s.py + 1;
      s.player_projectiles.push({
        float_x: px_start,
        float_y: py_start,
        x: px_start,
        y: py_start,
        vx: 2.0,
        vy: 0.0,
        type: "classified",
        damage: 40,
        freeze: 0,
      });
      s.classified_cd = 5;
      cb.showFeedback("CLASSIFIED SHOT!", "yellow");
    } else {
      cb.showFeedback(`classified CD ${s.classified_cd.toFixed(1)}s`, "red");
    }
    return;
  }

  if (val === "tea time") {
    if (s.teatime_cd === 0) {
      s.player_hp = Math.min(100, s.player_hp + 20);
      s.teatime_cd = 8;
      cb.showFeedback("Tea Time +20 HP!", "green");
    } else {
      cb.showFeedback(`tea time CD ${s.teatime_cd.toFixed(1)}s`, "red");
    }
    return;
  }

  cb.showFeedback("Invalid cmd.", "red");
}
