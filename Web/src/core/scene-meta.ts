// scene-meta.ts — 对应 Engine/scene.py 中的元数据常量与 SCENE_META 字典
// 字段名与原 Python 字典 1:1 保持

import type { EffectTag } from "./models";
import { WORLDLINE_STABLE } from "./constants";

// 原 Python 中 SCENE_META 的元数据形状（部分字段全为可选）
export interface SceneMeta {
  location?: string;
  // entries 是预先在代码里手写的合成条目（仅用于 c2a_map_return / c2b_map_return 等少量场景）
  entries?: Array<EntryMetaSpec>;
  // 选项以 [index, label, target_scene, requires_flag?, requires_item?] 元组形式给出
  choices?: Array<ChoiceMetaSpec>;
  commands?: ReadonlyArray<string>;
  hint?: string;
  set_location?: string | null;
  set_worldline?: string | null;
  // 别名 grant_items/items；scene.py 用的是 "items"
  items?: ReadonlyArray<string>;
  consume?: ReadonlyArray<string>;
  flags?: Readonly<Record<string, boolean>>;
  loop_reset?: boolean;
  auto?: string;
  terminal?: boolean;
  worldline?: string;
}

export type EntryMetaSpec =
  | readonly ["dialogue", string, string]
  | readonly ["narration", string]
  | readonly ["system", string];

// [index, label, target] | [index, label, target, requires_flag] | [index, label, target, requires_flag, requires_item]
export type ChoiceMetaSpec =
  | readonly [number, string, string]
  | readonly [number, string, string, string | null]
  | readonly [number, string, string, string | null, string | null];

// Chapter 3 显示用时间槽
export const CH3_TIME_SLOTS_LOOP1: ReadonlyArray<string> = [
  "10:15",
  "12:00",
  "15:00",
  "17:30",
];
export const CH3_TIME_SLOTS_LOOP2: ReadonlyArray<string> = [
  "09:50",
  "10:10",
  "10:15",
  "11:30",
  "13:45",
  "16:30",
  "19:20",
];

// 进入即消耗 1 AP 的场景集合
export const AP_SCENES_LOOP1: ReadonlySet<string> = new Set([
  "c3a_street",
  "c3a_store",
  "c3a_nagato",
  "c3a_rooftop",
]);
export const AP_SCENES_LOOP2: ReadonlySet<string> = new Set([
  "c3b_street",
  "c3b_store",
  "c3b_store_revisit",
  "c3b_nagato",
  "c3b_nagato_revisit",
  "c3b_rooftop",
  "c3b_rooftop_revisit",
]);

// 地图 hub 场景
export const MAP_HUBS: ReadonlySet<string> = new Set([
  "c2a_paid",
  "c2a_map_return",
  "c2b_paid",
  "c2b_map_return",
]);

// 进入这些场景时初始化 AP
export const AP_INIT_SCENES: ReadonlyMap<string, number> = new Map([
  ["c2a_paid", 4],
  ["c2b_paid", 7],
]);

// AP 耗尽后的最终目标
export const AP_FINAL_TARGETS: ReadonlyMap<number, string> = new Map([
  [4, "c4a_final"],
  [7, "c4b_final"],
]);

// 二周目智能路由：访问统一目标时按是否首访/物品决定实际跳到哪
export interface LoopRoute {
  revisit_scene: string;
  revisit_requires: ReadonlySet<string>;
}
export const LOOP2_ROUTING: ReadonlyMap<string, LoopRoute> = new Map([
  [
    "c3b_store",
    {
      revisit_scene: "c3b_store_revisit",
      revisit_requires: new Set(["普通的怪兽贴纸"]),
    },
  ],
  [
    "c3b_nagato",
    {
      revisit_scene: "c3b_nagato_revisit",
      revisit_requires: new Set(["普通的灯带"]),
    },
  ],
  [
    "c3b_rooftop",
    {
      revisit_scene: "c3b_rooftop_revisit",
      revisit_requires: new Set(["玩偶服", "大红按钮"]),
    },
  ],
]);

// 系统行前缀（用于把行识别为 system kind）
export const SYSTEM_PREFIXES: ReadonlyArray<string> = [
  "SYSTEM",
  "DATE",
  "WORLDLINE",
  "USER_HOST",
  "ACCESS",
  "WARNING",
  "CALL",
  "MESSAGE",
  "STATUS",
  "Kyon.status",
  "PAYMENT_",
  "WALLET_",
  "LOCATION_LIST",
  "ROUTE:",
];

// 二级状态字段（缩进后开头匹配）
export const STATUS_FIELDS: ReadonlyArray<string> = [
  "SLEEP",
  "WALLET",
  "SANITY",
  "DEJA_VU",
  "CAFFEINE",
  "USEFUL_HINT",
];

