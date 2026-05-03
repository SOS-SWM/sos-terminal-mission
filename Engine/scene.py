"""
scenario.py - Scenario loader for the original scripts in books/Chapter1-4.md.

The markdown files are the source of truth for plot text. This module imports
those documents into Scene objects and validates the resulting scene graph.
"""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from typing import Iterable

from models import (
    Choice,
    Command,
    KEY_ITEMS,
    EffectTag,
    LogEntry,
    NORMAL_ITEMS,
    Scene,
    WORLDLINE_STABLE,
    WORLDLINE_UNSTABLE,
)


BOOK_DIR = Path(__file__).with_name("books")
BOOK_FILES = ("Chapter1.md", "Chapter2.md", "Chapter3.md", "Chapter4.md")
SCENE_HEADING_RE = re.compile(r"^### 场景ID：`(.+?)`\s*$", re.MULTILINE)
TIMED_LINE_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$")
SPEAKER_RE = re.compile(r"^([^>\n]+?)\s*>\s*(.+)$")

# Chapter 3 display-only time slots (base time per AP action)
CH3_TIME_SLOTS_LOOP1 = ["10:15", "12:00", "15:00", "17:30"]
CH3_TIME_SLOTS_LOOP2 = ["09:50", "10:10", "10:15", "11:30", "13:45", "16:30", "19:20"]

# Scenes that consume an action point when entered from a map hub
AP_SCENES_LOOP1 = {"c3a_street", "c3a_store", "c3a_nagato", "c3a_rooftop"}
AP_SCENES_LOOP2 = {
    "c3b_street",
    "c3b_store",
    "c3b_store_revisit",
    "c3b_nagato",
    "c3b_nagato_revisit",
    "c3b_rooftop",
    "c3b_rooftop_revisit",
}

# Map hub scene IDs
MAP_HUBS = {"c2a_paid", "c2a_map_return", "c2b_paid", "c2b_map_return"}

# AP initializer scenes
AP_INIT_SCENES = {"c2a_paid": 4, "c2b_paid": 7}

# Auto-final targets when AP runs out
AP_FINAL_TARGETS = {4: "c4a_final", 7: "c4b_final"}

# Smart routing for second-loop unified location targets
LOOP2_ROUTING: dict[str, dict] = {
    "c3b_store": {
        "revisit_scene": "c3b_store_revisit",
        "revisit_requires": {"普通的怪兽贴纸"},
    },
    "c3b_nagato": {
        "revisit_scene": "c3b_nagato_revisit",
        "revisit_requires": {"普通的灯带"},
    },
    "c3b_rooftop": {
        "revisit_scene": "c3b_rooftop_revisit",
        "revisit_requires": {"玩偶服", "大红按钮"},
    },
}

SYSTEM_PREFIXES = (
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
)

SCENE_IDS = {
    "第一次未轮回：清晨来电": "c1a_morning_call",
    "第一次未轮回：被窝抵抗": "c1a_blanket",
    "第一次未轮回：出门去咖啡厅": "c1a_leave_home",
    "轮回后：清晨重启": "c1b_morning_reboot",
    "轮回后：确认状态": "c1b_status",
    "轮回后：再次抵抗": "c1b_blanket",
    "轮回后：带着既视感出门": "c1b_leave_home",
    "第一次未轮回：咖啡厅集合": "c2a_cafe",
    "第一次未轮回：抗议账单": "c2a_protest",
    "第一次未轮回：买单后开放地图": "c2a_paid",
    "轮回后：咖啡厅再次集合": "c2b_cafe",
    "轮回后：咖啡厅状态确认": "c2b_status",
    "轮回后：抗议账单": "c2b_protest",
    "轮回后：买单后开放地图": "c2b_paid",
    "第一次未轮回：大街调查": "c3a_street",
    "第一次未轮回：便利店的普通贴纸": "c3a_store",
    "第一次未轮回：长门公寓的普通灯带": "c3a_nagato",
    "第一次未轮回：天台的普通风筝线": "c3a_rooftop",
    "轮回后：大街再调查": "c3b_street",
    "轮回后：便利店首访": "c3b_store",
    "轮回后：长门公寓首访": "c3b_nagato",
    "轮回后：便利店重访": "c3b_store_revisit",
    "轮回后：拒绝玩偶服失败": "c3b_mikuru_refuse",
    "轮回后：长门公寓重访": "c3b_nagato_revisit",
    "轮回后：天台首访": "c3b_rooftop",
    "轮回后：天台重访": "c3b_rooftop_revisit",
    "第一次未轮回：天台最终验收": "c4a_final",
    "轮回后：天台最终验收": "c4b_final",
    "结局：关键物品不足": "c4b_insufficient",
    "结局：执行终端任务——UFO演出": "c4b_true_end",
}

