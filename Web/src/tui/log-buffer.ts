// log-buffer.ts — 维护"已写出的日志行（ANSI 字符串）"+ 打字机播放器
// 对应 components.py:54-292（StoryLog 的 _play_log / flush_pending_entries / append）
// 与原 textual.RichLog 不同：这里只保存渲染后的 ANSI 字符串，由上层 XtermApp 统一全量重绘

import type { LogEntry } from "../core/models";
import { renderEntryAnsi } from "./render/effect-ansi";
import { wrap } from "./render/ansi";

const MIKURU_TRIGGER = "可不只是乌龟啊";

// components.py:117-139 完全一致的延迟公式
const EFFECT_MULTIPLIER: Record<string, number> = {
  instant: 0.0,
  typewriter_fast: 0.55,
  typewriter_slow: 1.7,
  cursor_fast: 0.3,
  separator: 0.35,
  route_trace: 0.7,
  route_trace_ghost: 0.85,
  glitch: 0.75,
  glitch_heavy: 0.6,
  flicker: 0.6,
  jitter: 0.9,
  worldline_shift: 1.15,
  warning: 1.05,
  success: 0.75,
  reboot: 1.3,
};

function lineDelaySeconds(entry: LogEntry, lineDelay: number): number {
  const text = entry.text;
  let asciiCount = 0;
  for (let i = 0; i < text.length; i++) {
    if (text.charCodeAt(i) < 128) asciiCount++;
  }
  const cjkCount = text.length - asciiCount;
  const baseDelay = cjkCount * 0.045 + lineDelay;
  const mul = EFFECT_MULTIPLIER[entry.effect] ?? 1.0;
  const speed = Math.max(entry.speed, 0.05);
  return baseDelay * mul * speed;
}

export interface LogBufferCallbacks {
  // 状态变更：行被写出 / 一段播放结束。上层据此触发重绘 + 检查 mikuru 触发。
  onChanged(): void;
  onLineWritten(line: string): void;
  onComplete(): void;
}

export class LogBuffer {
  // 已渲染（ANSI）行列表
  lines: string[] = [];

  private playTimer: ReturnType<typeof setTimeout> | null = null;
  private playEntries: LogEntry[] = [];
  private playIndex = 0;
  private lineDelay = 0.7;

  constructor(private cb: LogBufferCallbacks) {}

  isPlaying(): boolean {
    return this.playTimer !== null || this.playIndex < this.playEntries.length;
  }

  clear(): void {
    this.lines = [];
    this.cb.onChanged();
  }

  // 直接追加一行 ANSI（用于玩家回显、场景头）
  pushLine(line: string): void {
    this.lines.push(line);
    this.cb.onChanged();
    this.cb.onLineWritten(line);
  }

  // 立即写一组条目（command 响应 — 无延迟）
  pushEntriesImmediately(entries: LogEntry[]): void {
    this.stopTimer();
    for (const e of entries) {
      const line = renderEntryAnsi(e);
      this.lines.push(line);
      this.cb.onLineWritten(line);
    }
    this.cb.onChanged();
    this.cb.onComplete();
  }

  // 场景日志：清屏 + 头 + 逐行播放
  playScene(scene: { entries: LogEntry[] }, location: string | null): void {
    this.clear();
    const ts = scene.entries.find((e) => e.timestamp)?.timestamp ?? "UNKNOWN";
    const loc = (location ?? "UNKNOWN").toUpperCase();
    this.pushLine(
      wrap(`==================== ${loc} ${ts} ====================`, {
        fg: "cyan",
        bold: true,
      }),
    );
    this.playEntries_(scene.entries);
  }

  // 追加一组条目（场景延续，有打字机延迟）
  playAppend(entries: LogEntry[]): void {
    this.playEntries_(entries);
  }

  // 跳过当前播放队列：立即写出剩余条目；遇 MIKURU_TRIGGER 则停止 dump 并对后续条目重启 playLog
  flush(): void {
    this.stopTimer();
    if (this.playIndex >= this.playEntries.length) {
      this.cb.onComplete();
      return;
    }
    for (let i = this.playIndex; i < this.playEntries.length; i++) {
      const entry = this.playEntries[i];
      if (entry.kind === "player") continue;
      const line = renderEntryAnsi(entry);
      this.lines.push(line);
      this.cb.onLineWritten(line);
      if (line.includes(MIKURU_TRIGGER)) {
        this.cb.onChanged();
        this.playEntries_(this.playEntries.slice(i + 1));
        return;
      }
    }
    this.playIndex = this.playEntries.length;
    this.cb.onChanged();
    this.cb.onComplete();
  }

  // ── internal ──
  private stopTimer(): void {
    if (this.playTimer !== null) {
      clearTimeout(this.playTimer);
      this.playTimer = null;
    }
  }

  private playEntries_(entries: LogEntry[]): void {
    this.stopTimer();
    this.playEntries = entries.slice();
    this.playIndex = 0;
    if (this.playEntries.length === 0) {
      this.cb.onComplete();
      return;
    }
    const tick = (): void => {
      if (this.playIndex < this.playEntries.length) {
        const e = this.playEntries[this.playIndex];
        if (e.kind === "player") {
          this.playIndex++;
          tick();
          return;
        }
        const line = renderEntryAnsi(e);
        this.lines.push(line);
        this.cb.onLineWritten(line);
        this.cb.onChanged();
        this.playIndex++;
        const d = lineDelaySeconds(e, this.lineDelay);
        this.playTimer = setTimeout(tick, d * 1000);
      } else {
        this.stopTimer();
        this.cb.onComplete();
      }
    };
    tick();
  }
}
