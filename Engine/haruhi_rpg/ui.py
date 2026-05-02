"""
ui.py — Textual TUI widgets. Purely presentational; talks to GameEngine.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import (
    Static, Input, RichLog, Footer
)
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual import on
from textual.binding import Binding
from rich.text import Text
from rich.style import Style

from haruhi_rpg.models import LogEntry, Scene, SystemStatus
from haruhi_rpg.engine import GameEngine


# ─────────────────────────────────────────────────────────────────────────────
# Color / style palette  (terminal-hacker green on black)
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "bg":           "#0a0e0a",
    "green":        "#00ff41",
    "green_dim":    "#00aa2a",
    "green_muted":  "#006618",
    "amber":        "#ffb000",
    "amber_dim":    "#a07000",
    "cyan":         "#00e5ff",
    "cyan_dim":     "#007a8a",
    "red":          "#ff3333",
    "white":        "#e8e8e8",
    "grey":         "#555555",
    "player":       "#7dff8a",
    "border":       "#1a3a1a",
}

# Rich markup colour shortcuts
C = {k: f"[{v}]" for k, v in PALETTE.items()}
_R = {k: f"[/{v}]" for k, v in PALETTE.items()}   # unused but handy


def _entry_to_rich(entry: LogEntry) -> Text:
    """Convert a LogEntry to a Rich Text object with styling."""
    ts_style   = Style(color=PALETTE["green_dim"])
    sys_style  = Style(color=PALETTE["cyan_dim"])
    narr_style = Style(color=PALETTE["white"])
    dlg_style  = Style(color=PALETTE["green"])
    spk_style  = Style(color=PALETTE["amber"], bold=True)
    plr_style  = Style(color=PALETTE["player"], italic=True)
    err_style  = Style(color=PALETTE["red"])

    t = Text()

    if entry.kind == "system":
        t.append(f"  {entry.text}", style=sys_style)
    elif entry.kind == "narration":
        t.append(f"[{entry.timestamp}] ", style=ts_style)
        t.append(entry.text, style=narr_style)
    elif entry.kind == "dialogue":
        t.append(f"[{entry.timestamp}] ", style=ts_style)
        t.append(f"{entry.speaker}", style=spk_style)
        t.append(" > ", style=Style(color=PALETTE["green_dim"]))
        t.append(entry.text, style=dlg_style)
    elif entry.kind == "player":
        t.append(f"  INPUT > ", style=Style(color=PALETTE["green_muted"]))
        t.append(entry.text, style=plr_style)
    elif entry.kind == "error":
        t.append(f"  {entry.text}", style=err_style)
    else:
        t.append(f"[{entry.timestamp}] {entry.text}")

    return t


# ─────────────────────────────────────────────────────────────────────────────
# Widget: StatusBar  (top strip)
# ─────────────────────────────────────────────────────────────────────────────

class StatusBar(Static):
    """Top system-status bar, single line."""

    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        background: #0d1a0d;
        border-bottom: solid #1a3a1a;
        padding: 0 1;
        color: #00aa2a;
    }
    """

    status: reactive[SystemStatus] = reactive(SystemStatus, layout=True)

    def render(self) -> Text:
        s = self.status
        sep = Text("  ▉  ", style=Style(color=PALETTE["green_muted"]))
        t = Text()
        t.append("▉ ", style=Style(color=PALETTE["green"], bold=True))
        t.append("SYSTEM: ", style=Style(color=PALETTE["green_dim"]))
        t.append(s.interface, style=Style(color=PALETTE["cyan"], bold=True))
        t.append_text(sep)
        t.append("WORLDLINE: ", style=Style(color=PALETTE["green_dim"]))
        t.append(s.worldline, style=Style(color=PALETTE["amber"]))
        t.append_text(sep)
        t.append("USER: ", style=Style(color=PALETTE["green_dim"]))
        t.append(s.user, style=Style(color=PALETTE["green"]))
        t.append_text(sep)
        t.append("LOCATION: ", style=Style(color=PALETTE["green_dim"]))
        t.append(s.location, style=Style(color=PALETTE["cyan"]))
        t.append_text(sep)
        t.append("TIME: ", style=Style(color=PALETTE["green_dim"]))
        t.append(s.time, style=Style(color=PALETTE["white"]))
        return t


# ─────────────────────────────────────────────────────────────────────────────
# Widget: NarrativeLog  (centre scrollable story pane)
# ─────────────────────────────────────────────────────────────────────────────

