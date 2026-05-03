"""
engine.py — Game logic layer. No UI dependencies.
Receives player input → returns updated GameState + new log entries.
"""

from __future__ import annotations
import random
from models import (
    GameState,
    LogEntry,
    Scene,
    WORLDLINE_UNSTABLE,
    NORMAL_ITEMS,
)
from scene import (
    LOOP2_ROUTING,
    AP_SCENES_LOOP1,
    AP_SCENES_LOOP2,
    MAP_HUBS,
    AP_INIT_SCENES,
    AP_FINAL_TARGETS,
    CH3_TIME_SLOTS_LOOP1,
    CH3_TIME_SLOTS_LOOP2,
    build_scenario,
    get_command_response,
)


class GameEngine:
    def __init__(self, initialize_scene: str | None) -> None:
        self.scenes: dict[str, Scene] = build_scenario()
        self.state = GameState()
        first_scene = (
            "c1a_morning_call" if initialize_scene is None else initialize_scene
        )
        self.state.log.extend(self._enter_scene(first_scene))

    # ── Public API ──────────────────────────────────────────────────────────

    def current_scene(self) -> Scene:
        return self.scenes[self.state.current_scene_id]

    def process_input(self, raw: str) -> tuple[list[LogEntry], bool]:
        """
        returns: (new log entries, whether the input was recognized as a valid choice or command)
        """
        text = raw.strip()
        if not text:
            return [], False

        player_entry = LogEntry(
            kind="player",
            speaker="kyon",
            text=text,
        )
        new_entries: list[LogEntry] = [player_entry]

        isCommand = not text.isdigit()

        if isCommand:
            entries = self._handle_command(text)
        else:
            entries = self._handle_choice(int(text))

        new_entries.extend(entries)
        self.state.log.extend(new_entries)

        return new_entries, isCommand

    # ── Internal helpers ────────────────────────────────────────────────────

    def _handle_choice(self, index: int) -> list[LogEntry]:
        scene = self.current_scene()
        for choice in scene.choices:
            if choice.index == index and self._choice_available(choice):
                target = choice.target_scene
                if self._is_ap_target(target):
                    return self._handle_ap_entry(target)
                return self._enter_scene(target)
        return [
            LogEntry(
                kind="error",
                speaker=None,
                text=f">> 选项 [{index}] 在当前场景不可用",
            )
        ]

    def _handle_command(self, text: str) -> list[LogEntry]:
        scene_id = self.state.current_scene_id
        return get_command_response(
            text,
            scene_id,
            self.state.inventory,
            self.state.status.loop_count,
            self.state.flags,
        )

    def _choice_available(self, choice) -> bool:
        if choice.requires_flag and not self.state.flags.get(
            choice.requires_flag, False
        ):
            return False
        if choice.requires_item and choice.requires_item not in self.state.inventory:
            return False
        if choice.hidden:
            return False
        return True

    # ── Action Point system ────────────────────────────────────────────────

    def _is_ap_target(self, scene_id: str) -> bool:
        return scene_id in AP_SCENES_LOOP1 or scene_id in AP_SCENES_LOOP2

    def _current_ap_scenes(self) -> set[str]:
        if self.state.action_points_max == 7:
            return AP_SCENES_LOOP2
        return AP_SCENES_LOOP1

    def _handle_ap_entry(self, target: str) -> list[LogEntry]:
        is_loop1 = self.state.action_points_max == 4

        # Smart routing: resolve unified target to first-visit or revisit
        resolved = self._resolve_loop2_target(target) if not is_loop1 else target

        if resolved in self.state.visited_actions:
            if is_loop1:
                return [
                    LogEntry(
                        "dialogue",
                        "Kyon",
                        "那个地方已经去过了，没什么好看的了。",
                        "typewriter",
                        1.0,
                    )
                ]
            else:
                self._consume_ap()
                # Check if this is a "first-visit done but can't upgrade" situation
                route = LOOP2_ROUTING.get(target)
                if (
                    route
                    and target in self.state.visited_actions
                    and not route["revisit_requires"].issubset(self.state.inventory)
                ):
                    msg = "总觉得还缺点什么……白跑了一趟。"
                else:
                    msg = "又来了一次，但什么也没发生。浪费了宝贵的时间。"
                entries = [LogEntry("dialogue", "Kyon", msg, "typewriter", 1.0)]
                entries.extend(self._check_ap_exhausted())
                return entries

        self._consume_ap()
        self.state.visited_actions.add(resolved)
        entries = self._enter_scene(resolved)
        # Don't check AP exhaustion here — let the player finish the scene.
        # AP exhaustion is checked when returning to a map hub.
        return entries

    def _resolve_loop2_target(self, target: str) -> str:
        route = LOOP2_ROUTING.get(target)
        if route is None:
            return target
        first_visit_id = target
        revisit_id = route["revisit_scene"]
        revisit_requires = route["revisit_requires"]
        # If first visit already done and player holds required items -> revisit
        if first_visit_id in self.state.visited_actions and revisit_requires.issubset(
            self.state.inventory
        ):
            return revisit_id
        return first_visit_id

    def _consume_ap(self) -> None:
        if self.state.action_points_remaining > 0:
            self.state.action_points_remaining -= 1

    def _inject_ch3_timestamps(self, entries: list[LogEntry]) -> None:
        """Inject display-only timestamps into Chapter 3 entries."""
        is_loop1 = self.state.action_points_max == 4
        slots = CH3_TIME_SLOTS_LOOP1 if is_loop1 else CH3_TIME_SLOTS_LOOP2
        # AP slot index = how many AP consumed so far
        consumed = self.state.action_points_max - self.state.action_points_remaining
        # Clamp to valid range (consume happens before enter_scene)
        idx = max(0, min(consumed - 1, len(slots) - 1))
        base = slots[idx]
        h, m = (int(x) for x in base.split(":"))
        s = 0
        for entry in entries:
            if entry.kind == "fx":
                continue
            entry.timestamp = f"{h:02d}:{m:02d}:{s:02d}"
            # Increment: sometimes +1 min, always random seconds
            s = random.randint(0, 59)
            if random.random() < 0.4:
                m += 1
                if m >= 60:
                    m = 0
                    h += 1

    def _check_ap_exhausted(self) -> list[LogEntry]:
        if self.state.action_points_remaining <= 0:
            final = AP_FINAL_TARGETS.get(self.state.action_points_max)
            if final and final in self.scenes:
                hub = self.state.current_scene_id
                if hub in MAP_HUBS or hub.startswith("c3"):
                    return self._enter_scene(final)
        return []

    def _init_ap_for_scene(self, scene_id: str) -> None:
        if scene_id in AP_INIT_SCENES:
            ap = AP_INIT_SCENES[scene_id]
            if self.state.action_points_max == 0:
                self.state.action_points_max = ap
                self.state.action_points_remaining = ap
                self.state.visited_actions.clear()

    def _enter_scene(self, scene_id: str) -> list[LogEntry]:
        if scene_id not in self.scenes:
            return [
                LogEntry(
                    kind="error",
                    speaker=None,
                    text=f">> ERROR: 场景 '{scene_id}' 不存在",
                )
            ]
        self.state.current_scene_id = scene_id
        self.state.visited.add(scene_id)
        self._init_ap_for_scene(scene_id)
        scene = self.scenes[scene_id]
        self._apply_scene_side_effects(scene)
        entries = list(scene.entries) + list(scene.auto_entries)

        # Inject display timestamps for Chapter 3 scenes (no game logic)
        if scene_id.startswith("c3"):
            self._inject_ch3_timestamps(entries)

        # When returning to a map hub, check if AP is exhausted
        if scene_id in MAP_HUBS:
            exhausted = self._check_ap_exhausted()
            if exhausted:
                entries.extend(exhausted)
                return entries

        # Loop reset scenes should immediately route into reboot flow.
        if scene.triggers_loop_reset:
            next_scene = "c1b_morning_reboot"
            if scene_id != "c4a_loop_start" and "c4a_loop_start" in self.scenes:
                next_scene = "c4a_loop_start"
            if next_scene in self.scenes and next_scene != scene_id:
                # entries.extend(self._enter_scene(next_scene))
                self.state.pending_scene = next_scene

        auto_next_scene = scene.auto_next_scene
        if auto_next_scene and auto_next_scene in self.scenes:
            entries.extend(self._enter_scene(auto_next_scene))
        return entries

    def _apply_scene_side_effects(self, scene: Scene) -> None:
        if scene.set_location is not None:
            self.state.status.location = scene.set_location
        if scene.set_worldline is not None:
            self.state.status.worldline = scene.set_worldline
        if scene.grant_items:
            self.state.inventory.update(scene.grant_items)
        if scene.consume_items:
            self.state.inventory.difference_update(scene.consume_items)
        if scene.set_flags:
            self.state.flags.update(scene.set_flags)

        # Derive flag for true ending gate
        if scene.id == "c4b_final":
            self.state.flags["has_all_key_items"] = self.state.has_all_key_items()

        # 添加结局
        if scene.id == "c4b_true_end":
            self.state.game_over = True

        if scene.triggers_loop_reset:
            # Transitional loop scene should not count as an extra full loop.
            if scene.id != "c4a_loop_start":
                self.state.status.loop_count += 1
            # Regular props reset after each failed run.
            self.state.inventory.difference_update(NORMAL_ITEMS)
            self.state.flags.clear()
            if scene.set_worldline is None:
                self.state.status.worldline = WORLDLINE_UNSTABLE
            # Reset AP state for next loop
            self.state.action_points_remaining = 0
            self.state.action_points_max = 0
            self.state.visited_actions.clear()
