from typing import Callable, List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.timer import Timer
from textual.widgets import Static, Input, RichLog
from rich.text import Text
from models import LogEntry, Choice, Command, Scene


class StatusBar(Container):
    """三行状态栏，使用容器实现响应式双列布局"""

    DEFAULT_CSS = """
    StatusBar {
        height: auto;
        layout: vertical;
        padding: 0 1;
    }

    StatusBar Horizontal {
        layout: horizontal;
        height: 1;
    }

    StatusBar .status-part {
        width: 1fr;
        content-align: left middle;
    }
    """

    def compose(self) -> ComposeResult:
        for row in range(1, 4):
            with Horizontal(classes="status-row"):
                yield Static(classes="status-part", id=f"status-left-{row}")
                yield Static(classes="status-part", id=f"status-right-{row}")

    def update_status(self) -> None:
        rows = (
            (
                "  ▉ SYSTEM_CORE: Nagato_Interface v1.1.4",
                "▉ WORLDLINE: [bold green]0xFF-05-02[/]",
            ),
            (
                "  ▉ USER_HOST: kyon@SOS",
                "▉ PRIVILEGE: /dev/human/sudo",
            ),
        )

        for row, (left, right) in enumerate(rows, start=1):
            self.query_one(f"#status-left-{row}", Static).update(left)
            self.query_one(f"#status-right-{row}", Static).update(right)


