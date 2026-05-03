from typing import Any
from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Input
from textual import on
from components import StatusBar, StoryLog, InputBar, OptionsConsole
from credit import EndingCreditScene
from mikuru import MikuruTypingSurvival
from engine import GameEngine
from textual import events
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame

# 1096, boot
bgm_path = ["assets/1096.mp3", "assets/fixed.wav", "assets/haruhi.mp3"]


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

    def __init__(
        self,
        initial_scene_id: str | None,
        is_entered_mikuru: bool,
        engine: Any,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.initial_scene_id = initial_scene_id
        self.engine = engine

        self.last_scene_id = None
        self.is_playing = False  # 是否正在播放动画
        self.is_entered_mikuru = is_entered_mikuru

        self.bgm_map = {
            # 1. 神前暁 - そして、いつもの風景
            "c1a_leave_home": "assets/itsumo_no_fuukei.mp3",
            "c2a_cafe": "assets/itsumo_no_fuukei.mp3",
            "c2a_protest": "assets/itsumo_no_fuukei.mp3",
            "c2a_paid": "assets/itsumo_no_fuukei.mp3",
            # 2. 神前暁 - 何かがおかしい
            "c1b_leave_home": "assets/nanika_ga_okashii.mp3",
            "c2b_cafe": "assets/nanika_ga_okashii.mp3",
            "c2b_status": "assets/nanika_ga_okashii.mp3",
            "c2b_protest": "assets/nanika_ga_okashii.mp3",
            "c2b_paid": "assets/nanika_ga_okashii.mp3",
            # 3. 神前暁 - カマドウマ
            "c4b_insufficient": "assets/kamadouma.mp3",
            "c4a_final": "assets/kamadouma.mp3",
            # 4. 神前暁 - ミクル変身! そして戦闘!
            "c4b_true_end": "assets/mikuru_henshin.mp3",
        }
        self.current_bgm_path = None

    def _play_scene_bgm(self, scene_id: str) -> None:
        """根据场景 ID 自动切换背景音乐"""
        pygame.mixer.music.set_volume(0.3)
        if scene_id not in self.bgm_map:
            if self.current_bgm_path is not None:
                pygame.mixer.music.fadeout(1000)
                self.current_bgm_path = None
            return

        target_bgm = self.bgm_map[scene_id]
        if self.current_bgm_path != target_bgm:
            try:
                pygame.mixer.music.load(target_bgm)
                # fade_ms=1000 会让新音乐自带 1 秒的淡入效果，平滑过渡
                pygame.mixer.music.play(loops=-1, fade_ms=1000)
                self.current_bgm_path = target_bgm
            except Exception:
                pass

    def play_boot_music(self, seconds: float):
        pygame.mixer.music.load(bgm_path[1])
        pygame.mixer.music.play()

        def stop_music():
            pygame.mixer.music.stop()

        self.set_timer(seconds, stop_music)

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")

        with Vertical(id="main-layout"):
            with Container(id="log-container"):
                yield StoryLog(id="story-log", markup=True)
            with Container(id="console-container"):
                yield OptionsConsole(id="options-console")

        yield InputBar(id="inputbar")

    def on_mount(self) -> None:
        if not self.is_entered_mikuru:
            self.play_boot_music(3.3)
        self.theme = "ansi-dark"
        self.query_one(InputBar).focus_input()
        log = self.query_one(StoryLog)
        log.on_line_written = self._on_line_written
        self._refresh_ui_for_new_scene()

    def _refresh_ui_for_new_scene(self) -> None:
        scene = self.engine.current_scene()
        log = self.query_one(StoryLog)

        # 隐藏旧选项并禁用输入，防止在动画时操作
        # TODO: 加入 skip 指令 快速播放完动画
        # self.query_one(OptionsConsole).update("")
        # self.query_one("#player-input").disabled = True

        self._play_scene_bgm(self.engine.state.current_scene_id)

        # 初始状态栏更新
        self._update_status_bar()

        # 开始播放场景日志，并传入回调
        self.is_playing = True
        log.render_scene_log(
            scene,
            on_complete=self._on_log_complete,
        )

        # NOTE: 学姐特化
        if (
            self.is_entered_mikuru
            and self.initial_scene_id == "c3b_store_revisit"
            and self.last_scene_id is None
        ):
            log.flush_pending_entries()

    def _on_line_written(self, line: str) -> None:
        # 调度异步函数，不阻塞 UI
        self.call_later(self.transfer2mikutu, line)

    def _update_status_bar(self) -> None:
        self.query_one(StatusBar).update_status()

    def _on_log_complete(self) -> None:
        self.is_playing = False

        # 捕捉结局
        if getattr(self.engine.state, "game_over", False):
            # 清空普通选项，显示通关提示
            self.query_one(OptionsConsole).render_options(
                [], [], "【 请按回车键继续 】"
            )
            input_widget = self.query_one("#player-input")
            input_widget.disabled = False
            self.query_one(InputBar).clear_input()
            self.query_one(InputBar).focus_input()
            return

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

    async def transfer2mikutu(self, line: str) -> None:
        if "可不只是乌龟啊" in line and not self.is_entered_mikuru:
            app.exit(self.engine.state.current_scene_id)

    def process_command(self, raw: str) -> None:
        """处理玩家输入的核心逻辑。"""
        # self.query_one("#player-input").disabled = True
        self.query_one(OptionsConsole).update("")  # 清空选项区

        if (
            raw.lower() == "skip" and self.is_playing
        ):  # and self.engine.state.loop_count() > 1:
            self.query_one(StoryLog).flush_pending_entries()
            # self.is_playing = False
            return

        if self.is_playing:
            return

        # 打印玩家自己的输入
        log = self.query_one(StoryLog)

        # 从引擎获取结果
        entries, is_command = self.engine.process_input(raw)

        if self.engine.state.game_over:
            self.exit("GAME_CLEARED")
            return

        # 进入新场景
        if self.engine.state.current_scene_id != self.last_scene_id and not is_command:
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
        if getattr(self.engine.state, "game_over", False) and not self.is_playing:
            self.exit("GAME_CLEARED")
            return

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
    pygame.mixer.init()

    current_scene_id: str | None = None
    # current_scene_id = "c4b_true_end"
    is_entered_mikuru = False
    engine = GameEngine(current_scene_id)
    while True:
        app = NagatoInterface(current_scene_id, is_entered_mikuru, engine)
        current_scene_id = app.run()
        if not current_scene_id:
            break

        if current_scene_id == "GAME_CLEARED":
            EndingCreditScene().run()
            break

        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.load(bgm_path[0])
        pygame.mixer.music.play(loops=-1)
        mikuru = MikuruTypingSurvival()

        is_entered_mikuru = True
        mikuru.run()
        pygame.mixer.music.fadeout(1000)
