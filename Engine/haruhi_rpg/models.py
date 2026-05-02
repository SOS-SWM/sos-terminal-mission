"""
models.py — Pure data structures. No UI, no I/O.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ─────────────────────────────────────────────
# Entry kinds & visual effects
# ─────────────────────────────────────────────

EntryKind = Literal["narration", "dialogue", "system", "player", "error", "fx"]

# Visual effect tags — ui.py reads these to trigger animations
EffectTag = Literal[
    "typewriter",        # default: char-by-char reveal
    "typewriter_fast",   # faster typewriter
    "typewriter_slow",   # slower, dramatic typewriter
    "instant",           # no animation
    "flicker",           # one-shot terminal flicker before line
    "glitch",            # text corruption effect (mild)
    "glitch_heavy",      # heavy multi-char corruption burst
    "jitter",            # text jitter/shake
    "dim",               # dim screen momentarily
    "route_trace",       # animated ASCII path
    "route_trace_ghost", # route trace with ghost afterimage
    "separator",         # ── horizontal rule
    "worldline_shift",   # dramatic banner
    "reboot",            # full reboot screen wipe
    "success",           # green success flash
    "warning",           # amber warning pulse
    "cursor_fast",       # accelerated cursor blink line
]


@dataclass
class LogEntry:
    timestamp: str            # "HH:MM:SS" or "??"
    kind: EntryKind
    speaker: str | None       # None for narration/system/fx entries
    text: str
    effect: EffectTag = "typewriter"
    speed: float = 1.0        # typewriter speed multiplier (lower = faster)


# ─────────────────────────────────────────────
# Scene building blocks
# ─────────────────────────────────────────────

@dataclass
class Choice:
    index: int
    label: str
    target_scene: str
    requires_flag: str | None = None   # flag key that must be True
    requires_item: str | None = None   # inventory item required
    hidden: bool = False               # only shown if condition met


@dataclass
class Command:
    name: str
    description: str
    hint: str = ""


@dataclass
class Scene:
    id: str
    location: str = ""
    entries: list[LogEntry] = field(default_factory=list)
    auto_entries: list[LogEntry] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    hint: str = ""
    # State mutations on enter
    set_location: str | None = None
    set_time: str | None = None
    set_worldline: str | None = None
    grant_items: list[str] = field(default_factory=list)
    set_flags: dict[str, bool] = field(default_factory=dict)
    triggers_loop_reset: bool = False   # ends loop, goes to reboot


# ─────────────────────────────────────────────
# World / system status
# ─────────────────────────────────────────────

WORLDLINE_STABLE   = "1.048596[α·STABLE]"
WORLDLINE_UNSTABLE = "0xFF-05-02[UNSTABLE]"
WORLDLINE_SHIFTING = "??:??:??[SHIFTING···]"


@dataclass
class SystemStatus:
    worldline: str = WORLDLINE_UNSTABLE
    interface: str = "Nagato_Interface v1.1.4"
    user: str = "root@kyon"
    privilege: str = "/dev/human/sudo"
    location: str = "Home"
    time: str = "08:00:00 JST"
    date: str = "2006-05-02"
    loop_count: int = 0


# ─────────────────────────────────────────────
# Full game state
# ─────────────────────────────────────────────

# Canonical key items required for true ending
KEY_ITEMS = frozenset(["玩偶服", "大红按钮", "超能力飞行装置"])
# Normal items (first loop)
NORMAL_ITEMS = frozenset(["普通的怪兽贴纸", "普通的灯带", "普通的风筝线"])


@dataclass
class GameState:
    status: SystemStatus = field(default_factory=SystemStatus)
    current_scene_id: str = "_ch1a"
    log: list[LogEntry] = field(default_factory=list)
    visited: set[str] = field(default_factory=set)
    flags: dict[str, bool] = field(default_factory=dict)
    inventory: set[str] = field(default_factory=set)
    game_over: bool = False

    # ── Convenience helpers ──────────────────────────────

    def has_item(self, item: str) -> bool:
        return item in self.inventory

    def has_flag(self, flag: str) -> bool:
        return self.flags.get(flag, False)

    def is_first_loop(self) -> bool:
        return self.status.loop_count == 0

    def has_all_key_items(self) -> bool:
        return KEY_ITEMS.issubset(self.inventory)

    def has_all_normal_items(self) -> bool:
        return NORMAL_ITEMS.issubset(self.inventory)

    def loop_count(self) -> int:
        return self.status.loop_count