// 中文场景标题 → 内部 ID
export const SCENE_IDS: ReadonlyMap<string, string> = new Map([
  ["第一次未轮回：清晨来电", "c1a_morning_call"],
  ["第一次未轮回：被窝抵抗", "c1a_blanket"],
  ["第一次未轮回：出门去咖啡厅", "c1a_leave_home"],
  ["轮回后：清晨重启", "c1b_morning_reboot"],
  ["轮回后：确认状态", "c1b_status"],
  ["轮回后：再次抵抗", "c1b_blanket"],
  ["轮回后：带着既视感出门", "c1b_leave_home"],
  ["第一次未轮回：咖啡厅集合", "c2a_cafe"],
  ["第一次未轮回：抗议账单", "c2a_protest"],
  ["第一次未轮回：买单后开放地图", "c2a_paid"],
  ["轮回后：咖啡厅再次集合", "c2b_cafe"],
  ["轮回后：咖啡厅状态确认", "c2b_status"],
  ["轮回后：抗议账单", "c2b_protest"],
  ["轮回后：买单后开放地图", "c2b_paid"],
  ["第一次未轮回：大街调查", "c3a_street"],
  ["第一次未轮回：便利店的普通贴纸", "c3a_store"],
  ["第一次未轮回：长门公寓的普通灯带", "c3a_nagato"],
  ["第一次未轮回：天台的普通风筝线", "c3a_rooftop"],
  ["轮回后：大街再调查", "c3b_street"],
  ["轮回后：便利店首访", "c3b_store"],
  ["轮回后：长门公寓首访", "c3b_nagato"],
  ["轮回后：便利店重访", "c3b_store_revisit"],
  ["轮回后：拒绝玩偶服失败", "c3b_mikuru_refuse"],
  ["轮回后：长门公寓重访", "c3b_nagato_revisit"],
  ["轮回后：天台首访", "c3b_rooftop"],
  ["轮回后：天台重访", "c3b_rooftop_revisit"],
  ["第一次未轮回：天台最终验收", "c4a_final"],
  ["轮回后：天台最终验收", "c4b_final"],
  ["结局：关键物品不足", "c4b_insufficient"],
  ["结局：执行终端任务——UFO演出", "c4b_true_end"],
]);

