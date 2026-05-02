from typing import Dict
from models import Choice, Command, LogEntry, Scene

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
            LogEntry("", "\n[cyan]CALL_STATUS: disconnected_by_remote[/]\n"),
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
            LogEntry("", "\n[red]WARNING: Temporal Anomaly Detected[/]\n"),
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
