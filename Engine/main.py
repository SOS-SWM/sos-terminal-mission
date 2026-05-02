from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Input
from textual import on
from components import StatusBar, StoryLog, InputBar, OptionsConsole
from mikuru import MikuruTypingSurvival
from scene import SCENE_DB


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
        self.transition_to_scene(self.initial_scene_id or "scene_01")

    def transition_to_scene(self, scene_id: str) -> None:
        scene = SCENE_DB.get(scene_id)
        if scene:
            self.current_scene = scene
            self.query_one(StatusBar).update_status(scene.location, scene.time)
            self.query_one(StoryLog).render_scene_log(scene)
            self.query_one(OptionsConsole).render_options(
                scene.choices, scene.commands, scene.hint
            )

            self.query_one(InputBar).focus_input()

    # def on_input_submitted(self, event: Input.Submitted) -> None:
    #     user_input = event.value.strip()
    #     event.input.value = ""

    #     if user_input:
    #         self.process_command(user_input)

    #     event.input.focus()

    def process_command(self, user_input: str) -> None:
        """抽取出的逻辑处理函数"""
        scene = self.current_scene
        if not scene:
            return
        log_view = self.query_one(StoryLog)

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(scene.choices):
                self.transition_to_scene(scene.choices[idx].next_scene_id)
            else:
                log_view.write("[bold red]无效的选项编号。[/]")
        else:
            # 简单的命令匹配
            for cmd in scene.commands:
                cmd_key = cmd.name.split()[0].lower()
                if user_input.lower() == cmd_key:
                    if cmd.next_scene_id == "quit":
                        self.exit()
                    elif cmd.next_scene_id == "game":
                        self.exit(self.current_scene.id)
                    elif cmd.next_scene_id:
                        self.transition_to_scene(cmd.next_scene_id)
                    else:
                        log_view.write("[cyan]系统状态正常。[/]")
                    return
            log_view.write("[bold red]未识别的指令。[/]")

    @on(Input.Submitted, "#player-input")
    def handle_input(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return

        # 你的原始逻辑
        self.process_command(raw)

        # 清空并重新聚焦
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