SCENE_META: dict[str, dict] = {
    "c1a_morning_call": {
        "location": "home",
        "choices": [
            (1, "把头埋进被子里装死。", "c1a_blanket"),
            (2, "叹口气，乖乖起床穿衣服。", "c1a_leave_home"),
        ],
        "commands": ("status", "help"),
    },
    "c1a_blanket": {"location": "home", "choices": [(1, "起床。", "c1a_leave_home")]},
    "c1a_leave_home": {"location": "home", "auto": "c2a_cafe"},
    "c1b_morning_reboot": {
        "location": "home",
        "choices": [
            (1, "再次把头埋进被子里。", "c1b_blanket"),
            (2, "直接起床，避免重复无意义抵抗。", "c1b_leave_home"),
            (3, "输入状态指令，确认自己的精神状态。", "c1b_status"),
        ],
        "commands": ("status", "help"),
    },
    "c1b_status": {"location": "home", "choices": [(1, "起床。", "c1b_leave_home")]},
    "c1b_blanket": {
        "location": "home",
        "choices": [(1, "承认失败并起床。", "c1b_leave_home")],
    },
    "c1b_leave_home": {"location": "home", "auto": "c2b_cafe"},
    "c2a_cafe": {
        "location": "cafe",
        "choices": [
            (1, "默默拿起账单。", "c2a_paid"),
            (2, "对着账单进行抗议。", "c2a_protest"),
        ],
        "commands": ("status", "help"),
    },
    "c2a_protest": {"location": "cafe", "choices": [(1, "买单。", "c2a_paid")]},
    "c2a_paid": {
        "location": "cafe",
        "choices": [
            (1, "Go Street", "c3a_street"),
            (2, "Go Store", "c3a_store"),
            (3, "Go Nagato_Apt", "c3a_nagato"),
            (4, "Go Rooftop", "c3a_rooftop"),
        ],
        "commands": ("status", "inventory", "map", "help"),
    },
    "c2a_map_return": {
        "location": "cafe",
        "entries": [("dialogue", "Kyon", "接下来去哪呢？")],
        "choices": [
            (1, "Go Street", "c3a_street"),
            (2, "Go Store", "c3a_store"),
            (3, "Go Nagato_Apt", "c3a_nagato"),
            (4, "Go Rooftop", "c3a_rooftop"),
        ],
        "commands": ("status", "inventory", "map", "help"),
    },
    "c2b_cafe": {
        "location": "cafe",
        "choices": [
            (1, "熟练地拿起账单。", "c2b_paid"),
            (2, "即使知道没用，也再次抗议。", "c2b_protest"),
            (3, "输入状态指令，确认既视感。", "c2b_status"),
        ],
        "commands": ("status", "help"),
    },
    "c2b_status": {"location": "cafe", "choices": [(1, "买单。", "c2b_paid")]},
    "c2b_protest": {"location": "cafe", "choices": [(1, "买单。", "c2b_paid")]},
    "c2b_paid": {
        "location": "cafe",
        "choices": [
            (1, "Go Street", "c3b_street"),
            (2, "Go Store", "c3b_store"),
            (3, "Go Nagato_Apt", "c3b_nagato"),
            (4, "Go Rooftop", "c3b_rooftop"),
        ],
        "commands": ("status", "inventory", "map", "help"),
    },
    "c2b_map_return": {
        "location": "cafe",
        "entries": [("dialogue", "Kyon", "接下来去哪呢？")],
        "choices": [
            (1, "Go Street", "c3b_street"),
            (2, "Go Store", "c3b_store"),
            (3, "Go Nagato_Apt", "c3b_nagato"),
            (4, "Go Rooftop", "c3b_rooftop"),
        ],
        "commands": ("status", "inventory", "map", "help"),
    },
    "c3a_street": {
        "location": "street",
        "choices": [(1, "返回自由移动。", "c2a_map_return")],
    },
    "c3a_store": {
        "location": "store",
        "items": ["普通的怪兽贴纸"],
        "choices": [(1, "返回自由移动。", "c2a_map_return")],
    },
    "c3a_nagato": {
        "location": "nagato_apt",
        "items": ["普通的灯带"],
        "choices": [(1, "返回自由移动。", "c2a_map_return")],
    },
    "c3a_rooftop": {
        "location": "rooftop",
        "items": ["普通的风筝线"],
        "choices": [(1, "返回自由移动。", "c2a_map_return")],
    },
    "c3b_street": {
        "location": "street",
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c3b_store": {
        "location": "store",
        "items": ["普通的怪兽贴纸"],
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c3b_nagato": {
        "location": "nagato_apt",
        "items": ["普通的灯带"],
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c3b_store_revisit": {
        "location": "store",
        "items": ["玩偶服"],
        "consume": ["普通的怪兽贴纸"],
        "choices": [
            (1, "接过玩偶服。", "c2b_map_return"),
            (2, "试图把命运推回给学姐。", "c3b_mikuru_refuse"),
        ],
    },
    "c3b_mikuru_refuse": {
        "location": "store",
        "choices": [(1, "学姐楚楚可怜的眼神让我无法拒绝。", "c2b_map_return")],
    },
    "c3b_nagato_revisit": {
        "location": "nagato_apt",
        "items": ["大红按钮"],
        "consume": ["普通的灯带"],
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c3b_rooftop": {
        "location": "rooftop",
        "items": ["普通的风筝线"],
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c3b_rooftop_revisit": {
        "location": "rooftop",
        "items": ["超能力飞行装置"],
        "consume": ["普通的风筝线"],
        "choices": [(1, "返回自由移动。", "c2b_map_return")],
    },
    "c4a_final": {"location": "rooftop", "loop_reset": True},
    "c4b_final": {
        "location": "rooftop",
        "choices": [
            (1, "执行终端任务。", "c4b_insufficient"),
            (2, "执行终端任务——UFO演出。", "c4b_true_end", "has_all_key_items"),
        ],
        "commands": ("status", "inventory", "help"),
    },
    "c4b_insufficient": {"location": "rooftop", "loop_reset": True},
    "c4b_true_end": {
        "location": "rooftop",
        "worldline": WORLDLINE_STABLE,
        "terminal": True,
        "flags": {"true_end": True},
    },
}


