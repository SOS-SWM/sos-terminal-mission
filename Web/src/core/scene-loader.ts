// scene-loader.ts — 解析 Engine/books/*.md 为 Scene
// 对应 scene.py:295-498 中的 build_scenario / _load_book_scenes / _extract_lines /
// _make_scene / _entries_from_book / _entry_from_book_line / _is_system_text /
// _effect_for_system / _validate_scenario

import {
  Choice,
  Command,
  LogEntry,
  Scene,
  type EffectTag,
} from "./models";
import { KEY_ITEMS, NORMAL_ITEMS } from "./constants";
import {
  AP_FINAL_TARGETS,
  AP_SCENES_LOOP1,
  AP_SCENES_LOOP2,
  MAP_HUBS,
  SCENE_IDS,
  SCENE_META,
  STATUS_FIELDS,
  SYSTEM_PREFIXES,
  type ChoiceMetaSpec,
  type EntryMetaSpec,
  type SceneMeta,
} from "./scene-meta";

// 三正则：与 Python 端逐字符一致
//   ^### 场景ID：`(.+?)`\s*$
const SCENE_HEADING_RE = /^### 场景ID：`(.+?)`\s*$/gm;
//   ^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$
const TIMED_LINE_RE = /^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$/;
//   ^([^>\n]+?)\s*>\s*(.+)$
const SPEAKER_RE = /^([^>\n]+?)\s*>\s*(.+)$/;

const COMMAND_LABELS: ReadonlyMap<string, string> = new Map([
  ["HELP", "显示帮助"],
  ["STATUS", "查看当前状态"],
  ["INVENTORY", "查看背包物品"],
  ["MAP", "查看地图"],
]);

// 输入：四章 Markdown 原文（顺序对应 Chapter1..Chapter4）
// 输出：完整的 sceneId → Scene Map
export function buildScenario(bookTexts: ReadonlyArray<string>): Map<string, Scene> {
  const rawScenes = loadBookScenes(bookTexts);
  const scenes = new Map<string, Scene>();
  for (const sceneId of SCENE_META.keys()) {
    scenes.set(sceneId, makeScene(sceneId, rawScenes));
  }
  validateScenario(scenes);
  return scenes;
}

function loadBookScenes(bookTexts: ReadonlyArray<string>): Map<string, string[]> {
  const rawScenes = new Map<string, string[]>();
  for (const text of bookTexts) {
    const matches = matchAllSceneHeadings(text);
    for (let i = 0; i < matches.length; i++) {
      const m = matches[i];
      const title = m.title;
      const sceneId = SCENE_IDS.get(title);
      if (sceneId === undefined) continue;
      const blockStart = m.end;
      const blockEnd = i + 1 < matches.length ? matches[i + 1].start : text.length;
      rawScenes.set(sceneId, extractLines(text.slice(blockStart, blockEnd)));
    }
  }
  // 校验：所有 SCENE_META 中没有手写 entries 的场景必须能在书里找到
  const missing: string[] = [];
  for (const [sceneId, meta] of SCENE_META) {
    if (!rawScenes.has(sceneId) && !meta.entries) {
      missing.push(sceneId);
    }
  }
  if (missing.length > 0) {
    missing.sort();
    throw new Error("Missing scenes in books: " + missing.join(", "));
  }
  return rawScenes;
}

interface SceneHeadingMatch {
  title: string;
  start: number;
  end: number;
}
function matchAllSceneHeadings(text: string): SceneHeadingMatch[] {
  const out: SceneHeadingMatch[] = [];
  // 重置 RegExp 状态
  SCENE_HEADING_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = SCENE_HEADING_RE.exec(text)) !== null) {
    out.push({ title: m[1], start: m.index, end: m.index + m[0].length });
  }
  return out;
}

function extractLines(block: string): string[] {
  const marker = "#### Lines";
  const markerIndex = block.indexOf(marker);
  if (markerIndex === -1) return [];
  const fenceStart = block.indexOf("```text", markerIndex);
  if (fenceStart === -1) return [];
  const contentStart = block.indexOf("\n", fenceStart);
  if (contentStart === -1) return [];
  const fenceEnd = block.indexOf("```", contentStart + 1);
  if (fenceEnd === -1) return [];
  const inner = block.slice(contentStart + 1, fenceEnd);
  return inner.split("\n").map((line) => line.replace(/[ \t]+$/, ""));
}

