// state.ts — Mikuru 游戏状态容器
// reactive 字段在 Web 上不需要 reactive 框架，直接放在 class 里；UI 每帧重读

import type { Enemy, EnemyProjectile, PlayerProjectile } from "./types";

export class MikuruState {
  // 网格自适应（运行时被 ResizeObserver 更新）
  map_w = 52;
  map_h = 13;

  // 玩家
  px = 3;
  py = 5;
  player_hp = 10;
  beam_charge = 0;
  beam_ready = false;
  beam_active_frames = 0;

  // 敌人 / 弹幕
  enemies: Enemy[] = [];
  enemy_projectiles: EnemyProjectile[] = [];
  player_projectiles: PlayerProjectile[] = [];

  // 计数 / 时间
  kill_count = 0;
  time_elapsed = 0;
  victory_time = 180;

  // 技能 CD（秒，由 1s 时钟递减）
  classified_cd = 0;
  teatime_cd = 0;

  // 反馈队列（最近 N 条）
  feedback_queue: string[] = ["Ready."];
  feedback_limit = 3;

  // 总开关
  game_active = true;

  // hit-flash 倒计时
  hit_flash_until = 0;
}
