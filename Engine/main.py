from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Input
from textual import on
from components import StatusBar, StoryLog, InputBar, OptionsConsole
from mikuru import MikuruTypingSurvival
from engine import GameEngine


class NagatoInterface(App[str]):
    CSS = """
    Screen {
        background: #050505;
        layout: vertical;
    }

    #main-layout {
        layout: vertical;
        height: 1fr;
    }

    #log-container {
        height: 70%;
        border: solid #1a4d1a;
        margin: 0 1;
    }

    #console-container {
        height: 30%;
        border: solid #1a4d1a;
        margin: 0 1;
    }

    #inputbar {
        height: auto;
    }
    """

    def __init__(self, initial_scene_id: str | None, **kwargs: Any):
        super().__init__(**kwargs)
        self.initial_scene_id = initial_scene_id
        self.engine = GameEngine()

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")

        with Vertical(id="main-layout"):
            with Container(id="log-container"):
                yield StoryLog(id="story-log", markup=True)
            with Container(id="console-container"):
                yield OptionsConsole(id="options-console")

        yield InputBar(id="inputbar")

    def on_mount(self) -> None:
        self.theme = "ansi-dark"
        self.query_one(InputBar).focus_input()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        """Sync UI with current engine state."""
        scene = self.engine.current_scene()
        status = self.engine.state.status

        # Update status bar
        self.query_one(StatusBar).update_status(
            location=status.location,
            time=status.time,
        )

        # Play story entries
        log = self.query_one(StoryLog)
        for entry in self.engine.state.log:
            log.write(f"{entry.frontmatter} {entry.content}" if entry.frontmatter else entry.content)

        # Render options
        available_choices = [
            c for c in scene.choices
            if self.engine._choice_available(c)
        ]
        self.query_one(OptionsConsole).render_options(
            available_choices, scene.commands, scene.hint
        )

    def process_command(self, raw: str) -> None:
        entries = self.engine.process_input(raw)

        if self.engine.state.game_over:
            self.exit()
            return

        # Display new entries
        log = self.query_one(StoryLog)
        for entry in entries:
            if entry.kind == "player":
                continue
            log.write(f"{entry.frontmatter} {entry.content}" if entry.frontmatter else entry.content)

        # Refresh options for current scene
        scene = self.engine.current_scene()
        status = self.engine.state.status
        self.query_one(StatusBar).update_status(
            location=status.location,
            time=status.time,
        )
        available_choices = [
            c for c in scene.choices
            if self.engine._choice_available(c)
        ]
        self.query_one(OptionsConsole).render_options(
            available_choices, scene.commands, scene.hint
        )

        # Check for mikuru mini-game trigger
        scene_id = self.engine.state.current_scene_id
        if scene_id == "mikuru_game":
            self.exit(scene_id)

    @on(Input.Submitted, "#player-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return

        self.process_command(raw)

        bar = self.query_one(InputBar)
        bar.clear_input()
        bar.focus_input()


if __name__ == "__main__":
    current_scene_id: str | None = None

    while True:
        app = NagatoInterface(current_scene_id)
        current_scene_id = app.run()
        if not current_scene_id:
            break
        mikuru = MikuruTypingSurvival()
        mikuru.run()
