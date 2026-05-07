// models.ts — 纯数据结构，对应 Engine/models.py

import { KEY_ITEMS, NORMAL_ITEMS, WORLDLINE_UNSTABLE } from "./constants";

export type EntryKind =
  | "narration"
  | "dialogue"
  | "system"
  | "player"
  | "error"
  | "fx";

export type EffectTag =
  | "typewriter"
  | "typewriter_fast"
  | "typewriter_slow"
  | "instant"
  | "flicker"
  | "glitch"
  | "glitch_heavy"
  | "jitter"
  | "dim"
  | "route_trace"
  | "route_trace_ghost"
  | "separator"
  | "worldline_shift"
  | "reboot"
  | "success"
  | "warning"
  | "cursor_fast";

export interface LogEntryInit {
  kind: EntryKind;
  speaker: string | null;
  text: string;
  effect?: EffectTag;
  speed?: number;
  timestamp?: string;
}

export class LogEntry {
  kind: EntryKind;
  speaker: string | null;
  text: string;
  effect: EffectTag;
  speed: number;
  timestamp: string;

  constructor(init: LogEntryInit) {
    this.kind = init.kind;
    this.speaker = init.speaker;
    this.text = init.text;
    this.effect = init.effect ?? "typewriter";
    this.speed = init.speed ?? 1.0;
    this.timestamp = init.timestamp ?? "";
  }

  // 与 components.py 显示层兼容：带方括号的 timestamp + speaker
  get frontmatter(): string {
    const ts = this.timestamp ? `[${this.timestamp}]` : "";
    if (this.speaker) {
      return ts ? `${this.speaker} >` : `${this.speaker} >`;
    }
    return ts;
  }

  get content(): string {
    return this.text;
  }
}

export interface ChoiceInit {
  index: number;
  label: string;
  target_scene: string;
  requires_flag?: string | null;
  requires_item?: string | null;
  hidden?: boolean;
}

export class Choice {
  index: number;
  label: string;
  target_scene: string;
  requires_flag: string | null;
  requires_item: string | null;
  hidden: boolean;

  constructor(init: ChoiceInit) {
    this.index = init.index;
    this.label = init.label;
    this.target_scene = init.target_scene;
    this.requires_flag = init.requires_flag ?? null;
    this.requires_item = init.requires_item ?? null;
    this.hidden = init.hidden ?? false;
  }

  get name(): string {
    return this.label;
  }

  get next_scene_id(): string {
    return this.target_scene;
  }
}

export interface CommandInit {
  name: string;
  description: string;
  hint?: string;
  next_scene_id?: string | null;
}

export class Command {
  name: string;
  description: string;
  hint: string;
  next_scene_id: string | null;

  constructor(init: CommandInit) {
    this.name = init.name;
    this.description = init.description;
    this.hint = init.hint ?? "";
    this.next_scene_id = init.next_scene_id ?? null;
  }
}

export interface SceneInit {
  id: string;
  location?: string;
  entries?: LogEntry[];
  auto_entries?: LogEntry[];
  choices?: Choice[];
  commands?: Command[];
  hint?: string;
  set_location?: string | null;
  set_worldline?: string | null;
  grant_items?: string[];
  consume_items?: string[];
  set_flags?: Record<string, boolean>;
  triggers_loop_reset?: boolean;
  auto_next_scene?: string | null;
  terminal_scene?: boolean;
}

export class Scene {
  id: string;
  location: string;
  entries: LogEntry[];
  auto_entries: LogEntry[];
  choices: Choice[];
  commands: Command[];
  hint: string;
  set_location: string | null;
  set_worldline: string | null;
  grant_items: string[];
  consume_items: string[];
  set_flags: Record<string, boolean>;
  triggers_loop_reset: boolean;
  auto_next_scene: string | null;
  terminal_scene: boolean;

  constructor(init: SceneInit) {
    this.id = init.id;
    this.location = init.location ?? "";
    this.entries = init.entries ?? [];
    this.auto_entries = init.auto_entries ?? [];
    this.choices = init.choices ?? [];
    this.commands = init.commands ?? [];
    this.hint = init.hint ?? "";
    this.set_location = init.set_location ?? null;
    this.set_worldline = init.set_worldline ?? null;
    this.grant_items = init.grant_items ?? [];
    this.consume_items = init.consume_items ?? [];
    this.set_flags = init.set_flags ?? {};
    this.triggers_loop_reset = init.triggers_loop_reset ?? false;
    this.auto_next_scene = init.auto_next_scene ?? null;
    this.terminal_scene = init.terminal_scene ?? false;
  }

  get time(): string {
    return "";
  }
}

export class SystemStatus {
  worldline: string = WORLDLINE_UNSTABLE;
  interface_: string = "Nagato_Interface v1.1.4";
  user: string = "root@kyon";
  privilege: string = "/dev/human/sudo";
  location: string = "Home";
  loop_count: number = 0;
}

export class GameState {
  status: SystemStatus = new SystemStatus();
  current_scene_id: string = "_ch1a";
  log: LogEntry[] = [];
  visited: Set<string> = new Set();
  flags: Record<string, boolean> = {};
  inventory: Set<string> = new Set();
  game_over: boolean = false;
  action_points_remaining: number = 0;
  action_points_max: number = 0;
  visited_actions: Set<string> = new Set();
  pending_scene: string | null = null;

  get location(): string {
    return this.status.location;
  }
  set location(v: string) {
    this.status.location = v;
  }

  has_item(item: string): boolean {
    return this.inventory.has(item);
  }

  has_flag(flag: string): boolean {
    return this.flags[flag] === true;
  }

  is_first_loop(): boolean {
    return this.status.loop_count === 0;
  }

  has_all_key_items(): boolean {
    for (const item of KEY_ITEMS) {
      if (!this.inventory.has(item)) return false;
    }
    return true;
  }

  has_all_normal_items(): boolean {
    for (const item of NORMAL_ITEMS) {
      if (!this.inventory.has(item)) return false;
    }
    return true;
  }

  loop_count(): number {
    return this.status.loop_count;
  }
}
