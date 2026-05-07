// engine.ts — 游戏逻辑层，对应 Engine/engine.py
// 接收输入 → 更新 GameState → 返回新增日志条目

import {
  Choice,
  GameState,
  LogEntry,
  Scene,
} from "./models";
import { NORMAL_ITEMS, WORLDLINE_UNSTABLE } from "./constants";
import {
  AP_FINAL_TARGETS,
  AP_INIT_SCENES,
  AP_SCENES_LOOP1,
  AP_SCENES_LOOP2,
  CH3_TIME_SLOTS_LOOP1,
  CH3_TIME_SLOTS_LOOP2,
  LOOP2_ROUTING,
  MAP_HUBS,
} from "./scene-meta";
import { getCommandResponse } from "./commands";
import { defaultRandom, type RandomSource } from "./prng";

export class GameEngine {
  scenes: Map<string, Scene>;
  state: GameState;
  private rng: RandomSource;

  constructor(scenes: Map<string, Scene>, initialSceneId: string | null = null, rng: RandomSource = defaultRandom) {
    this.scenes = scenes;
    this.state = new GameState();
    this.rng = rng;
    const first = initialSceneId ?? "c1a_morning_call";
    this.state.log.push(...this._enter_scene(first));
  }

  // ── Public API ──────────────────────────────────────────────────────────

  current_scene(): Scene {
    const s = this.scenes.get(this.state.current_scene_id);
    if (!s) throw new Error(`Scene not found: ${this.state.current_scene_id}`);
    return s;
  }

  // 返回 [新条目, 是否被识别为合法 choice 或 command]
  process_input(raw: string): [LogEntry[], boolean] {
    const text = raw.trim();
    if (!text) return [[], false];

    const player_entry = new LogEntry({
      kind: "player",
      speaker: "kyon",
      text,
    });
    const new_entries: LogEntry[] = [player_entry];

    const isCommand = !this._isDigitString(text);

    let entries: LogEntry[];
    if (isCommand) {
      entries = this._handle_command(text);
    } else {
      entries = this._handle_choice(parseInt(text, 10));
    }

    new_entries.push(...entries);
    this.state.log.push(...new_entries);

    return [new_entries, isCommand];
  }

  private _isDigitString(s: string): boolean {
    if (s.length === 0) return false;
    for (let i = 0; i < s.length; i++) {
      const ch = s.charCodeAt(i);
      if (ch < 48 || ch > 57) return false;
    }
    return true;
  }

  // ── Internal ────────────────────────────────────────────────────────────

  private _handle_choice(index: number): LogEntry[] {
    const scene = this.current_scene();
    for (const choice of scene.choices) {
      if (choice.index === index && this._choice_available(choice)) {
        const target = choice.target_scene;
        if (this._is_ap_target(target)) {
          return this._handle_ap_entry(target);
        }
        return this._enter_scene(target);
      }
    }
    return [
      new LogEntry({
        kind: "error",
        speaker: null,
        text: `>> 选项 [${index}] 在当前场景不可用`,
      }),
    ];
  }

  private _handle_command(text: string): LogEntry[] {
    return getCommandResponse(
      text,
      this.state.current_scene_id,
      this.state.inventory,
      this.state.status.loop_count,
      this.state.flags,
    );
  }

  // 暴露给 UI 层渲染选项时使用（components.py 中的等价物）
  _choice_available(choice: Choice): boolean {
    if (choice.requires_flag && !this.state.flags[choice.requires_flag]) {
      return false;
    }
    if (choice.requires_item && !this.state.inventory.has(choice.requires_item)) {
      return false;
    }
    if (choice.hidden) return false;
    return true;
  }

  // ── Action Point system ────────────────────────────────────────────────

  private _is_ap_target(scene_id: string): boolean {
    return AP_SCENES_LOOP1.has(scene_id) || AP_SCENES_LOOP2.has(scene_id);
  }

  private _handle_ap_entry(target: string): LogEntry[] {
    const is_loop1 = this.state.action_points_max === 4;

    // 智能路由：把 loop2 统一目标转换为首访/重访的实际场景
    const resolved = is_loop1 ? target : this._resolve_loop2_target(target);

    if (this.state.visited_actions.has(resolved)) {
      if (is_loop1) {
        return [
          new LogEntry({
            kind: "dialogue",
            speaker: "Kyon",
            text: "那个地方已经去过了，没什么好看的了。",
            effect: "typewriter",
            speed: 1.0,
          }),
        ];
      } else {
        this._consume_ap();
        // "首访已完成但无法升级" 的情况
        const route = LOOP2_ROUTING.get(target);
        let msg: string;
        if (
          route &&
          this.state.visited_actions.has(target) &&
          !this._isSubset(route.revisit_requires, this.state.inventory)
        ) {
          msg = "总觉得还缺点什么……白跑了一趟。";
        } else {
          msg = "又来了一次，但什么也没发生。浪费了宝贵的时间。";
        }
        const entries = [
          new LogEntry({
            kind: "dialogue",
            speaker: "Kyon",
            text: msg,
            effect: "typewriter",
            speed: 1.0,
          }),
        ];
        entries.push(...this._check_ap_exhausted());
        return entries;
      }
    }

    this._consume_ap();
    this.state.visited_actions.add(resolved);
    const entries = this._enter_scene(resolved);
    // 不在此检查 AP 耗尽 — 让玩家先把当前场景走完
    return entries;
  }

  private _resolve_loop2_target(target: string): string {
    const route = LOOP2_ROUTING.get(target);
    if (!route) return target;
    const first_visit_id = target;
    const revisit_id = route.revisit_scene;
    if (
      this.state.visited_actions.has(first_visit_id) &&
      this._isSubset(route.revisit_requires, this.state.inventory)
    ) {
      return revisit_id;
    }
    return first_visit_id;
  }

