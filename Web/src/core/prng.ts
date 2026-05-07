// prng.ts — 轻量种子化伪随机；可选用，默认走 Math.random
// 与原 Python random 不要求逐帧重现，但提供包装以便未来切到种子模式

export type RandomSource = {
  random(): number;
  randint(a: number, b: number): number;
};

export const defaultRandom: RandomSource = {
  random: () => Math.random(),
  randint: (a, b) => a + Math.floor(Math.random() * (b - a + 1)),
};

// mulberry32: 32-bit 状态种子化 PRNG，质量足够游戏使用
export function createSeededRandom(seed: number): RandomSource {
  let s = seed >>> 0;
  const random = (): number => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    random,
    randint: (a, b) => a + Math.floor(random() * (b - a + 1)),
  };
}