def build_scenario() -> dict[str, Scene]:
    raw_scenes = _load_book_scenes()
    scenes = {scene_id: _make_scene(scene_id, raw_scenes) for scene_id in SCENE_META}
    _validate_scenario(scenes)
    return scenes


def _load_book_scenes() -> dict[str, list[str]]:
    raw_scenes: dict[str, list[str]] = {}
    for file_name in BOOK_FILES:
        path = BOOK_DIR / file_name
        text = path.read_text(encoding="utf-8")
        matches = list(SCENE_HEADING_RE.finditer(text))
        for index, match in enumerate(matches):
            title = match.group(1)
            scene_id = SCENE_IDS.get(title)
            if scene_id is None:
                continue
            block_start = match.end()
            block_end = (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            )
            raw_scenes[scene_id] = _extract_lines(text[block_start:block_end])
    missing = sorted(
        scene_id
        for scene_id, meta in SCENE_META.items()
        if scene_id not in raw_scenes and "entries" not in meta
    )
    if missing:
        raise ValueError("Missing scenes in books: " + ", ".join(missing))
    return raw_scenes


def _extract_lines(block: str) -> list[str]:
    marker = "#### Lines"
    marker_index = block.find(marker)
    if marker_index == -1:
        return []
    fence_start = block.find("```text", marker_index)
    if fence_start == -1:
        return []
    content_start = block.find("\n", fence_start)
    fence_end = block.find("```", content_start + 1)
    if content_start == -1 or fence_end == -1:
        return []
    return [line.rstrip() for line in block[content_start + 1 : fence_end].splitlines()]


