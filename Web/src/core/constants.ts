// constants.ts — 对应 models.py 中的世界线 / 物品常量

export const WORLDLINE_STABLE = "1.048596[α·STABLE]";
export const WORLDLINE_UNSTABLE = "0xFF-05-02[UNSTABLE]";
export const WORLDLINE_SHIFTING = "??:??:??[SHIFTING···]";

export const KEY_ITEMS: ReadonlySet<string> = new Set([
  "玩偶服",
  "大红按钮",
  "超能力飞行装置",
]);

export const NORMAL_ITEMS: ReadonlySet<string> = new Set([
  "普通的怪兽贴纸",
  "普通的灯带",
  "普通的风筝线",
]);