class StoryLog(RichLog):
    """中间层：负责故事流打印（支持逐行输出）"""

    def __init__(self, id: str | None, markup: bool):
        super().__init__(id=id, markup=markup, wrap=True)
        self._play_timer: Timer | None = None
        self._play_index: int = 0
        self._play_entries: List[LogEntry] = []

        # 回调方法
        self._on_tick: Optional[Callable[[LogEntry], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None
        self.on_line_written: Optional[Callable[[str], None]] = None

    def _format_entry(self, entry: LogEntry) -> str:
        """复用原有格式化逻辑，返回单行字符串（含 markup）"""
        if entry.frontmatter:
            # Split timestamp from speaker for separate coloring
            fm = entry.frontmatter
            if fm.startswith("[") and "]" in fm:
                bracket_end = fm.index("]") + 1
                ts_part = fm[:bracket_end]
                rest = fm[bracket_end:].strip()
                if rest:
                    return f"[green]{ts_part}[/] [green]{rest}[/] {entry.content}"
                return f"[green]{ts_part}[/] {entry.content}"
            return f"[yellow]{fm}[/] {entry.content}"
        else:
            return entry.content

    def _stop_timer(self):
        """安全地停止计时器。"""
        if self._play_timer is not None:
            try:
                self._play_timer.stop()
            except Exception:
                pass
            self._play_timer = None

    def _play_log(
        self,
        entries: List[LogEntry],
        line_delay: float = 0.7,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:

        self._stop_timer()  # 停止上一次的播放

        self._play_entries = entries.copy()
        self._play_index = 0
        self._on_complete = on_complete

        if not self._play_entries:
            if self._on_complete:
                self._on_complete()
            return

        def _tick():
            if self._play_index < len(self._play_entries):
                entry = self._play_entries[self._play_index]
                # 忽略玩家自己的输入条目，直接跳过
                if entry.kind == "player":
                    self._play_index += 1
                    _tick()  # 立即进行下一次tick
                    return

                line = self._format_entry(entry)
                self.write(line)
                # 开后门
                if self.on_line_written:
                    self.on_line_written(line)

                if self._on_tick:
                    self._on_tick(entry)

                self._play_index += 1
                asciiLength = sum(1 for ch in entry.text if ord(ch) < 128)
                delay = max(0, len(entry.text) - asciiLength) * 0.05 + line_delay
                self._play_timer = self.set_timer(delay, _tick)
            else:
                self._stop_timer()
                if self._on_complete:
                    self._on_complete()

        _tick()  # 立即触发第一行

    def render_log_entries_immediately(
        self,
        entries: List[LogEntry],
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """立即渲染所有条目（跳过逐行动画）"""
        self._stop_timer()
        for entry in entries:
            line = self._format_entry(entry)
            self.write(line)
            if self.on_line_written:
                self.on_line_written(line)
        if on_complete:
            on_complete()

    def render_scene_log(
        self,
        scene: Scene,
        line_delay: float = 0.7,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        清屏并逐行输出 entries。
        :param entries: 场景条目列表
        :param line_delay: 每行输出间隔（秒）
        """
        # 停止上一次播放（如果有）
        # if self._play_timer is not None:
        #     try:
        #         self._play_timer.pause()
        #     except Exception:
        #         pass
        #     self._play_timer = None

        # 初始化播放队列与索引
        # self._play_entries = scene.entries.copy()
        # self._play_index = 0

        # 清屏并写入场景头
        self.clear()
        timestamp = next((e.timestamp for e in scene.entries if e.timestamp), "UNKNOWN")
        self.write(
            f"[bold cyan]==================== {timestamp} ====================[/]"
        )
        self._play_log(scene.entries, line_delay, on_complete)

    def render_entries_append(
        self,
        entries: List[LogEntry],
        line_delay: float = 0.7,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """在现有日志后追加并逐行输出新条目。"""
        self._play_log(entries, line_delay, on_complete)

    def flush_pending_entries(self):
        """立即输出所有尚未播放的条目，并触发 on_complete 回调。"""
        # 停止计时器
        self._stop_timer()

        # 如果没有剩余条目，直接触发完成回调
        if self._play_index >= len(self._play_entries):
            if self._on_complete:
                self._on_complete()
            return

        # 输出剩余条目
        for i in range(self._play_index, len(self._play_entries)):
            entry = self._play_entries[i]

            # 跳过玩家输入
            if entry.kind == "player":
                continue

            line = self._format_entry(entry)
            self.write(line)

            if self.on_line_written:
                self.on_line_written(line)
            if self._on_tick:
                self._on_tick(entry)

            if "可不只是乌龟啊" in line:
                # self._play_index = i + 1
                # self.set_timer(0.5, self.flush_pending_entries)
                self._play_log(
                    self._play_entries[i+1:],
                    on_complete=self._on_complete
                )
                return

        # 播放结束
        self._play_index = len(self._play_entries)

        if self._on_complete:
            self._on_complete()


class OptionsConsole(Static):
    """选项台：负责安全地渲染交互选项（基于 rich.text.Text 防止标记冲突）"""

    def render_options(
        self, choices: List[Choice], commands: List[Command], hint: str
    ) -> None:
        t = Text()
        # 渲染选项
        for i, choice in enumerate(choices, 1):
            t.append(f"[{str(i)}] ", style="bold green")
            t.append(f"{choice.name}\n", style="default")
        if choices:
            t.append("\n")
        # 渲染指令
        for cmd in commands:
            t.append("> ", style="bold cyan")
            t.append(f"{cmd.name}\n", style="bold cyan")
        if commands:
            t.append("\n")
        # 渲染提示词
        if hint:
            t.append("[HINT] ", style="bold green")
            t.append(f"{hint}\n", style="default")
        self.update(t)


class InputBar(Container):
    """底部输入栏：提示符 + 输入框"""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        background: #0a0a0a;
        border-top: solid #1a4d1a;
        layout: horizontal;
        align: left middle;
        padding: 0 1;
    }

    InputBar Static#prompt {
        width: auto;
        color: #33cc33;
        padding-right: 1;
        content-align: left middle;
    }

    InputBar Input {
        border: none;
        background: transparent;
        color: white;
        width: 1fr;
    }

    InputBar Input:focus {
        border: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("kyon@SOS:~$", id="prompt")
        yield Input(id="player-input")

    def focus_input(self) -> None:
        self.query_one(Input).focus()

    def clear_input(self) -> None:
        inp = self.query_one(Input)
        inp.value = ""
