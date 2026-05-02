from textual.widgets import Static
from textual.timer import Timer

class Typewriter(Static):
    def __init__(self, text: str, speed: float = 0.01):
        super().__init__("")
        self.full_text = text
        self.speed = speed
        self.index = 0
        self.timer: Timer | None = None

    def on_mount(self):
        self.timer = self.set_interval(self.speed, self._tick)

    def _tick(self):
        if self.index < len(self.full_text):
            self.update(self.full_text[: self.index + 1])
            self.index += 1
        else:
            self.timer.pause()

    def reset_and_play(self, new_text: str):
        self.full_text = new_text
        self.index = 0
        self.timer.resume()

from textual.widgets import Static
from textual.timer import Timer

class MultiEntryTypewriter(Static):
    """逐条 LogEntry 播放的打字机组件"""

    def __init__(self, speed: float = 0.02):
        super().__init__("")
        self.speed = speed
        self.entries: list[str] = []
        self.current_text = ""
        self.index = 0
        self.timer: Timer | None = None
        self.playing = False

    def on_mount(self):
        self.timer = self.set_interval(self.speed, self._tick)
        self.timer.pause()

    def play_entries(self, entries: list[str]):
        """传入多条文本，开始逐条播放"""
        self.entries = entries
        self.current_text = ""
        self.index = 0
        self.update("")
        self.playing = True
        self.timer.resume()

    def _tick(self):
        if not self.playing:
            return

        # 当前条目播放完 → 切换下一条
        if self.index >= len(self.current_text):
            if self.entries:
                self.current_text = self.entries.pop(0)
                self.index = 0
                self.update("")  # 清空，准备播放下一条
            else:
                self.playing = False
                self.timer.pause()
                return

        # 播放当前条目
        self.update(self.current_text[: self.index + 1])
        self.index += 1
