from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.containers import Vertical
from textual.reactive import reactive

from models import Scene, LogEntry, Choice, Command
from engine import GameEngine


# ───────────────────────────────────────────────
# 顶栏：简单、左右对齐、无复杂样式
# ───────────────────────────────────────────────

class StatusBar(Static):
    scene: reactive[Scene] = reactive(None)

    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        background: #000000;
        color: #00ff41;
        padding: 0 1;
        border-bottom: solid #005500;
        content-align: left middle;
        font-family: monospace;
    }
    """

    def render(self):
        s = self.scene
        if not s:
            return ""

        return (
            f"▉ SYSTEM: Nagato_Interface v1.1.4"
            f"    ▉ WORLDLINE: 0xFF-05-02[UNSTABLE]\n"
            f"▉ USER: root@kyon"
            f"                 ▉ LOCATION: {s.location}\n"
            f"▉ TIME: 17:05:00 JST"
        )


# ───────────────────────────────────────────────
# 中间日志区：纯文本，无 RichLog
# ───────────────────────────────────────────────

class LogPanel(Static):
    scene: reactive[Scene] = reactive(None)

    DEFAULT_CSS = """
    LogPanel {
        height: 1fr;
        background: #000000;
        color: #00ff41;
        padding: 1 2;
        border: solid #005500;
        overflow-y: auto;
        font-family: monospace;
    }
    """

    def render(self):
        if not self.scene:
            return ""

        lines = ["[ ▲ ]", ""]

        for e in self.scene.entries:
            lines.append(f"{e.frontmatter} {e.content}")
            lines.append("")

        lines.append("[ ▼ ]")
        return "\n".join(lines)


# ───────────────────────────────────────────────
# 底栏：选项 + 指令 + 输入框
# ───────────────────────────────────────────────

class Console(Static):
    scene: reactive[Scene] = reactive(None)

    DEFAULT_CSS = """
    Console {
        height: 10;
        background: #000000;
        color: #00ff41;
        padding: 1 2;
        border: solid #005500;
        font-family: monospace;
    }
    Console Input {
        background: #000000;
        color: #00ff41;
        border: none;
    }
    """

    def compose(self) -> ComposeResult:
        self.options = Static()
        self.input = Input(placeholder="root@sos-brigade/kyon:~# ")
        yield self.options
        yield self.input

    def render_options(self):
        s = self.scene
        if not s:
            return ""

        lines = ["[ INTERACTIVE_CONSOLE | CONTEXT_OPTIONS ]"]

        for i, c in enumerate(s.choices, start=1):
            lines.append(f"  [{i}] {c.name}")

        for cmd in s.commands:
            lines.append(f"  > {cmd.name}")

        lines.append(f"[HINT] {s.hint}")
        return "\n".join(lines)

    def watch_scene(self, scene):
        self.options.update(self.render_options())


# ───────────────────────────────────────────────
# 主应用：只负责 Scene 切换
# ───────────────────────────────────────────────

class GameUI(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #000000;
    }
    """

    def __init__(self):
        super().__init__()
        self.engine = GameEngine()

    def compose(self) -> ComposeResult:
        self.status = StatusBar()
        self.log = LogPanel()
        self.console = Console()
        yield self.status
        yield self.log
        yield self.console

    def on_mount(self):
        self.load_scene(self.engine.current_scene())

    def load_scene(self, scene: Scene):
        self.status.scene = scene
        self.log.scene = scene
        self.console.scene = scene
        self.console.input.focus()

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        event.input.value = ""

        next_scene = self.engine.process_input(text)
        if next_scene:
            self.load_scene(next_scene)
