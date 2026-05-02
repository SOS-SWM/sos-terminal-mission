from dataclasses import dataclass, field
from typing import List, Dict
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Input, RichLog
from rich.text import Text
from textual import on
# ==============================================================================
# 数据结构接口定义
# ==============================================================================
@dataclass
class LogEntry:
    frontmatter: str
    content: str

@dataclass
class Command:
    name: str
    next_scene_id: str | None

@dataclass
class Choice:
    name: str
    next_scene_id: str

@dataclass
class Scene:
    id: str
    location: str = ""
    time: str = ""
    entries: List[LogEntry] = field(default_factory=list)
    commands: List[Command] = field(default_factory=list)
    choices: List[Choice] = field(default_factory=list)
    hint: str = ""

# ==============================================================================
# 模拟数据库：场景集合
# ==============================================================================
SCENE_DB: Dict[str, Scene] = {
    "scene_01": Scene(
        id="scene_01",
        location="Home",
        time="08:00:00 JST",
        entries=[
            LogEntry("[08:00:45] Haruhi >", "太慢了！给你二十分钟，立刻到站前的咖啡厅集合！"),
            LogEntry("[08:00:52] Haruhi >", "那种形式主义省略掉也没关系！总之快点来！"),
            LogEntry("", "\n[cyan]CALL_STATUS: disconnected_by_remote[/cyan]\n"),
            LogEntry("[08:01:15] Kyon >", "开什么玩笑。今天是 5 月 2 日，是黄金周啊。"),
        ],
        choices=[
            Choice("把头埋进被子里装死", "scene_02_a"),
            Choice("叹口气，乖乖起床穿衣服", "scene_02_b")
        ],
        commands=[Command("status - 查看当前状态", None)],
        hint="两种选择最终都会走向咖啡厅——但阿虚的心情不同"
    ),
    "scene_02_a": Scene(
        id="scene_02_a",
        location="Bedroom",
        time="08:05:00 JST",
        entries=[
            LogEntry("[08:05:01] System >", "你选择了把头埋进被子里。"),
            LogEntry("[08:05:05] Kyon >", "只要我假装没听见，世界毁灭就与我无关..."),
            LogEntry("[]", "\n[red]WARNING: Temporal Anomaly Detected[/red]\n[]"),
            LogEntry("[08:05:10] Sister >", "阿虚！凉宫学姐直接冲进家里来了啊！"),
        ],
        choices=[Choice("面对现实，滚下床", "scene_03")],
        commands=[],
        hint="逃避可耻且没用。"
    ),
    "scene_02_b": Scene(
        id="scene_02_b",
        location="Street",
        time="08:15:00 JST",
        entries=[
            LogEntry("[08:15:01] System >", "你穿戴整齐，走出了家门。"),
            LogEntry("[08:15:05] Kyon >", "五月的阳光真刺眼，比起拯救世界，我现在更需要一杯咖啡。"),
        ],
        choices=[Choice("加快脚步前往站前咖啡厅", "scene_03")],
        commands=[],
        hint="向命运低头。"
    ),
    "scene_03": Scene(
        id="scene_03",
        location="Cafe",
        time="08:20:00 JST",
        entries=[
            LogEntry("[08:20:00] Haruhi >", "太慢了！说好的二十分钟，你居然用了二十一分钟！"),
            LogEntry("[08:20:05] System >", "END OF DEMO."),
        ],
        choices=[],
        commands=[Command("quit - 退出系统", "quit")],
        hint="流程演示结束。"
    )
}

# ==============================================================================
# 独立 UI 组件拆分
# ==============================================================================
class StatusBar(Static):
    """顶栏：负责展示系统状态和位置时间"""
    def update_status(self, location: str, time: str) -> None:
        content = (
            f"█ SYSTEM: [bold cyan]Nagato_Interface v1.1.4[/]  █  "
            f"WORLDLINE: [bold yellow]0xFF-05-02[UNSTABLE][/]  █  "
            f"USER: root@kyon  █  "
            f"LOCATION: [bold green]{location}[/]  █  "
            f"TIME: {time}"
        )
        self.update(content)

class StoryLog(RichLog):
    """中间层：负责故事流打印"""
    def render_scene_log(self, entries: List[LogEntry]) -> None:
        self.clear() # 切换场景时清屏（或者也可以保留，视你的需求而定）
        self.write("\n[bold black]==================== SCENE INITIALIZED ====================[/]")
        for entry in entries:
            if "CALL_" in entry.content or "WARNING" in entry.content:
                self.write(entry.frontmatter + entry.content)
            else:
                parts = entry.frontmatter.split("]", 1)
                if len(parts) == 2:
                    time_stamp = f"{parts[0]}]"
                    speaker = parts[1]
                    self.write(f"[green]{time_stamp}[/] [bold yellow]{speaker}[/] {entry.content}")
                else:
                    self.write(f"{entry.frontmatter} {entry.content}")

