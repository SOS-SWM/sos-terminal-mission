// status-bar.ts — 顶部 2 行双列状态栏
// 1:1 对应 components.py:38-51

import { padRightVisible, visibleWidth, wrap } from "./ansi";

export function renderStatusBar(width: number): string[] {
  // StatusBar 里的 ▉ 没有 Rich 标记，保持 Textual ansi-dark 默认前景色。
  const blk = "▉";
  const innerWidth = Math.max(1, width - 2);
  const rows: ReadonlyArray<readonly [string, string]> = [
    [
      `  ${blk} SYSTEM_CORE: Nagato_Interface v1.1.4`,
      `${blk} WORLDLINE: ${wrap("0xFF-05-02", { fg: "green", bold: true })}`,
    ],
    [`  ${blk} USER_HOST: kyon@SOS`, `${blk} PRIVILEGE: /dev/human/sudo`],
  ];
  const halfW = Math.floor(innerWidth / 2);
  return rows.map(([left, right]) => {
    // 左半区按 halfW 留位，右半区贴左
    const leftPadded = padRightVisible(left, halfW);
    const rightVisible = visibleWidth(right);
    const rightPad = Math.max(0, innerWidth - halfW - rightVisible);
    return " " + leftPadded + right + " ".repeat(rightPad) + " ";
  });
}
