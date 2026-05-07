// options.ts — 选项 / 命令 / hint 区域，对应 components.py:295-318

import type { Choice, Command } from "../../core/models";
import { wrap } from "./ansi";

export function renderOptionsBody(
  choices: ReadonlyArray<Choice>,
  commands: ReadonlyArray<Command>,
  hint: string,
): string[] {
  const lines: string[] = [];
  for (let i = 0; i < choices.length; i++) {
    const c = choices[i];
    const idx = wrap(`[${i + 1}]`, { fg: "green", bold: true });
    lines.push(`${idx} ${c.name}`);
  }
  if (choices.length > 0) lines.push("");
  for (const c of commands) {
    const arrow = wrap(">", { fg: "cyan", bold: true });
    const name = wrap(c.name, { fg: "cyan", bold: true });
    lines.push(`${arrow} ${name}`);
  }
  if (commands.length > 0) lines.push("");
  if (hint) {
    lines.push(`${wrap("[HINT]", { fg: "green", bold: true })} ${hint}`);
  }
  return lines;
}
