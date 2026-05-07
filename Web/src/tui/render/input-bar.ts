// input-bar.ts — 底部输入栏，对应 components.py:321-362
// 显示 prompt + 当前值 + 闪烁块光标

import { wrap } from "./ansi";

const PROMPT = "kyon@SOS:~$ ";

export interface InputBarParams {
  value: string;
  cursorOn: boolean;
}

export function renderInputBar({ value, cursorOn }: InputBarParams): string {
  // components.py InputBar 的 prompt 颜色是 #33cc33
  const prompt = wrap(PROMPT, { fg: "prompt_green", bold: true });
  const cursor = cursorOn ? wrap("▍", { fg: "white" }) : " ";
  return `${prompt}${value}${cursor}`;
}