def _make_scene(scene_id: str, raw_scenes: dict[str, list[str]]) -> Scene:
    meta = SCENE_META[scene_id]
    entries = (
        _entries_from_meta(meta["entries"])
        if "entries" in meta
        else _entries_from_book(raw_scenes[scene_id])
    )
    return Scene(
        id=scene_id,
        entries=entries,
        choices=[_choice_from_tuple(choice) for choice in meta.get("choices", [])],
        commands=_common_commands(*meta.get("commands", ())),
        hint=meta.get("hint", ""),
        set_location=meta.get("location"),
        set_worldline=meta.get("worldline"),
        grant_items=list(meta.get("items", [])),
        consume_items=list(meta.get("consume", [])),
        set_flags=dict(meta.get("flags", {})),
        triggers_loop_reset=bool(meta.get("loop_reset", False)),
        auto_next_scene=meta.get("auto"),
        terminal_scene=bool(meta.get("terminal", False)),
    )


def _entries_from_meta(specs: Iterable[tuple]) -> list[LogEntry]:
    entries: list[LogEntry] = []
    for spec in specs:
        kind = spec[0]
        if kind == "dialogue":
            _, speaker, text = spec
            entries.append(_dialogue(speaker, text))
        elif kind == "narration":
            _, text = spec
            entries.append(_narration(text))
        elif kind == "system":
            _, text = spec
            entries.append(_system(text))
        else:
            raise ValueError(f"Unknown synthetic entry kind: {kind!r}")
    return entries


def _choice_from_tuple(spec: tuple) -> Choice:
    index, label, target, *rest = spec
    requires_flag = rest[0] if len(rest) >= 1 else None
    requires_item = rest[1] if len(rest) >= 2 else None
    return Choice(
        index,
        label,
        target,
        requires_flag=requires_flag,
        requires_item=requires_item,
    )


def _entries_from_book(lines: Iterable[str]) -> list[LogEntry]:
    entries: list[LogEntry] = []
    current_ts = ""
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if entries and entries[-1].kind != "fx":
                entries.append(_sep())
            continue
        entry, explicit_ts = _entry_from_book_line(stripped, current_ts)
        entries.append(entry)
        if explicit_ts:
            current_ts = explicit_ts
    while entries and entries[-1].kind == "fx":
        entries.pop()
    return entries


def _entry_from_book_line(line: str, inherited_ts: str) -> tuple[LogEntry, str]:
    """Return (LogEntry, explicit_timestamp_or_empty)."""
    # Extract [HH:MM:SS] prefix if present
    timed_match = TIMED_LINE_RE.match(line)
    if timed_match:
        ts = timed_match.group(1)
        text = timed_match.group(2)
    else:
        ts = ""
        text = line

    display_ts = ts or inherited_ts

    speaker_match = SPEAKER_RE.match(text)
    if speaker_match:
        return _dialogue(
            speaker_match.group(1).strip(),
            speaker_match.group(2).strip(),
            ts=display_ts,
        ), ts
    if _is_system_text(text):
        return _system(text, _effect_for_system(text), ts), ts
    return _narration(text, ts=display_ts), ts


def _is_system_text(text: str) -> bool:
    status_fields = (
        "SLEEP",
        "WALLET",
        "SANITY",
        "DEJA_VU",
        "CAFFEINE",
        "USEFUL_HINT",
    )
    return (
        text.startswith(SYSTEM_PREFIXES)
        or text.startswith("KYON.STATUS")
        or text.lstrip().startswith(status_fields)
        or text.startswith("}")
    )


def _effect_for_system(text: str) -> EffectTag:
    if "WORLDLINE" in text:
        return "worldline_shift"
    if "WARNING" in text or "WALLET_DAMAGE" in text:
        return "warning"
    if "ROUTE" in text:
        return "route_trace"
    if "CALL_NOISE" in text:
        return "jitter"
    if "STATUS" in text:
        return "glitch"
    return "typewriter_fast"


def _narration(text: str, effect: EffectTag = "typewriter", ts: str = "") -> LogEntry:
    return LogEntry("narration", None, text, effect, 1.0, timestamp=ts)


def _dialogue(
    speaker: str, text: str, effect: EffectTag = "typewriter", ts: str = ""
) -> LogEntry:
    return LogEntry("dialogue", speaker, text, effect, 1.0, timestamp=ts)


