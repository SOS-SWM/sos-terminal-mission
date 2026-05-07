// credit/XtermApp.ts — 滚动字幕（xterm 版），对应 Engine/credit.py

import type { Terminal } from "@xterm/xterm";
import { wrap, RESET, centerInWidth, padRightVisible } from "../tui/render/ansi";
import { renderPanel } from "../tui/render/panel";

const CREDIT_LINES: ReadonlyArray<string> = [
  wrap("SOS TERMINAL MISSION", { bold: true, fg: "white" }),
  "",
  wrap("ENDING CREDIT SEQUENCE", { fg: "cyan" }),
  "",
  "Story / System Design",
  wrap("Machillka, Sheshenxian, Asttear and the SOS Brigade", { fg: "white" }),
  "",
  "Terminal Operations",
  wrap("Textual Runtime", { fg: "white" }),
  "",
  "Emergency Support",
  wrap("Mikuru Beam Department", { fg: "white" }),
  "",
  "Worldline Stabilization",
  wrap("You", { fg: "magenta" }),
  "",
  wrap("No matter how many loops it took,", { fg: "yellow" }),
  wrap("the signal finally made it through.", { fg: "yellow" }),
];

export class CreditXtermApp {
  private rollIndex = 0;
  private rollTimer: ReturnType<typeof setTimeout> | null = null;
  private removeResize: (() => void) | null = null;

  constructor(private term: Terminal) {}

  start(): void {
    this.term.write("\x1b[?1049h\x1b[?25l\x1b[H\x1b[2J");
    const onResize = this.term.onResize(() => this.refresh());
    this.removeResize = () => onResize.dispose();
    this.scheduleNext();
    this.refresh();
  }

  unmount(): void {
    if (this.rollTimer) clearTimeout(this.rollTimer);
    this.removeResize?.();
    this.term.write("\x1b[?25h\x1b[?1049l");
  }

  private scheduleNext(): void {
    if (this.rollIndex >= CREDIT_LINES.length) return;
    this.rollTimer = setTimeout(() => {
      this.rollIndex += 1;
      this.refresh();
      this.scheduleNext();
    }, 800);
  }

  private refresh(): void {
    const cols = this.term.cols;
    const rows = this.term.rows;
    if (cols < 10 || rows < 6) return;

    const out = makeBlankRows(cols, rows);
    const outer = centeredRect(cols, rows, 0.96, 0.96);
    drawDoubleBox(out, outer.x, outer.y, outer.w, outer.h, "green");

    // #crt-monitor { padding: 1 2; layout: vertical; }
    const innerX = outer.x + 1 + 2;
    const innerY = outer.y + 1 + 1;
    const innerW = Math.max(2, outer.w - 2 - 4);
    const innerH = Math.max(4, outer.h - 2 - 2);
    const footerH = 3;
    const footerMarginTop = 1;
    const creditsH = Math.max(3, innerH - footerMarginTop - footerH);
    const footerY = innerY + creditsH + footerMarginTop;

    const visible = CREDIT_LINES.slice(0, this.rollIndex);
    const creditsInnerH = Math.max(1, creditsH - 2);
    const topPad = Math.max(0, Math.floor((creditsInnerH - visible.length) / 2));
    const creditBody: string[] = [];
    for (let i = 0; i < topPad; i++) creditBody.push("");
    creditBody.push(...visible);
    while (creditBody.length < creditsInnerH) creditBody.push("");

    const creditsPanel = renderPanel(creditBody.join("\n"), innerW, {
      title: "ENDING CREDIT",
      borderColor: "green",
      titleColor: "green",
    });
    blitRows(out, innerX, innerY, creditsPanel.slice(0, creditsH), innerW);

    const footer =
      this.rollIndex >= CREDIT_LINES.length
        ? wrap("Transmission complete. Thank you for your playing!", { fg: "green" })
        : wrap("SOS Brigade Presents...", { fg: "green" });
    const footerBody = centerInWidth(footer, Math.max(1, innerW - 4));
    const footerPanel = renderPanel(footerBody, innerW, {
      title: "TRANSMISSION",
      borderColor: "green",
      titleColor: "green",
    });
    blitRows(out, innerX, footerY, footerPanel.slice(0, footerH), innerW);

    const frame = out.slice(0, rows).map((l) => l + RESET + "\x1b[K").join("\r\n");
    this.term.write(`\x1b[H${frame}`);
  }
}

function makeBlankRows(cols: number, rows: number): string[] {
  return Array.from({ length: rows }, () => " ".repeat(cols));
}

function centeredRect(cols: number, rows: number, wRatio: number, hRatio: number) {
  const w = Math.max(2, Math.floor(cols * wRatio));
  const h = Math.max(2, Math.floor(rows * hRatio));
  return {
    x: Math.max(0, Math.floor((cols - w) / 2)),
    y: Math.max(0, Math.floor((rows - h) / 2)),
    w,
    h,
  };
}

function drawDoubleBox(rows: string[], x: number, y: number, w: number, h: number, _color: string): void {
  const top = `╔${"═".repeat(Math.max(0, w - 2))}╗`;
  const mid = `║${" ".repeat(Math.max(0, w - 2))}║`;
  const bottom = `╚${"═".repeat(Math.max(0, w - 2))}╝`;
  blitLine(rows, x, y, top, w);
  for (let yy = y + 1; yy < y + h - 1; yy++) blitLine(rows, x, yy, mid, w);
  blitLine(rows, x, y + h - 1, bottom, w);
}

function blitRows(rows: string[], x: number, y: number, lines: string[], width: number): void {
  for (let i = 0; i < lines.length; i++) {
    blitLine(rows, x, y + i, padRightVisible(lines[i], width), width);
  }
}

function blitLine(rows: string[], x: number, y: number, line: string, width: number): void {
  if (y < 0 || y >= rows.length) return;
  const left = rows[y].slice(0, x);
  const rightStart = x + width;
  const right = rightStart < rows[y].length ? rows[y].slice(rightStart) : "";
  rows[y] = left + line + right;
}