  private _consume_ap(): void {
    if (this.state.action_points_remaining > 0) {
      this.state.action_points_remaining -= 1;
    }
  }

  private _inject_ch3_timestamps(entries: LogEntry[]): void {
    const is_loop1 = this.state.action_points_max === 4;
    const slots = is_loop1 ? CH3_TIME_SLOTS_LOOP1 : CH3_TIME_SLOTS_LOOP2;
    // AP 槽 = 已消耗 AP（_consume_ap 在 _enter_scene 之前执行）
    const consumed = this.state.action_points_max - this.state.action_points_remaining;
    const idx = Math.max(0, Math.min(consumed - 1, slots.length - 1));
    const base = slots[idx];
    let [h, m] = base.split(":").map((x) => parseInt(x, 10));
    let s = 0;
    for (const entry of entries) {
      if (entry.kind === "fx") continue;
      entry.timestamp =
        `${pad2(h)}:${pad2(m)}:${pad2(s)}`;
      s = this.rng.randint(0, 59);
      if (this.rng.random() < 0.4) {
        m += 1;
        if (m >= 60) {
          m = 0;
          h += 1;
        }
      }
    }
  }

  private _check_ap_exhausted(): LogEntry[] {
    if (this.state.action_points_remaining <= 0) {
      const final = AP_FINAL_TARGETS.get(this.state.action_points_max);
      if (final && this.scenes.has(final)) {
        const hub = this.state.current_scene_id;
        if (MAP_HUBS.has(hub) || hub.startsWith("c3")) {
          return this._enter_scene(final);
        }
      }
    }
    return [];
  }

  private _init_ap_for_scene(scene_id: string): void {
    const ap = AP_INIT_SCENES.get(scene_id);
    if (ap !== undefined) {
      if (this.state.action_points_max === 0) {
        this.state.action_points_max = ap;
        this.state.action_points_remaining = ap;
        this.state.visited_actions.clear();
      }
    }
  }

  // 暴露 _enter_scene 给 UI 层（main.py 中也直接调用 engine._enter_scene）
  _enter_scene(scene_id: string): LogEntry[] {
    const scene = this.scenes.get(scene_id);
    if (!scene) {
      return [
        new LogEntry({
          kind: "error",
          speaker: null,
          text: `>> ERROR: 场景 '${scene_id}' 不存在`,
        }),
      ];
    }
    this.state.current_scene_id = scene_id;
    this.state.visited.add(scene_id);
    this._init_ap_for_scene(scene_id);
    this._apply_scene_side_effects(scene);
    const entries: LogEntry[] = [...scene.entries, ...scene.auto_entries];

    if (scene.location && scene.location.trim()) {
      this.state.location = scene.location;
    }

    if (scene_id.startsWith("c3")) {
      this._inject_ch3_timestamps(entries);
    }

    if (MAP_HUBS.has(scene_id)) {
      const exhausted = this._check_ap_exhausted();
      if (exhausted.length > 0) {
        entries.push(...exhausted);
        return entries;
      }
    }

    if (scene.triggers_loop_reset) {
      let next_scene = "c1b_morning_reboot";
      if (scene_id !== "c4a_loop_start" && this.scenes.has("c4a_loop_start")) {
        next_scene = "c4a_loop_start";
      }
      // 保留守卫：c4a_loop_start 实际未在 SCENE_META 中定义，所以兜底走 c1b_morning_reboot
      if (this.scenes.has(next_scene) && next_scene !== scene_id) {
        this.state.pending_scene = next_scene;
      }
    }

    if (scene.auto_next_scene && this.scenes.has(scene.auto_next_scene)) {
      entries.push(...this._enter_scene(scene.auto_next_scene));
    }
    return entries;
  }

  private _apply_scene_side_effects(scene: Scene): void {
    if (scene.set_location !== null && scene.set_location !== undefined) {
      this.state.location = scene.set_location;
    }
    if (scene.set_worldline !== null && scene.set_worldline !== undefined) {
      this.state.status.worldline = scene.set_worldline;
    }
    if (scene.grant_items.length > 0) {
      for (const it of scene.grant_items) this.state.inventory.add(it);
    }
    if (scene.consume_items.length > 0) {
      for (const it of scene.consume_items) this.state.inventory.delete(it);
    }
    if (Object.keys(scene.set_flags).length > 0) {
      for (const [k, v] of Object.entries(scene.set_flags)) {
        this.state.flags[k] = v;
      }
    }

    if (scene.id === "c4b_final") {
      this.state.flags["has_all_key_items"] = this.state.has_all_key_items();
    }

    if (scene.id === "c4b_true_end") {
      this.state.game_over = true;
    }

    if (scene.triggers_loop_reset) {
      if (scene.id !== "c4a_loop_start") {
        this.state.status.loop_count += 1;
      }
      // 普通物品在每次失败 loop 后清空
      for (const it of NORMAL_ITEMS) this.state.inventory.delete(it);
      this.state.flags = {};
      if (scene.set_worldline === null || scene.set_worldline === undefined) {
        this.state.status.worldline = WORLDLINE_UNSTABLE;
      }
      // 重置 AP
      this.state.action_points_remaining = 0;
      this.state.action_points_max = 0;
      this.state.visited_actions.clear();
    }
  }

  // 工具：判断 sub 是否是 sup 的子集
  private _isSubset(sub: ReadonlySet<string>, sup: ReadonlySet<string>): boolean {
    for (const x of sub) if (!sup.has(x)) return false;
    return true;
  }
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : `${n}`;
}
