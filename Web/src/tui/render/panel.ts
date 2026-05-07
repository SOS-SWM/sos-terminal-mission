// Rich Panel 等价：用 box drawing 字符 ┏━┓┃┗┛ 自绘，标题嵌入顶边。
// title 居左偏移 2 列，与 Rich 默认对齐。

import {
  centerInWidth,
  padRightVisible,
  splitLines,
  style,
  visibleWidth,
  wrap,
  RESET,
} from "./ansi";

export interface PanelOptions {
  title?: string;
  borderColor?: string;
  titleColor?: string;
  align?: "left" | "center";
  padding?: number;
}

export function renderPanel(body: string, width: number, opts: PanelOptions = {}): string[] {
  const borderColor = opts.borderColor ?? "white";
  const titleColor = opts.titleColor ?? "default";
  const padding = opts.padding ?? 1;
  const innerWidth = Math.max(2, width - 2 - padding * 2);

  const open = style({ fg: borderColor });
  const close = RESET;
  const titleRaw = opts.title ?? "";

  const top = buildTopBorder(width, titleRaw, titleColor, borderColor);
  const bottomChars = "─".repeat(width - 2);
  const bottom = `${open}└${bottomChars}┘${close}`;

  const padStr = " ".repeat(padding);
  const linesOut: string[] = [top];
  for (const raw of splitLines(body)) {
    const wrapped = wrapLineToWidth(raw, innerWidth, opts.align ?? "left");
    for (const seg of wrapped) {
      const padded = padRightVisible(seg, innerWidth);
      linesOut.push(`${open}│${close}${padStr}${padded}${padStr}${open}│${close}`);
    }
  }
  if (linesOut.length === 1) {
    linesOut.push(`${open}│${close}${padStr}${" ".repeat(innerWidth)}${padStr}${open}│${close}`);
  }
  linesOut.push(bottom);
  return linesOut;
}

function buildTopBorder(
  width: number,
  title: string,
  titleColor: string,
  borderColor: string,
): string {
  const open = style({ fg: borderColor });
  const close = RESET;
  if (!title) {
    return `${open}┌${"─".repeat(width - 2)}┐${close}`;
  }
  const titleStyled = wrap(` ${title} `, { fg: titleColor, bold: true });
  const titleVis = visibleWidth(titleStyled);
  const remain = width - 2 - titleVis;
  const left = Math.max(2, Math.floor(remain / 2));
  const right = Math.max(2, remain - left);
  return `${open}┌${"─".repeat(left)}${close}${titleStyled}${open}${"─".repeat(right)}┐${close}`;
}

// 简易折行：按可见宽度切片；不破坏 ANSI 序列（在传入前已 reset 即可）。
function wrapLineToWidth(text: string, width: number, align: "left" | "center"): string[] {
  if (visibleWidth(text) <= width) {
    return [align === "center" ? centerInWidth(text, width) : text];
  }
  const segs: string[] = [];
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
    const w = isWideCodePoint(cp) ? 2 : 1;
    const ch = String.fromCodePoint(cp);
    if (bufW + w > width) {
      segs.push(align === "center" ? centerInWidth(buf, width) : buf);
      buf = ch;
      bufW = w;
    } else {
      buf += ch;
      bufW += w;
    }
    i += cp > 0xffff ? 2 : 1;
  }
  if (buf) segs.push(align === "center" ? centerInWidth(buf, width) : buf);
  return segs;
}

function isWideCodePoint(cp: number): boolean {
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
    (cp >= 0xffe0 && cp <= 0xffe6)
  );
}
