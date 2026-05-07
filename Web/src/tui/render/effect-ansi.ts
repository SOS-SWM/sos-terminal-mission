// effect-ansi.ts — 把 LogEntry 渲染成单行 ANSI 字符串
// 1:1 对应 components.py 中 _format_entry / _effect_style_line / 17 种 EffectTag 的着色
//
// 输入：LogEntry（含 frontmatter / content / effect / timestamp）
// 输出：包含 ANSI 转义序列的字符串（不含换行；行末以 RESET 结尾）

import type { EffectTag, LogEntry } from "../../core/models";
import { wrap, wrapNested, RESET } from "./ansi";

// 把 frontmatter 与 content 组合成基础着色行（components.py:68-82）
function formatEntry(entry: LogEntry): string {
  const fm = entry.frontmatter;
  const content = entry.content;
  if (fm) {
    if (fm.startsWith("[") && fm.includes("]")) {
      const bracketEnd = fm.indexOf("]") + 1;
      const tsPart = fm.slice(0, bracketEnd);
      const rest = fm.slice(bracketEnd).trim();
      if (rest) {
        return `${wrap(tsPart, { fg: "green" })} ${wrap(rest, { fg: "green" })} ${content}`;
      }
      return `${wrap(tsPart, { fg: "green" })} ${content}`;
    }
    return `${wrap(fm, { fg: "yellow" })} ${content}`;
  }
  return content;
}

// 根据 effect 给整行包样式（components.py:84-112）
function applyEffect(entry: LogEntry, line: string): string {
  switch (entry.effect as EffectTag) {
    case "separator": {
      const width = Math.max(24, entry.text ? entry.text.length : 36);
      const rule = entry.text ? entry.text : "─".repeat(width);
      return wrap(rule, { fg: "cyan", dim: true });
    }
    case "warning":
      return wrapNested(line, { fg: "yellow", bold: true });
    case "success":
      return wrapNested(line, { fg: "green", bold: true });
    case "dim":
      return wrapNested(line, { dim: true });
    case "route_trace":
      return wrapNested(line, { fg: "cyan", bold: true });
    case "route_trace_ghost":
      return wrapNested(line, { fg: "cyan", dim: true });
    case "worldline_shift":
      return wrapNested(line, { fg: "green", bold: true });
    case "cursor_fast":
      return `${wrap(">", { fg: "cyan", bold: true })} ${line}`;
    case "glitch":
      return wrapNested(line, { fg: "magenta", bold: true });
    case "glitch_heavy":
      return wrapNested(line, { fg: "red", bold: true });
    case "flicker":
    case "jitter":
    case "reboot":
      return wrapNested(line, { fg: "white", bold: true });
    default:
      return line;
  }
}

export function renderEntryAnsi(entry: LogEntry): string {
  return applyEffect(entry, formatEntry(entry));
}

// 场景头：==================== <LOCATION> <TIMESTAMP> ====================
// components.py:236-241 一致
export function renderSceneHeader(location: string, timestamp: string): string {
  const loc = (location || "UNKNOWN").toUpperCase();
  const ts = timestamp || "UNKNOWN";
  return wrap(`==================== ${loc} ${ts} ====================`, {
    fg: "cyan",
    bold: true,
  });
}

export { RESET };