def _system(text: str, effect: EffectTag = "typewriter_fast", ts: str = "") -> LogEntry:
    return LogEntry("system", None, text, effect, 0.6, timestamp=ts)


def _sep() -> LogEntry:
    return LogEntry("fx", None, "", "separator", 1.0)


def _common_commands(*names: str) -> list[Command]:
    labels = {
        "help": "显示帮助",
        "status": "查看当前状态",
        "inventory": "查看背包物品",
        "map": "查看地图",
    }
    return [Command(name, labels[name], name) for name in names]


def _validate_scenario(all_scenes: dict[str, Scene]) -> None:
    allowed_items = KEY_ITEMS | NORMAL_ITEMS
    all_flags = {flag for scene in all_scenes.values() for flag in scene.set_flags}
    # Flags set dynamically by the engine at runtime
    all_flags.add("has_all_key_items")
    invalid_items: list[str] = []
    invalid_required_items: list[str] = []
    missing_required_flags: list[str] = []
    missing_targets: list[str] = []
    duplicate_choice_indexes: list[str] = []
    invalid_auto_next: list[str] = []
    dead_end_scenes: list[str] = []

    for scene in all_scenes.values():
        if scene.auto_next_scene and scene.auto_next_scene not in all_scenes:
            invalid_auto_next.append(f"{scene.id}->{scene.auto_next_scene}")
        for item in scene.grant_items:
            if item not in allowed_items:
                invalid_items.append(f"{scene.id}:{item}")
        seen_indexes: set[int] = set()
        for choice in scene.choices:
            if choice.index in seen_indexes:
                duplicate_choice_indexes.append(f"{scene.id}:{choice.index}")
            seen_indexes.add(choice.index)
            if choice.target_scene not in all_scenes:
                missing_targets.append(f"{scene.id}->{choice.target_scene}")
            if choice.requires_item and choice.requires_item not in allowed_items:
                invalid_required_items.append(f"{scene.id}:{choice.requires_item}")
            if choice.requires_flag and choice.requires_flag not in all_flags:
                missing_required_flags.append(f"{scene.id}:{choice.requires_flag}")
        has_progress_exit = (
            bool(scene.choices)
            or bool(scene.auto_next_scene)
            or scene.triggers_loop_reset
        )
        if not has_progress_exit and not scene.terminal_scene:
            dead_end_scenes.append(scene.id)

    unreachable_scenes = _find_unreachable_scenes(all_scenes)
    errors = {
        "Invalid grant_items outside models constraints": invalid_items,
        "Invalid requires_item outside models constraints": invalid_required_items,
        "Unknown requires_flag references": missing_required_flags,
        "Broken auto_next_scene links": invalid_auto_next,
        "Broken choice target_scene links": missing_targets,
        "Duplicate choice indexes in scene": duplicate_choice_indexes,
        "Dead-end scenes without progression exit": dead_end_scenes,
        "Unreachable scenes from c1a_morning_call": unreachable_scenes,
    }
    for message, values in errors.items():
        if values:
            raise ValueError(message + ": " + ", ".join(values))


def _find_unreachable_scenes(all_scenes: dict[str, Scene]) -> list[str]:
    """BFS reachability including runtime-implicit edges (loop resets, AP finals)."""
    implicit_edges: dict[str, list[str]] = {}
    for sid, sc in all_scenes.items():
        extras: list[str] = []
        if sc.triggers_loop_reset:
            extras.append("c1b_morning_reboot")
            if "c4a_loop_start" in all_scenes:
                extras.append("c4a_loop_start")
        if sid in MAP_HUBS:
            for final_scene in AP_FINAL_TARGETS.values():
                if final_scene in all_scenes:
                    extras.append(final_scene)
            for ap_scene in AP_SCENES_LOOP1 | AP_SCENES_LOOP2:
                if ap_scene in all_scenes:
                    extras.append(ap_scene)
        if extras:
            implicit_edges[sid] = extras

    visited: set[str] = set()
    queue: deque[str] = deque(["c1a_morning_call"])
    while queue:
        current = queue.popleft()
        if current in visited or current not in all_scenes:
            continue
        visited.add(current)
        scene = all_scenes[current]
        if scene.auto_next_scene:
            queue.append(scene.auto_next_scene)
        queue.extend(choice.target_scene for choice in scene.choices)
        if current in implicit_edges:
            queue.extend(implicit_edges[current])
    return sorted(sid for sid in all_scenes if sid not in visited)


