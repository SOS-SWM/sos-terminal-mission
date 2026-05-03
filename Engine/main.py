from typing import Any
from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Input
from textual import on
from components import StatusBar, StoryLog, InputBar, OptionsConsole
from mikuru import MikuruTypingSurvival
from engine import GameEngine
from textual import events

class NagatoInterface(App[str]):
    CSS = """
    Screen {
        background: #050505;
        layout: vertical;
    }
    #story-log {
        overflow-x: hidden;
        scrollbar-gutter: stable;
    }
    #main-layout {
        layout: vertical;
        height: 1fr;
    }

    #log-container {
        height: 70%;
        border: solid #1a4d1a;
        margin: 0 1;
        overflow: hidden;
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
        self.engine = GameEngine(initial_scene_id)

        self.last_scene_id = None
        self.is_playing = False  # 是否正在播放动画

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
        self._refresh_ui_for_new_scene()

    def _refresh_ui_for_new_scene(self) -> None:
        scene = self.engine.current_scene()
        log = self.query_one(StoryLog)

        # 隐藏旧选项并禁用输入，防止在动画时操作
        # TODO: 加入 skip 指令 快速播放完动画
        # self.query_one(OptionsConsole).update("")
        # self.query_one("#player-input").disabled = True

        # 初始状态栏更新
        self._update_status_bar()

        # 开始播放场景日志，并传入回调
        self.is_playing = True
        log.render_scene_log(
            scene,
            on_complete=self._on_log_complete,
        )

    def _update_status_bar(self) -> None:
        self.query_one(StatusBar).update_status()

    def _on_log_complete(self) -> None:
        self.is_playing = False

        # 刷新选项
        scene = self.engine.current_scene()
        available_choices = [
            c for c in scene.choices if self.engine._choice_available(c)
        ]
        self.query_one(OptionsConsole).render_options(
            available_choices, scene.commands, scene.hint
        )

        # 重新启用并聚焦输入框
        input_widget = self.query_one("#player-input")
        input_widget.disabled = False
        self.query_one(InputBar).clear_input()
        self.query_one(InputBar).focus_input()

        # 检查是否需要触发小游戏
        if self.engine.state.current_scene_id == "mikuru_game":
            self.exit("mikuru_game")

    def process_command(self, raw: str) -> None:
        """处理玩家输入的核心逻辑。"""
        # self.query_one("#player-input").disabled = True
        self.query_one(OptionsConsole).update("")  # 清空选项区

        if raw.lower() == "skip" and self.is_playing: #and self.engine.state.loop_count() > 1:
            self.query_one(StoryLog).flush_pending_entries()
            self.is_playing = False
            return

        if self.is_playing:
            return

        # 打印玩家自己的输入
        log = self.query_one(StoryLog)

        # 从引擎获取结果
        entries, is_command = self.engine.process_input(raw)

        if self.engine.state.game_over:
            self.exit()
            return

        # 进入新场景
        if (
            self.engine.state.current_scene_id != self.last_scene_id
            and self.last_scene_id is not None
        ):
            self._refresh_ui_for_new_scene()
        else:
            if is_command:
                log.render_log_entries_immediately(
                    entries,
                    on_complete=self._on_log_complete,
                )
            else:
                self.is_playing = True
                log.render_entries_append(
                    entries,
                    on_complete=self._on_log_complete,
                )

        self.last_scene_id = self.engine.state.current_scene_id

    @on(Input.Submitted, "#player-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return

        self.process_command(raw)

        bar = self.query_one(InputBar)
        bar.clear_input()
        bar.focus_input()

    async def on_key(self, event: events.Key) -> None:
        log = self.query_one(StoryLog)

        # ↑ 上箭头
        if event.key == "up":
            log.scroll_up()
            event.stop()

        # ↓ 下箭头
        elif event.key == "down":
            log.scroll_down()
            event.stop()

        # PageUp
        elif event.key == "pageup":
            log.scroll_page_up()
            event.stop()

        # PageDown
        elif event.key == "pagedown":
            log.scroll_page_down()
            event.stop()


if __name__ == "__main__":
    current_scene_id: str | None = None

    while True:
        app = NagatoInterface(current_scene_id)
        current_scene_id = app.run()
        if not current_scene_id:
            break
        mikuru = MikuruTypingSurvival()
        mikuru.run()
