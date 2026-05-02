from typing import List
from textual.app import ComposeResult
from textual.containers import Container
from textual.timer import Timer
from textual.widgets import Static, Input, RichLog
from rich.text import Text
from models import LogEntry, Choice, Command


class StatusBar(Static):
    """三行 Nagato HUD，左右严格对齐"""

    TARGET_WIDTH = 97  # 你可以根据窗口宽度调整

    def pad_line(self, left: str, right: str) -> str:
        # 计算去除 markup 后的真实长度
        left_len = len(Text.from_markup(left).plain)
        right_len = len(Text.from_markup(right).plain)

        spaces = self.TARGET_WIDTH - left_len - right_len
        if spaces < 1:
            spaces = 1

        return f"{left}{' ' * spaces}{right}"

    def update_status(self, location: str, time: str) -> None:
        # 左右字段
        L1 = "  ▉ SYSTEM_CORE: Nagato_Interface v1.1.4"
        R1 = "▉ WORLDLINE: [bold yellow]0xFF-05-02[/]"

        L2 = "  ▉ USER: root@kyon"
        R2 = "▉ PRIVILEGE: /dev/human/sudo"

        L3 = f"  ▉ LOCATION: [bold green]{location}[/]"
        R3 = f"▉ TIME: {time}"

        # 拼接三行
        content = (
            self.pad_line(L1, R1)
            + "\n"
            + self.pad_line(L2, R2)
            + "\n"
            + self.pad_line(L3, R3)
        )

        self.update(content)


class StoryLog(RichLog):
    """中间层：负责故事流打印（支持逐行输出）"""

    def __init__(self, id: str | None, markup: bool):
        super().__init__(id=id, markup=markup)
        self._play_timer: Timer | None = None
        self._play_index: int = 0
        self._play_entries: List[LogEntry] = []

    def _format_entry(self, entry: LogEntry) -> str:
        """复用原有格式化逻辑，返回单行字符串（含 markup）"""
        if "CALL_" in entry.content or "WARNING" in entry.content:
            return entry.frontmatter + entry.content
        else:
            parts = entry.frontmatter.split("]", 1)
            if len(parts) == 2:
                time_stamp = f"{parts[0]}]"
                speaker = parts[1]
                return (
                    f"[green]{time_stamp}[/] [bold yellow]{speaker}[/] {entry.content}"
                )
            else:
                return f"{entry.frontmatter} {entry.content}"

    def render_scene_log(
        self, entries: List[LogEntry], line_delay: float = 0.7
    ) -> None:
        """
        清屏并逐行输出 entries。
        :param entries: 场景条目列表
        :param line_delay: 每行输出间隔（秒）
        """
        # 停止上一次播放（如果有）
        if self._play_timer is not None:
            try:
                self._play_timer.pause()
            except Exception:
                pass
            self._play_timer = None

        # 初始化播放队列与索引
        self._play_entries = entries.copy()
        self._play_index = 0

        # 清屏并写入场景头
        self.clear()
        self.write(
            "\n[bold black]==================== SCENE INITIALIZED ====================[/]"
        )

        # 如果没有条目，直接返回
        if not self._play_entries:
            return

        # 定时器回调：逐条写入并在结束时停止定时器
        def _tick():
            if self._play_index < len(self._play_entries):
                entry = self._play_entries[self._play_index]
                line = self._format_entry(entry)
                self.write(line)
                self._play_index += 1
            else:
                # 播放完毕，停止定时器
                if self._play_timer is not None:
                    try:
                        self._play_timer.pause()
                    except Exception:
                        pass
                    self._play_timer = None

        # 创建并启动定时器（立即触发第一行）
        self._play_timer = self.set_interval(line_delay, _tick)
        _tick()


class OptionsConsole(Static):
    """选项台：负责安全地渲染交互选项（基于 rich.text.Text 防止标记冲突）"""

    def render_options(
        self, choices: List[Choice], commands: List[Command], hint: str
    ) -> None:
        t = Text()
        # 渲染选项
        for i, choice in enumerate(choices, 1):
            t.append("[", style="bold green")
            t.append(str(i), style="bold yellow")
            t.append("] ", style="bold green")
            t.append(f"{choice.name}\n", style="default")
        t.append("\n")
        # 渲染指令
        for cmd in commands:
            t.append("> ", style="bold cyan")
            t.append(f"{cmd.name}\n", style="bold cyan")
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
        yield Static("INPUT: root@kyon:~#", id="prompt")
        yield Input(placeholder="输入指令或选项编号...", id="player-input")

    def focus_input(self) -> None:
        self.query_one(Input).focus()

    def clear_input(self) -> None:
        inp = self.query_one(Input)
        inp.value = ""