// SCENE_META — 与 scene.py:125-292 1:1 对应
export const SCENE_META: ReadonlyMap<string, SceneMeta> = new Map([
  [
    "c1a_morning_call",
    {
      location: "home",
      choices: [
        [1, "把头埋进被子里装死。", "c1a_blanket"],
        [2, "叹口气，乖乖起床穿衣服。", "c1a_leave_home"],
      ],
      commands: ["STATUS", "HELP"],
    },
  ],
  ["c1a_blanket", { location: "home", choices: [[1, "起床。", "c1a_leave_home"]] }],
  ["c1a_leave_home", { location: "home", auto: "c2a_cafe" }],
  [
    "c1b_morning_reboot",
    {
      location: "home",
      choices: [
        [1, "再次把头埋进被子里。", "c1b_blanket"],
        [2, "直接起床，避免重复无意义抵抗。", "c1b_leave_home"],
        [3, "输入状态指令，确认自己的精神状态。", "c1b_status"],
      ],
      commands: ["STATUS", "HELP"],
    },
  ],
  ["c1b_status", { location: "home", choices: [[1, "起床。", "c1b_leave_home"]] }],
  [
    "c1b_blanket",
    { location: "home", choices: [[1, "承认失败并起床。", "c1b_leave_home"]] },
  ],
  ["c1b_leave_home", { location: "home", auto: "c2b_cafe" }],
  [
    "c2a_cafe",
    {
      location: "cafe",
      choices: [
        [1, "默默拿起账单。", "c2a_paid"],
        [2, "对着账单进行抗议。", "c2a_protest"],
      ],
      commands: ["STATUS", "HELP"],
    },
  ],
  [
    "c2a_protest",
    { location: "cafe", choices: [[1, "买单。", "c2a_paid"]] },
  ],
  [
    "c2a_paid",
    {
      location: "cafe",
      choices: [
        [1, "GO STREET", "c3a_street"],
        [2, "GO STORE", "c3a_store"],
        [3, "GO NAGATO_APT", "c3a_nagato"],
        [4, "GO ROOFTOP", "c3a_rooftop"],
      ],
      commands: ["STATUS", "INVENTORY", "MAP", "HELP"],
    },
  ],
  [
    "c2a_map_return",
    {
      location: "cafe",
      entries: [["dialogue", "Kyon", "接下来去哪呢？"]],
      choices: [
        [1, "GO STREET", "c3a_street"],
        [2, "GO STORE", "c3a_store"],
        [3, "GO NAGATO_APT", "c3a_nagato"],
        [4, "GO ROOFTOP", "c3a_rooftop"],
      ],
      commands: ["STATUS", "INVENTORY", "MAP", "HELP"],
    },
  ],
  [
    "c2b_cafe",
    {
      location: "cafe",
      choices: [
        [1, "熟练地拿起账单。", "c2b_paid"],
        [2, "即使知道没用，也再次抗议。", "c2b_protest"],
        [3, "输入状态指令，确认既视感。", "c2b_status"],
      ],
      commands: ["STATUS", "HELP"],
    },
  ],
  [
    "c2b_status",
    { location: "cafe", choices: [[1, "买单。", "c2b_paid"]] },
  ],
  [
    "c2b_protest",
    { location: "cafe", choices: [[1, "买单。", "c2b_paid"]] },
  ],
  [
    "c2b_paid",
    {
      location: "cafe",
      choices: [
        [1, "GO STREET", "c3b_street"],
        [2, "GO STORE", "c3b_store"],
        [3, "GO NAGATO_APT", "c3b_nagato"],
        [4, "GO ROOFTOP", "c3b_rooftop"],
      ],
      commands: ["STATUS", "INVENTORY", "MAP", "HELP"],
    },
  ],
  [
    "c2b_map_return",
    {
      location: "cafe",
      entries: [["dialogue", "Kyon", "接下来去哪呢？"]],
      choices: [
        [1, "GO STREET", "c3b_street"],
        [2, "GO STORE", "c3b_store"],
        [3, "GO NAGATO_APT", "c3b_nagato"],
        [4, "GO ROOFTOP", "c3b_rooftop"],
      ],
      commands: ["STATUS", "INVENTORY", "MAP", "HELP"],
    },
  ],
  [
    "c3a_street",
    { location: "street", choices: [[1, "返回自由移动。", "c2a_map_return"]] },
  ],
  [
    "c3a_store",
    {
      location: "store",
      items: ["普通的怪兽贴纸"],
      choices: [[1, "返回自由移动。", "c2a_map_return"]],
    },
  ],
  [
    "c3a_nagato",
    {
      location: "nagato_apt",
      items: ["普通的灯带"],
      choices: [[1, "返回自由移动。", "c2a_map_return"]],
    },
  ],
  [
    "c3a_rooftop",
    {
      location: "rooftop",
      items: ["普通的风筝线"],
      choices: [[1, "返回自由移动。", "c2a_map_return"]],
    },
  ],
  [
    "c3b_street",
    { location: "street", choices: [[1, "返回自由移动。", "c2b_map_return"]] },
  ],
  [
    "c3b_store",
    {
      location: "store",
      items: ["普通的怪兽贴纸"],
      choices: [[1, "返回自由移动。", "c2b_map_return"]],
    },
  ],
  [
    "c3b_nagato",
    {
      location: "nagato_apt",
      items: ["普通的灯带"],
      choices: [[1, "返回自由移动。", "c2b_map_return"]],
    },
  ],
  [
    "c3b_store_revisit",
    {
      location: "store",
      items: ["玩偶服"],
      consume: ["普通的怪兽贴纸"],
      choices: [
        [1, "接过玩偶服。", "c2b_map_return"],
        [2, "试图把命运推回给学姐。", "c3b_mikuru_refuse"],
      ],
    },
  ],
  [
    "c3b_mikuru_refuse",
    {
      location: "store",
      choices: [
        [1, "学姐楚楚可怜的眼神让我无法拒绝。", "c2b_map_return"],
      ],
    },
  ],
  [
    "c3b_nagato_revisit",
    {
      location: "nagato_apt",
      items: ["大红按钮"],
      consume: ["普通的灯带"],
      choices: [[1, "返回自由移动。", "c2b_map_return"]],
    },
  ],
  [
    "c3b_rooftop",
    {
      location: "rooftop",
      items: ["普通的风筝线"],
      choices: [[1, "返回自由移动。", "c2b_map_return"]],
    },
  ],
  [
    "c3b_rooftop_revisit",
    {
      location: "rooftop",
      items: ["超能力飞行装置"],
      consume: ["普通的风筝线"],
      choices: [[1, "返回自由移动。", "c2b_map_return"]],
    },
  ],
  ["c4a_final", { location: "rooftop", loop_reset: true }],
  [
    "c4b_final",
    {
      location: "rooftop",
      choices: [
        [1, "执行终端任务。", "c4b_insufficient"],
        [2, "执行终端任务——UFO演出。", "c4b_true_end", "has_all_key_items"],
      ],
      commands: ["STATUS", "INVENTORY", "HELP"],
    },
  ],
  ["c4b_insufficient", { location: "rooftop", loop_reset: true }],
  [
    "c4b_true_end",
    {
      location: "rooftop",
      worldline: WORLDLINE_STABLE,
      terminal: true,
      flags: { true_end: true },
    },
  ],
]);