class OptionsConsole(Static):
    """选项台：负责安全地渲染交互选项（基于 rich.text.Text 防止标记冲突）"""
    def render_options(self, choices: List[Choice], commands: List[Command], hint: str) -> None:
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

# ==============================================================================
# 主应用调度器
# ==============================================================================
# class NagatoInterface(App):
#     CSS = """
#     Screen { background: #050505; }
    
#     StatusBar { dock: top; height: 1; color: #2eb82e; }
    
#     #main-layout { height: 1fr; }
    
#     #log-container { height: 70%; border: solid #1a4d1a; margin: 0 1; }
#     #console-container { height: 30%; border: solid #1a4d1a; margin: 0 1; }
    
#     #input-area {
#         dock: bottom;
#         height: 3;
#         background: #0a0a0a;
#         border-top: tall #1a4d1a;
#         padding: 0 1;
#     }
    
#     #prompt { color: #33cc33; padding-top: 1; }
    
#     Input {
#         width: 1fr;
#         border: none;
#         background: transparent;
#         color: white;
#     }
#     /* 去除 Input 默认的聚焦蓝色边框 */
#     Input:focus { border: none; } 
#     """

#     def __init__(self):
#         super().__init__()
#         self.current_scene: Scene = None

#     def compose(self) -> ComposeResult:
#         yield StatusBar(id="status-bar")
        
#         with Vertical():
#             with Container(id="log-container") as log_cont:
#                 log_cont.border_title = " LOG_STDOUT "
#                 yield StoryLog(id="story-log", markup=True, wrap=True)
            
#             with Container(id="console-container") as cons_cont:
#                 cons_cont.border_title = " INTERACTIVE_CONSOLE | CONTEXT_OPTIONS "
#                 yield OptionsConsole(id="options-console")
        
#         yield CommandInputArea(id="input-area")

#     def on_mount(self) -> None:
#         """初始化首个场景"""
#         self.transition_to_scene("scene_01")

#     def transition_to_scene(self, scene_id: str) -> None:
#         """核心路由引擎：处理场景切换与组件数据分发"""
#         if scene_id not in SCENE_DB:
#             self.query_one(StoryLog).write(f"[bold red]ERROR: Scene '{scene_id}' not found.[/]")
#             return

#         self.current_scene = SCENE_DB[scene_id]
#         scene = self.current_scene

#         # 数据下发到各个子组件
#         self.query_one(StatusBar).update_status(scene.location, scene.time)
#         self.query_one(StoryLog).render_scene_log(scene.entries)
#         self.query_one(OptionsConsole).render_options(scene.choices, scene.commands, scene.hint)

#     def on_input_submitted(self, event: Input.Submitted) -> None:
#         """统一输入处理：接收子组件 Input 的事件"""
#         user_input = event.value.strip()
#         if not user_input: return
        
#         log_view = self.query_one(StoryLog)
#         log_view.write(f"\n[bold white]>>> {user_input}[/]")
#         event.input.value = ""

#         # 简单的状态机判断逻辑
#         if not self.current_scene: return

#         # 1. 检查是否匹配选项编号 (如输入 "1" 或 "2")
#         if user_input.isdigit():
#             idx = int(user_input) - 1
#             if 0 <= idx < len(self.current_scene.choices):
#                 next_id = self.current_scene.choices[idx].next_scene_id
#                 self.transition_to_scene(next_id)
#                 return
#             else:
#                 log_view.write("[bold red]无效的选项编号。[/]")
#                 return

#         # 2. 检查是否匹配命令前缀
#         for cmd in self.current_scene.commands:
#             # 假设输入 'status' 能匹配到 'status - 查看当前状态'
#             if user_input.lower() in cmd.name.lower():
#                 if cmd.next_scene_id == "quit":
#                     self.exit()
#                 elif cmd.next_scene_id:
#                     self.transition_to_scene(cmd.next_scene_id)
#                 else:
#                     log_view.write("[bold cyan]系统返回: 当前状态正常。没能检测到异常时间干涉。[/]")
#                 return
        
#         log_view.write("[bold red]未识别的指令或选项。[/]")

class NagatoInterface(App):
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
        self.query_one(InputBar).focus_input()
        self.transition_to_scene("scene_01")

    def transition_to_scene(self, scene_id: str) -> None:
        scene = SCENE_DB.get(scene_id)
        if scene:
            self.current_scene = scene
            self.query_one(StatusBar).update_status(scene.location, scene.time)
            self.query_one(StoryLog).render_scene_log(scene.entries)
            self.query_one(OptionsConsole).render_options(scene.choices, scene.commands, scene.hint)

            self.query_one(InputBar).focus_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        event.input.value = ""

        if user_input:
            self.process_command(user_input)

        event.input.focus()


    def process_command(self, user_input: str) -> None:
        """抽取出的逻辑处理函数"""
        scene = self.current_scene
        if not scene: return
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