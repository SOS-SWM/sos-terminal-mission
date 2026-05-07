// types.ts — Mikuru 小游戏数据结构
// 与 Engine/mikuru.py 中 dataclass 一一对应

export interface Enemy {
  type: "melee" | "ranged";
  x: number;
  y: number;
  hp: number;
  freeze: number;
  cooldown: number;
}

export interface EnemyProjectile {
  float_x: number;
  float_y: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export type PlayerProjType = "attack" | "fire ball" | "ice ball" | "classified";

export interface PlayerProjectile {
  float_x: number;
  float_y: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  type: PlayerProjType;
  damage: number;
  freeze: number;
}

export const MIKURU_ART = [" ∩_∩ ", "(T_T)", "/>M<"];
