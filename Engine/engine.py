"""
engine.py — Game logic layer. No UI dependencies.
Receives player input → returns updated GameState + new log entries.
"""
from __future__ import annotations
from models import (
    GameState,
    LogEntry,
    Scene,
    SystemStatus,
    WORLDLINE_UNSTABLE,
    NORMAL_ITEMS,
)
from scene import (
    INHERIT_TIMESTAMP,
    LOOP1_TIME_SLOTS,
    LOOP2_TIME_SLOTS,
    LOOP2_ROUTING,
    AP_SCENES_LOOP1,
    AP_SCENES_LOOP2,
    MAP_HUBS,
    AP_INIT_SCENES,
    AP_FINAL_TARGETS,
    build_scenario,
    get_command_response,
)


class GameEngine:
    def __init__(self) -> None:
        self.scenes: dict[str, Scene] = build_scenario()
        self.state = GameState()
        self.state.log.extend(self._enter_scene("c1a_morning_call"))

    # ── Public API ──────────────────────────────────────────────────────────

    def current_scene(self) -> Scene:
        return self.scenes[self.state.current_scene_id]

    def process_input(self, raw: str) -> list[LogEntry]:
        text = raw.strip()
        if not text:
            return []

        player_entry = LogEntry(
            timestamp=self.state.status.time,
            kind="player",
            speaker="kyon",
            text=text,
        )
        new_entries: list[LogEntry] = [player_entry]

        if text.isdigit():
            entries = self._handle_choice(int(text))
        else:
            entries = self._handle_command(text)

        new_entries.extend(entries)
        self.state.log.extend(new_entries)
        return new_entries

    # ── Internal helpers ────────────────────────────────────────────────────

    def _handle_choice(self, index: int) -> list[LogEntry]:
        scene = self.current_scene()
        for choice in scene.choices:
            if choice.index == index and self._choice_available(choice):
                target = choice.target_scene
                if self._is_ap_target(target):
                    return self._handle_ap_entry(target)
                return self._enter_scene(target)
        return [LogEntry(
            timestamp=self.state.status.time,
            kind="error",
            speaker=None,
            text=f">> 选项 [{index}] 在当前场景不可用",
        )]

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
        if choice.requires_flag and not self.state.flags.get(choice.requires_flag, False):
            return False
        if choice.requires_item and choice.requires_item not in self.state.inventory:
            return False
        if choice.hidden:
            return False
        return True

    # ── Action Point system ────────────────────────────────────────────────

    def _is_ap_target(self, scene_id: str) -> bool:
        return scene_id in AP_SCENES_LOOP1 or scene_id in AP_SCENES_LOOP2

    def _current_time_slots(self) -> list[str]:
        if self.state.action_points_max == 7:
            return LOOP2_TIME_SLOTS
        return LOOP1_TIME_SLOTS

    def _current_ap_scenes(self) -> set[str]:
        if self.state.action_points_max == 7:
            return AP_SCENES_LOOP2
        return AP_SCENES_LOOP1

    def _handle_ap_entry(self, target: str) -> list[LogEntry]:
        ts = self.state.status.time
        is_loop1 = self.state.action_points_max == 4

        # Smart routing: resolve unified target to first-visit or revisit
        resolved = self._resolve_loop2_target(target) if not is_loop1 else target

        if resolved in self.state.visited_actions:
            if is_loop1:
                return [LogEntry(ts, "dialogue", "Kyon",
                    "那个地方已经去过了，没什么好看的了。",
                    "typewriter", 1.0)]
            else:
                self._consume_ap()
                # Check if this is a "first-visit done but can't upgrade" situation
                route = LOOP2_ROUTING.get(target)
                if route and target in self.state.visited_actions and not route["revisit_requires"].issubset(self.state.inventory):
                    msg = "总觉得还缺点什么……白跑了一趟。"
                else:
                    msg = "又来了一次，但什么也没发生。浪费了宝贵的时间。"
                entries = [LogEntry(ts, "dialogue", "Kyon", msg, "typewriter", 1.0)]
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
        if first_visit_id in self.state.visited_actions and revisit_requires.issubset(self.state.inventory):
            return revisit_id
        return first_visit_id

    def _consume_ap(self) -> None:
        if self.state.action_points_remaining > 0:
            slots = self._current_time_slots()
            idx = self.state.current_time_slot_index
            if idx < len(slots):
                self.state.status.time = slots[idx]
            self.state.current_time_slot_index += 1
            self.state.action_points_remaining -= 1

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
                self.state.current_time_slot_index = 0
                self.state.visited_actions.clear()

    def _time_to_seconds(self, raw_time: str | None) -> int | None:
        if not raw_time:
            return None
        token = raw_time.split()[0]
        parts = token.split(":")
        if len(parts) != 3:
            return None
        try:
            hours, minutes, seconds = (int(part) for part in parts)
        except ValueError:
            return None
        return hours * 3600 + minutes * 60 + seconds

    def _advance_time(self, incoming_time: str, allow_reset: bool = False) -> None:
        current_seconds = self._time_to_seconds(self.state.status.time)
        incoming_seconds = self._time_to_seconds(incoming_time)
        if incoming_seconds is None:
            return
        if allow_reset or current_seconds is None or incoming_seconds >= current_seconds:
            self.state.status.time = incoming_time

    def _enter_scene(self, scene_id: str) -> list[LogEntry]:
        if scene_id not in self.scenes:
            return [LogEntry(
                timestamp=self.state.status.time,
                kind="error",
                speaker=None,
                text=f">> ERROR: 场景 '{scene_id}' 不存在",
            )]
        self.state.current_scene_id = scene_id
        self.state.visited.add(scene_id)
        self._init_ap_for_scene(scene_id)
        scene = self.scenes[scene_id]
        self._apply_scene_side_effects(scene)
        entries = self._resolve_inherited_timestamps(
            list(scene.entries) + list(scene.auto_entries)
        )

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
                entries.extend(self._enter_scene(next_scene))

        auto_next_scene = scene.auto_next_scene
        if auto_next_scene and auto_next_scene in self.scenes:
            entries.extend(self._enter_scene(auto_next_scene))
        return entries

    def _resolve_inherited_timestamps(self, entries: list[LogEntry]) -> list[LogEntry]:
        floor_time = self._status_time_hms()
        inherited_timestamp = floor_time
        resolved_entries: list[LogEntry] = []
        for entry in entries:
            if entry.kind == "fx" and not entry.timestamp:
                resolved_entries.append(entry)
                continue
            if entry.timestamp == INHERIT_TIMESTAMP:
                ts = inherited_timestamp
            elif entry.timestamp:
                ts_seconds = self._time_to_seconds(entry.timestamp)
                floor_seconds = self._time_to_seconds(floor_time)
                if ts_seconds is not None and floor_seconds is not None and ts_seconds < floor_seconds:
                    ts = floor_time
                else:
                    ts = entry.timestamp
                    if ts_seconds is not None and (floor_seconds is None or ts_seconds > floor_seconds):
                        floor_time = entry.timestamp
            else:
                ts = inherited_timestamp
            resolved_entries.append(LogEntry(
                timestamp=ts,
                kind=entry.kind,
                speaker=entry.speaker,
                text=entry.text,
                effect=entry.effect,
                speed=entry.speed,
            ))
            if ts:
                inherited_timestamp = ts
        return resolved_entries

    def _status_time_hms(self) -> str:
        raw = self.state.status.time
        if not raw:
            return "00:00:00"
        return raw.split()[0] if " " in raw else raw

    def _apply_scene_side_effects(self, scene: Scene) -> None:
        if scene.set_location is not None:
            self.state.status.location = scene.set_location
        if scene.set_time is not None:
            self._advance_time(scene.set_time, scene.allow_time_reset)
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
            self.state.current_time_slot_index = 0
            self.state.visited_actions.clear()
