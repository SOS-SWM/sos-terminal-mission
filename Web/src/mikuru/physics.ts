// physics.ts — Mikuru 弹幕 / 敌人 AI tick
// 完全照搬 Engine/mikuru.py 的 engine_tick / ai_tick 物理

import type { MikuruState } from "./state";
import type { Enemy, EnemyProjectile, PlayerProjectile } from "./types";

export interface PhysicsCallbacks {
  onPlayerHit(damage: number): void;
  onKill(count: number): void;
  showFeedback(text: string, color: string): void;
}

// 100ms 一次的引擎 tick（弹幕物理 + 碰撞）
export function engineTick(s: MikuruState, cb: PhysicsCallbacks): void {
  if (!s.game_active) return;

  if (s.beam_active_frames > 0) s.beam_active_frames -= 1;

  // 敌方直线弹幕
  const survE: EnemyProjectile[] = [];
  for (const p of s.enemy_projectiles) {
    p.float_x += p.vx;
    p.float_y += p.vy;
    const px = Math.trunc(p.float_x);
    const py = Math.trunc(p.float_y);
    if (s.px <= px && px < s.px + 5 && s.py <= py && py < s.py + 3) {
      cb.onPlayerHit(5);
      continue;
    }
    if (px >= 0 && px < s.map_w && py >= 0 && py < s.map_h) {
      p.x = px;
      p.y = py;
      survE.push(p);
    }
  }
  s.enemy_projectiles = survE;

  // 我方自瞄弹幕
  const survP: PlayerProjectile[] = [];
  for (const p of s.player_projectiles) {
    let closest: Enemy | null = null;
    let minD = 999;
    for (const e of s.enemies) {
      const d = Math.hypot(e.x - p.float_x, e.y - p.float_y);
      if (d < minD) {
        minD = d;
        closest = e;
      }
    }
    if (closest && minD > 0) {
      const dx = closest.x + 1 - p.float_x;
      const dy = closest.y - p.float_y;
      const dist = Math.hypot(dx, dy);
      if (dist > 0) {
        const speed = 2.0;
        p.vx = (dx / dist) * speed;
        p.vy = (dy / dist) * speed;
      }
    }
    const steps = 2;
    let hit = false;
    let px = 0;
    let py = 0;
    for (let i = 0; i < steps; i++) {
      p.float_x += p.vx / steps;
      p.float_y += p.vy / steps;
      px = Math.trunc(p.float_x);
      py = Math.trunc(p.float_y);
      for (const e of s.enemies) {
        if (e.x <= px && px <= e.x + 2 && e.y === py) {
          hit = true;
          e.hp -= p.damage;
          if (p.freeze) e.freeze = p.freeze;
          if (e.hp <= 0) {
            const idx = s.enemies.indexOf(e);
            if (idx >= 0) s.enemies.splice(idx, 1);
            cb.onKill(1);
            cb.showFeedback("Destroyed!", "green");
          }
          break;
        }
      }
      if (hit) break;
    }
    if (!hit && px >= 0 && px < s.map_w && py >= 0 && py < s.map_h) {
      p.x = px;
      p.y = py;
      survP.push(p);
    }
  }
  s.player_projectiles = survP;
}

// 500ms 一次的 AI tick（生成敌人 + 移动 + 射击）
export function aiTick(s: MikuruState, cb: PhysicsCallbacks): void {
  if (!s.game_active) return;

  const spawnChance = 0.15 + (s.time_elapsed / 500.0) * 0.7;
  const hpMul = 1.0 + (s.time_elapsed / 500.0) * 2.0;

  if (Math.random() < spawnChance) {
    const spawn_x = s.map_w - 4;
    const spawn_y = randInt(0, Math.max(0, s.map_h - 1));
    if (Math.random() < 0.4) {
      s.enemies.push({
        type: "ranged",
        x: spawn_x,
        y: spawn_y,
        hp: Math.trunc(15 * hpMul),
        cooldown: 0,
        freeze: 0,
      });
    } else {
      s.enemies.push({
        type: "melee",
        x: spawn_x,
        y: spawn_y,
        hp: Math.trunc(25 * hpMul),
        freeze: 0,
        cooldown: 0,
      });
    }
  }

  const px_center = s.px + 2;
  const py_center = s.py + 1;

  for (const e of s.enemies) {
    if (e.freeze > 0) {
      e.freeze -= 1;
      continue;
    }
    const dx = px_center - (e.x + 1);
    const dy = py_center - e.y;
    const dist = Math.abs(dx) + Math.abs(dy);

    if (e.type === "melee") {
      if (dist <= 3) {
        cb.onPlayerHit(5);
      } else {
        if (Math.abs(dx) > Math.abs(dy)) {
          e.x += dx > 0 ? 1 : -1;
        } else {
          e.y += dy > 0 ? 1 : -1;
        }
      }
    } else {
      const is_aligned_y = s.py <= e.y && e.y < s.py + 3;
      const is_aligned_x = s.px <= e.x && e.x < s.px + 5;

      if (dist <= 30) {
        if (e.cooldown <= 0 && (is_aligned_x || is_aligned_y)) {
          let vx = 0;
          let vy = 0;
          if (is_aligned_y) {
            vx = dx > 0 ? 1.5 : -1.5;
            vy = 0;
          } else {
            vx = 0;
            vy = dy > 0 ? 1.5 : -1.5;
          }
          s.enemy_projectiles.push({
            float_x: e.x,
            float_y: e.y,
            x: e.x,
            y: e.y,
            vx,
            vy,
          });
          e.cooldown = 4;
        } else {
          if (e.cooldown > 0) e.cooldown -= 1;
          if (!is_aligned_y && !is_aligned_x) {
            if (Math.abs(dx) > Math.abs(dy)) {
              e.y += dy > 0 ? 1 : -1;
            } else {
              e.x += dx > 0 ? 1 : -1;
            }
          } else if (dist < 12) {
            e.x += dx < 0 ? 1 : -1;
          }
        }
      } else {
        e.x -= 1;
      }
    }
  }
}

function randInt(a: number, b: number): number {
  return a + Math.floor(Math.random() * (b - a + 1));
}
