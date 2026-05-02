"""
engine.py — Game logic layer. No UI dependencies.
Receives player input → returns updated GameState + new log entries.
"""
from __future__ import annotations
from haruhi_rpg.models import GameState, LogEntry, Scene, SystemStatus
from haruhi_rpg.scenario import build_scenario, get_command_response


class GameEngine:
    def __init__(self) -> None:
        self.scenes: dict[str, Scene] = build_scenario()
        self.state = GameState()
        # Load intro scene entries into log
        self._enter_scene("c1a_morning_call")

    # ── Public API ──────────────────────────────────────────────────────────

    def current_scene(self) -> Scene:
        return self.scenes[self.state.current_scene_id]

    def process_input(self, raw: str) -> list[LogEntry]:
        """Parse player input and return new log entries produced."""
        text = raw.strip()
        if not text:
            return []

        # Echo player input as a log entry
        player_entry = LogEntry(
            timestamp=self.state.status.time,
            kind="player",
            speaker="kyon",
            text=text,
        )
        new_entries: list[LogEntry] = [player_entry]

        # Check numeric choice
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
            if choice.index == index:
                return self._enter_scene(choice.target_scene)
        return [LogEntry(
            timestamp=self.state.status.time,
            kind="error",
            speaker=None,
            text=f">> 选项 [{index}] 在当前场景不可用",
        )]

    def _handle_command(self, text: str) -> list[LogEntry]:
        cmd_parts = text.lower().split()
        cmd_name = cmd_parts[0] if cmd_parts else ""
        scene_id = self.state.current_scene_id
        return get_command_response(cmd_name, scene_id)

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
        scene = self.scenes[scene_id]
        entries = list(scene.entries) + list(scene.auto_entries)
        self.state.log.extend(entries)
        return entries