def get_command_response(
    cmd: str,
    scene_id: str,
    inventory: set[str],
    loop_count: int,
    flags: dict[str, bool],
) -> list[LogEntry]:
    """Return informational terminal responses. Navigation remains choice-driven."""

    def sys(text: str, effect: EffectTag = "typewriter_fast") -> LogEntry:
        return LogEntry("system", None, text, effect, 0.6)

    def err(text: str) -> LogEntry:
        return LogEntry("error", None, text, "typewriter_fast", 0.6)

    c = cmd.strip().lower()
    if c == "help":
        return [
            sys(">> HELP"),
            sys("  STATUS    - 查看当前精神状态"),
            sys("  INVENTORY - 查看背包物品"),
            sys("  MAP       - 查看地图"),
            sys("  DATE      - 查看世界线信息"),
            sys("  HELP      - 显示此帮助"),
            sys("  SKIP      - 跳过当前场景"),
            sys("  请使用键盘上下或者 Page Up/Down 滚动场景"),
            sys("  剧情移动请使用当前场景的数字选项。"),
        ]
    if c in ("status", "st"):
        deja_vu = "NONE" if loop_count == 0 else "INCREASING"
        return [
            sys(">> STATUS", "cursor_fast"),
            sys("STATUS_CHECK_RUNNING...", "typewriter_slow"),
            sys("KYON.STATUS = {", "instant"),
            sys(f"  LOOP_COUNT: {loop_count},"),
            sys("  WALLET: ENDANGERED,"),
            sys("  SANITY: SUSPICIOUS,"),
            sys(f"  DEJA_VU: {deja_vu},"),
            sys(f"  ITEMS_HELD: {len(inventory)},"),
            sys("}", "instant"),
        ]
    if c in ("inventory", "inv", "i"):
        if not inventory:
            return [sys(">> INVENTORY"), sys("  [空] 背包里什么都没有。")]
        lines = [sys(">> INVENTORY")]
        for item in sorted(inventory):
            item_type = "关键物品" if item in KEY_ITEMS else "普通物品"
            lines.append(sys(f"  [{item_type}] {item}"))
        lines.append(sys(f"  共 {len(inventory)} 件物品。"))
        return lines
    if c == "map":
        return [
            sys(">> MAP"),
            sys("  HOME       - 阿虚的家"),
            sys("  CAFE       - 站前咖啡厅"),
            sys("  STREET     - 商业街"),
            sys("  STORE      - 便利店"),
            sys("  NAGATO_APT - 长门公寓"),
            sys("  ROOFTOP    - 北高天台"),
            sys(
                "  路线提示: 时间与地点决定道具。",
                "glitch" if loop_count > 0 else "typewriter_fast",
            ),
        ]
    if c == "date":
        worldline = WORLDLINE_UNSTABLE if loop_count == 0 else WORLDLINE_STABLE
        return [
            sys(">> DATE"),
            sys("  DATE: 2006-05-02"),
            sys(f"  WORLDLINE: {worldline}"),
            sys(f"  LOOP_COUNT: {loop_count}"),
        ]
    if c == "ls":
        return [sys(" >> LS"), sys("loop.log")]
    if c == "cat":
        return [
            sys(" >> CAT"),
            sys("用法: CAT <文件名>"),
        ]
    if c == "cat loop.log":
        return [
            sys(" >> CAT LOOP.LOG"),
            sys(f"LOOP COUNT: {loop_count + 15498}"),
        ]
    if c == "skip":
        return [
            sys(">> SKIP"),
            sys("  仅在播放文本的过程中跳过当前场景..."),
        ]
    if c.startswith("go "):
        return [
            err(">> GO 命令在此版本中仅作为剧本文档提示。"),
            err("   请使用当前场景的数字选项移动，以便场景校验保持可追踪。"),
        ]
    return [err(f">> 未知指令: '{cmd}'"), err("   输入 HELP 查看可用指令列表。")]