function makeScene(
  sceneId: string,
  rawScenes: Map<string, string[]>,
): Scene {
  const meta = SCENE_META.get(sceneId)!;
  const entries: LogEntry[] = meta.entries
    ? entriesFromMeta(meta.entries)
    : entriesFromBook(rawScenes.get(sceneId) ?? []);
  return new Scene({
    id: sceneId,
    entries,
    choices: (meta.choices ?? []).map(choiceFromTuple),
    commands: commonCommands(meta.commands ?? []),
    hint: meta.hint ?? "",
    set_location: meta.location ?? null,
    set_worldline: meta.worldline ?? null,
    grant_items: [...(meta.items ?? [])],
    consume_items: [...(meta.consume ?? [])],
    set_flags: { ...(meta.flags ?? {}) },
    triggers_loop_reset: !!meta.loop_reset,
    auto_next_scene: meta.auto ?? null,
    terminal_scene: !!meta.terminal,
  });
}

function entriesFromMeta(specs: ReadonlyArray<EntryMetaSpec>): LogEntry[] {
  const entries: LogEntry[] = [];
  for (const spec of specs) {
    const kind = spec[0];
    if (kind === "dialogue") {
      const [, speaker, text] = spec;
      entries.push(dialogue(speaker, text));
    } else if (kind === "narration") {
      const [, text] = spec;
      entries.push(narration(text));
    } else if (kind === "system") {
      const [, text] = spec;
      entries.push(systemEntry(text));
    } else {
      throw new Error(`Unknown synthetic entry kind: ${kind}`);
    }
  }
  return entries;
}

function choiceFromTuple(spec: ChoiceMetaSpec): Choice {
  const [index, label, target] = spec;
  const requires_flag = spec.length >= 4 ? (spec[3] ?? null) : null;
  const requires_item = spec.length >= 5 ? (spec[4] ?? null) : null;
  return new Choice({
    index,
    label,
    target_scene: target,
    requires_flag,
    requires_item,
  });
}

function entriesFromBook(lines: ReadonlyArray<string>): LogEntry[] {
  const entries: LogEntry[] = [];
  let currentTs = "";
  for (const line of lines) {
    const stripped = line.replace(/[ \t\r]+$/, "");
    if (stripped === "") {
      if (entries.length > 0 && entries[entries.length - 1].kind !== "fx") {
        entries.push(separator());
      }
      continue;
    }
    const [entry, explicitTs] = entryFromBookLine(stripped, currentTs);
    entries.push(entry);
    if (explicitTs) currentTs = explicitTs;
  }
  while (entries.length > 0 && entries[entries.length - 1].kind === "fx") {
    entries.pop();
  }
  return entries;
}

function entryFromBookLine(
  line: string,
  inheritedTs: string,
): [LogEntry, string] {
  let ts = "";
  let text = line;
  const timed = TIMED_LINE_RE.exec(line);
  if (timed) {
    ts = timed[1];
    text = timed[2];
  }
  const displayTs = ts || inheritedTs;

  const speaker = SPEAKER_RE.exec(text);
  if (speaker) {
    return [
      dialogue(speaker[1].trim(), speaker[2].trim(), "typewriter", displayTs),
      ts,
    ];
  }
  if (isSystemText(text)) {
    return [systemEntry(text, effectForSystem(text), ts), ts];
  }
  return [narration(text, "typewriter", displayTs), ts];
}

function isSystemText(text: string): boolean {
  for (const p of SYSTEM_PREFIXES) {
    if (text.startsWith(p)) return true;
  }
  if (text.startsWith("KYON.STATUS")) return true;
  const lstrip = text.replace(/^\s+/, "");
  for (const f of STATUS_FIELDS) {
    if (lstrip.startsWith(f)) return true;
  }
  if (text.startsWith("}")) return true;
  return false;
}

function effectForSystem(text: string): EffectTag {
  if (text.includes("WORLDLINE")) return "worldline_shift";
  if (text.includes("WARNING") || text.includes("WALLET_DAMAGE")) return "warning";
  if (text.includes("ROUTE")) return "route_trace";
  if (text.includes("CALL_NOISE")) return "jitter";
  if (text.includes("STATUS")) return "glitch";
  return "typewriter_fast";
}

function narration(text: string, effect: EffectTag = "typewriter", ts = ""): LogEntry {
  return new LogEntry({
    kind: "narration",
    speaker: null,
    text,
    effect,
    speed: 1.0,
    timestamp: ts,
  });
}

function dialogue(speaker: string, text: string, effect: EffectTag = "typewriter", ts = ""): LogEntry {
  return new LogEntry({
    kind: "dialogue",
    speaker,
    text,
    effect,
    speed: 1.0,
    timestamp: ts,
  });
}

function systemEntry(text: string, effect: EffectTag = "typewriter_fast", ts = ""): LogEntry {
  return new LogEntry({
    kind: "system",
    speaker: null,
    text,
    effect,
    speed: 0.6,
    timestamp: ts,
  });
}

function separator(): LogEntry {
  return new LogEntry({
    kind: "fx",
    speaker: null,
    text: "",
    effect: "separator",
    speed: 1.0,
  });
}