class NarrativeLog(RichLog):
    """Scrollable story/log pane."""

    DEFAULT_CSS = """
    NarrativeLog {
        background: #0a0e0a;
        border: solid #1a3a1a;
        padding: 0 2;
        scrollbar-color: #1a3a1a #0a0e0a;
        scrollbar-size: 1 1;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "LOG_STDOUT"
        self.border_title_style = Style(color=PALETTE["green_dim"])

    def push_entry(self, entry: LogEntry) -> None:
        self.write(_entry_to_rich(entry))

    def push_separator(self) -> None:
        self.write(Text("─" * 60, style=Style(color=PALETTE["green_muted"])))


# ─────────────────────────────────────────────────────────────────────────────
# Widget: OptionsPane  (bottom-left: choices + commands)
# ─────────────────────────────────────────────────────────────────────────────

class OptionsPane(Static):
    """Displays interactive choices and available commands."""

    DEFAULT_CSS = """
    OptionsPane {
        height: 12;
        background: #0a0f0a;
        border: solid #1a3a1a;
        padding: 0 1;
        overflow-y: auto;
        color: #00aa2a;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "INTERACTIVE_CONSOLE | CONTEXT_OPTIONS"

    def update_scene(self, scene: Scene) -> None:
        lines: list[Text] = []

        if scene.choices:
            for ch in scene.choices:
                t = Text()
                t.append(f"[{ch.index}]", style=Style(color=PALETTE["amber"], bold=True))
                t.append(f" {ch.label}", style=Style(color=PALETTE["white"]))
                lines.append(t)

        if scene.commands:
            if scene.choices:
                lines.append(Text(""))
            for cmd in scene.commands:
                t = Text()
                t.append(f"> {cmd.name}", style=Style(color=PALETTE["cyan"], bold=True))
                t.append(f"  — {cmd.description}", style=Style(color=PALETTE["grey"]))
                lines.append(t)

        if scene.hint:
            lines.append(Text(""))
            hint_t = Text()
            hint_t.append(scene.hint, style=Style(color=PALETTE["green_dim"], italic=True))
            lines.append(hint_t)

        # Render all as one markup block
        content = Text("\n").join(lines) if lines else Text(
            "  [等待输入...]", style=Style(color=PALETTE["green_muted"])
        )
        self.update(content)


# ─────────────────────────────────────────────────────────────────────────────
# Widget: InputBar  (bottom prompt)
# ─────────────────────────────────────────────────────────────────────────────

class InputBar(Container):
    """The player input prompt row."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        background: #0a0e0a;
        border-top: solid #1a3a1a;
        layout: horizontal;
        align: left middle;
    }
    InputBar Static#prompt {
        width: auto;
        color: #00ff41;
        padding: 0 1;
        content-align: left middle;
    }
    InputBar Input {
        border: none;
        background: #0a0e0a;
        color: #7dff8a;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("INPUT: root@sos-brigade/kyon:~#", id="prompt")
        yield Input(placeholder="输入指令或选项编号...", id="player-input")

    def focus_input(self) -> None:
        self.query_one(Input).focus()

    def clear_input(self) -> None:
        inp = self.query_one(Input)
        inp.value = ""


# ─────────────────────────────────────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────────────────────────────────────

class HaruhiApp(App):
    """SOS Brigade Terminal RPG — Main Application."""

    TITLE = "SOS Brigade Terminal v1.0"
    CSS = """
    Screen {
        background: #0a0e0a;
        layout: vertical;
    }
    #main-area {
        layout: vertical;
        height: 1fr;
    }
    #bottom-area {
        layout: vertical;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "退出", show=True),
        Binding("ctrl+r", "restart", "重新开始", show=True),
        Binding("escape", "focus_input", "输入框", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.engine = GameEngine()

    def compose(self) -> ComposeResult:
        yield StatusBar(id="statusbar")
        with Container(id="main-area"):
            yield NarrativeLog(id="log", highlight=False, markup=False)
        with Container(id="bottom-area"):
            yield OptionsPane(id="options")
            yield InputBar(id="inputbar")

    def on_mount(self) -> None:
        # Push initial scene log
        log_widget = self.query_one(NarrativeLog)
        for entry in self.engine.state.log:
            log_widget.push_entry(entry)

        # Update status bar
        self._sync_status()

        # Update options
        self._sync_options()

        # Focus input
        self.query_one(InputBar).focus_input()

    @on(Input.Submitted, "#player-input")
    def handle_input(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return

        log_widget = self.query_one(NarrativeLog)
        log_widget.push_separator()

        new_entries = self.engine.process_input(raw)
        for entry in new_entries:
            log_widget.push_entry(entry)

        self._sync_status()
        self._sync_options()
        self.query_one(InputBar).clear_input()
        self.query_one(InputBar).focus_input()

    def action_restart(self) -> None:
        self.engine = GameEngine()
        log_widget = self.query_one(NarrativeLog)
        log_widget.clear()
        log_widget.write(Text(">> SYSTEM REBOOT — 世界线重置", style=Style(color=PALETTE["amber"])))
        for entry in self.engine.state.log:
            log_widget.push_entry(entry)
        self._sync_status()
        self._sync_options()
        self.query_one(InputBar).focus_input()

    def action_focus_input(self) -> None:
        self.query_one(InputBar).focus_input()

    def _sync_status(self) -> None:
        bar = self.query_one(StatusBar)
        bar.status = self.engine.state.status
        bar.refresh()

    def _sync_options(self) -> None:
        opts = self.query_one(OptionsPane)
        opts.update_scene(self.engine.current_scene())
