// ANSI 颜色与样式常量，对齐 Rich 的颜色名。
// 所有面板都通过 wrap(...) 包装序列；xterm.js 直接渲染。

export const RESET = "\x1b[0m";

const FG: Record<string, string> = {
  default: "39",
  black: "30",
  red: "31",
  green: "32",
  yellow: "33",
  blue: "34",
  magenta: "35",
  cyan: "36",
  white: "37",
  bright_black: "90",
  bright_red: "91",
  bright_green: "92",
  bright_yellow: "93",
  bright_blue: "94",
  bright_magenta: "95",
  bright_cyan: "96",
  bright_white: "97",
  // Rich 的近似 256 色
  plum2: "38;5;183",
  grey70: "38;5;249",
  // SOS 项目专用色（components.py 中 border #1a4d1a / prompt #33cc33）
  dark_green: "38;2;26;77;26",
  prompt_green: "38;2;51;204;51",
  dim: "2",
};

const BG: Record<string, string> = {
  default: "49",
  black: "40",
  blue: "44",
  white: "47",
  bright_cyan: "106",
  bright_blue: "104",
  plum2: "48;5;183",
  grey70: "48;5;249",
  bright_magenta: "105",
  bright_yellow: "103",
};

export interface StyleSpec {
  fg?: string;
  bg?: string;
  bold?: boolean;
  italic?: boolean;
  reverse?: boolean;
  dim?: boolean;
  underline?: boolean;
}

export function style(spec: StyleSpec): string {
  const parts: string[] = [];
  if (spec.bold) parts.push("1");
  if (spec.dim) parts.push("2");
  if (spec.italic) parts.push("3");
  if (spec.underline) parts.push("4");
  if (spec.reverse) parts.push("7");
  if (spec.fg && FG[spec.fg]) parts.push(FG[spec.fg]!);
  if (spec.bg && BG[spec.bg]) parts.push(BG[spec.bg]!);
  if (parts.length === 0) return "";
  return `\x1b[${parts.join(";")}m`;
}

export function wrap(text: string, spec: StyleSpec): string {
  const open = style(spec);
  if (!open) return text;
  return `${open}${text}${RESET}`;
}

export function wrapNested(text: string, spec: StyleSpec): string {
  const open = style(spec);
  if (!open) return text;
  return `${open}${text.replaceAll(RESET, `${RESET}${open}`)}${RESET}`;
}

// 统计可见宽度（中日韩全角字符 = 2，半角 = 1，控制序列忽略）。
export function visibleWidth(text: string): number {
  let width = 0;
  let i = 0;
  while (i < text.length) {
    if (text[i] === "\x1b") {
      const idx = text.indexOf("m", i);
      if (idx === -1) break;
      i = idx + 1;
      continue;
    }
    const code = text.codePointAt(i)!;
    width += isWide(code) ? 2 : 1;
    i += code > 0xffff ? 2 : 1;
  }
  return width;
}

export function isWide(cp: number): boolean {
  // 简化：覆盖常用 CJK / 全角 / 假名 / 句读。
  return (
    (cp >= 0x1100 && cp <= 0x115f) ||
    (cp >= 0x2e80 && cp <= 0x303e) ||
    (cp >= 0x3041 && cp <= 0x33ff) ||
    (cp >= 0x3400 && cp <= 0x4dbf) ||
    (cp >= 0x4e00 && cp <= 0x9fff) ||
    (cp >= 0xa000 && cp <= 0xa4cf) ||
    (cp >= 0xac00 && cp <= 0xd7a3) ||
    (cp >= 0xf900 && cp <= 0xfaff) ||
    (cp >= 0xfe30 && cp <= 0xfe4f) ||
    (cp >= 0xff00 && cp <= 0xff60) ||
    (cp >= 0xffe0 && cp <= 0xffe6) ||
    (cp >= 0x20000 && cp <= 0x2fffd) ||
    (cp >= 0x30000 && cp <= 0x3fffd)
  );
}

// 把含可选外层 ANSI 包裹的文本按可见宽度切成多行。
// 假定 ANSI 序列只在最外层（前缀 + 末尾 \x1b[0m）；
// 内部还有其它 ANSI 时退化为单行（由 sliceByVisibleWidth 安全截断）。
export function wrapToWidth(text: string, width: number): string[] {
  if (width <= 0) return [text];
  if (visibleWidth(text) <= width) return [text];
  const prefixMatch = text.match(/^(?:\x1b\[[0-9;]*m)+/);
  const prefix = prefixMatch ? prefixMatch[0] : "";
  let body = prefix ? text.slice(prefix.length) : text;
  let suffix = "";
  if (body.endsWith(RESET)) {
    suffix = RESET;
    body = body.slice(0, body.length - suffix.length);
  }
  if (body.includes("\x1b")) {
    // 内部仍含 ANSI，难以稳健切分；安全起见单行截断。
    return [sliceByVisibleWidth(text, width)];
  }
  const segs: string[] = [];
  let buf = "";
  let bufW = 0;
  let i = 0;
  while (i < body.length) {
    const cp = body.codePointAt(i)!;
    const w = isWide(cp) ? 2 : 1;
    const ch = String.fromCodePoint(cp);
    if (bufW + w > width) {
      segs.push(prefix + buf + suffix);
      buf = ch;
      bufW = w;
    } else {
      buf += ch;
      bufW += w;
    }
    i += cp > 0xffff ? 2 : 1;
  }
  if (buf) segs.push(prefix + buf + suffix);
  return segs.length === 0 ? [""] : segs;
}

// 安全截断：保留 ANSI 序列原样（不计入宽度），可见字符达到 width 即停。
export function sliceByVisibleWidth(text: string, width: number): string {
  if (width <= 0) return "";
  if (visibleWidth(text) <= width) return text;
  let buf = "";
  let bufW = 0;
  let i = 0;
  while (i < text.length) {
    if (text[i] === "\x1b") {
      const idx = text.indexOf("m", i);
      if (idx === -1) break;
      buf += text.slice(i, idx + 1);
      i = idx + 1;
      continue;
    }
    const cp = text.codePointAt(i)!;
    const w = isWide(cp) ? 2 : 1;
    if (bufW + w > width) break;
    buf += String.fromCodePoint(cp);
    bufW += w;
    i += cp > 0xffff ? 2 : 1;
  }
  // 收尾 reset，避免遗漏的样式污染后续输出。
  return buf + RESET;
}

export function padRightVisible(text: string, width: number): string {
  const w = visibleWidth(text);
  if (w >= width) return text;
  return text + " ".repeat(width - w);
}

export function centerInWidth(text: string, width: number): string {
  const w = visibleWidth(text);
  if (w >= width) return text;
  const left = Math.floor((width - w) / 2);
  const right = width - w - left;
  return " ".repeat(left) + text + " ".repeat(right);
}

// 把内联多行字符串按行截断/对齐。
export function splitLines(text: string): string[] {
  return text.split(/\r?\n/);
}