function commonCommands(names: ReadonlyArray<string>): Command[] {
  return names.map((n) => {
    const desc = COMMAND_LABELS.get(n);
    if (!desc) throw new Error(`Unknown command: ${n}`);
    return new Command({ name: n, description: desc, hint: n });
  });
}

// 对应 _validate_scenario：验证道具白名单 / 选项目标 / 标志引用 / dead-end / unreachable
function validateScenario(allScenes: Map<string, Scene>): void {
  const allowedItems = new Set<string>([...KEY_ITEMS, ...NORMAL_ITEMS]);
  const allFlags = new Set<string>();
  for (const sc of allScenes.values()) {
    for (const k of Object.keys(sc.set_flags)) allFlags.add(k);
  }
  // engine 运行时动态注入的 flag
  allFlags.add("has_all_key_items");

  const invalidItems: string[] = [];
  const invalidRequiredItems: string[] = [];
  const missingRequiredFlags: string[] = [];
  const missingTargets: string[] = [];
  const duplicateChoiceIndexes: string[] = [];
  const invalidAutoNext: string[] = [];
  const deadEndScenes: string[] = [];

  for (const scene of allScenes.values()) {
    if (scene.auto_next_scene && !allScenes.has(scene.auto_next_scene)) {
      invalidAutoNext.push(`${scene.id}->${scene.auto_next_scene}`);
    }
    for (const item of scene.grant_items) {
      if (!allowedItems.has(item)) invalidItems.push(`${scene.id}:${item}`);
    }
    const seen = new Set<number>();
    for (const choice of scene.choices) {
      if (seen.has(choice.index)) {
        duplicateChoiceIndexes.push(`${scene.id}:${choice.index}`);
      }
      seen.add(choice.index);
      if (!allScenes.has(choice.target_scene)) {
        missingTargets.push(`${scene.id}->${choice.target_scene}`);
      }
      if (choice.requires_item && !allowedItems.has(choice.requires_item)) {
        invalidRequiredItems.push(`${scene.id}:${choice.requires_item}`);
      }
      if (choice.requires_flag && !allFlags.has(choice.requires_flag)) {
        missingRequiredFlags.push(`${scene.id}:${choice.requires_flag}`);
      }
    }
    const hasProgressExit =
      scene.choices.length > 0 ||
      scene.auto_next_scene != null ||
      scene.triggers_loop_reset;
    if (!hasProgressExit && !scene.terminal_scene) {
      deadEndScenes.push(scene.id);
    }
  }

  const unreachable = findUnreachableScenes(allScenes);
  const errors: ReadonlyArray<[string, string[]]> = [
    ["Invalid grant_items outside models constraints", invalidItems],
    ["Invalid requires_item outside models constraints", invalidRequiredItems],
    ["Unknown requires_flag references", missingRequiredFlags],
    ["Broken auto_next_scene links", invalidAutoNext],
    ["Broken choice target_scene links", missingTargets],
    ["Duplicate choice indexes in scene", duplicateChoiceIndexes],
    ["Dead-end scenes without progression exit", deadEndScenes],
    ["Unreachable scenes from c1a_morning_call", unreachable],
  ];
  for (const [msg, vals] of errors) {
    if (vals.length > 0) throw new Error(msg + ": " + vals.join(", "));
  }
}

function findUnreachableScenes(allScenes: Map<string, Scene>): string[] {
  const implicitEdges = new Map<string, string[]>();
  for (const [sid, sc] of allScenes) {
    const extras: string[] = [];
    if (sc.triggers_loop_reset) {
      extras.push("c1b_morning_reboot");
      if (allScenes.has("c4a_loop_start")) extras.push("c4a_loop_start");
    }
    if (MAP_HUBS.has(sid)) {
      for (const final of AP_FINAL_TARGETS.values()) {
        if (allScenes.has(final)) extras.push(final);
      }
      for (const apScene of AP_SCENES_LOOP1) {
        if (allScenes.has(apScene)) extras.push(apScene);
      }
      for (const apScene of AP_SCENES_LOOP2) {
        if (allScenes.has(apScene)) extras.push(apScene);
      }
    }
    if (extras.length > 0) implicitEdges.set(sid, extras);
  }
  const visited = new Set<string>();
  const queue: string[] = ["c1a_morning_call"];
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current) || !allScenes.has(current)) continue;
    visited.add(current);
    const scene = allScenes.get(current)!;
    if (scene.auto_next_scene) queue.push(scene.auto_next_scene);
    for (const c of scene.choices) queue.push(c.target_scene);
    const extras = implicitEdges.get(current);
    if (extras) queue.push(...extras);
  }
  const out: string[] = [];
  for (const sid of allScenes.keys()) if (!visited.has(sid)) out.push(sid);
  out.sort();
  return out;
}
