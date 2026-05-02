from typing import Dict
from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Input
from textual import on
from components import StatusBar, StoryLog, InputBar, OptionsConsole
from models import LogEntry, Scene, Choice, Command

# ==============================================================================
# 模拟数据库：场景集合
# ==============================================================================
SCENE_DB: Dict[str, Scene] = {
    "scene_01": Scene(
        id="scene_01",
        location="Home",
        time="08:00:00 JST",
        entries=[
            LogEntry(
                "[08:00:45] Haruhi >", "太慢了！给你二十分钟，立刻到站前的咖啡厅集合！"
            ),
            LogEntry("[08:00:52] Haruhi >", "那种形式主义省略掉也没关系！总之快点来！"),
            LogEntry("", "\n[cyan]CALL_STATUS: disconnected_by_remote[/cyan]\n"),
            LogEntry("[08:01:15] Kyon >", "开什么玩笑。今天是 5 月 2 日，是黄金周啊。"),
        ],
        choices=[
            Choice("把头埋进被子里装死", "scene_02_a"),
            Choice("叹口气，乖乖起床穿衣服", "scene_02_b"),
        ],
        commands=[Command("status - 查看当前状态", None)],
        hint="两种选择最终都会走向咖啡厅——但阿虚的心情不同",
    ),
    "scene_02_a": Scene(
        id="scene_02_a",
        location="Bedroom",
        time="08:05:00 JST",
        entries=[
            LogEntry("[08:05:01] System >", "你选择了把头埋进被子里。"),
            LogEntry("[08:05:05] Kyon >", "只要我假装没听见，世界毁灭就与我无关..."),
            LogEntry("", "\n[red]WARNING: Temporal Anomaly Detected[/red]\n"),
            LogEntry("[08:05:10] Sister >", "阿虚！凉宫学姐直接冲进家里来了啊！"),
        ],
        choices=[Choice("面对现实，滚下床", "scene_03")],
        commands=[],
        hint="逃避可耻且没用。",
    ),
    "scene_02_b": Scene(
        id="scene_02_b",
        location="Street",
        time="08:15:00 JST",
        entries=[
            LogEntry("[08:15:01] System >", "你穿戴整齐，走出了家门。"),
            LogEntry(
                "[08:15:05] Kyon >",
                "五月的阳光真刺眼，比起拯救世界，我现在更需要一杯咖啡。",
            ),
        ],
        choices=[Choice("加快脚步前往站前咖啡厅", "scene_03")],
        commands=[],
        hint="向命运低头。",
    ),
    "scene_03": Scene(
        id="scene_03",
        location="Cafe",
        time="08:20:00 JST",
        entries=[
            LogEntry(
                "[08:20:00] Haruhi >", "太慢了！说好的二十分钟，你居然用了二十一分钟！"
            ),
            LogEntry("[08:20:05] System >", "END OF DEMO."),
        ],
        choices=[],
        commands=[Command("quit - 退出系统", "quit")],
        hint="流程演示结束。",
    ),
}


class NagatoInterface(App[None]):
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
        self.transition_to_scene("scene_01")

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
    app = NagatoInterface()
    app.run()
