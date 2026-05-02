"""
scenario.py — All story content (Chapters 1-4, first loop + loop variants).
Only imports from models. Zero UI / engine logic.

Effect legend:
  typewriter       — default char-by-char
  typewriter_slow  — dramatic slow reveal
  typewriter_fast  — quick system lines
  flicker          — screen flash before this line
  glitch           — mild text corruption
  glitch_heavy     — heavy corruption burst
  jitter           — text shakes
  reboot           — full screen wipe animation
  worldline_shift  — dramatic WORLDLINE banner
  route_trace      — animated ASCII path
  route_trace_ghost— route trace with echo
  separator        — horizontal rule
  warning          — amber pulse
  success          — green flash
  cursor_fast      — blinking cursor line
  instant          — no animation
"""
from __future__ import annotations
from haruhi_rpg.models import (
    Scene, LogEntry, Choice, Command,
    WORLDLINE_STABLE, WORLDLINE_UNSTABLE, WORLDLINE_SHIFTING,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shorthand constructors
# ─────────────────────────────────────────────────────────────────────────────

def _n(ts: str, text: str, effect="typewriter", speed=1.0) -> LogEntry:
    """Narration line."""
    return LogEntry(ts, "narration", None, text, effect, speed)

def _d(ts: str, speaker: str, text: str, effect="typewriter", speed=1.0) -> LogEntry:
    """Dialogue line."""
    return LogEntry(ts, "dialogue", speaker, text, effect, speed)

def _s(ts: str, text: str, effect="typewriter_fast", speed=0.6) -> LogEntry:
    """System line."""
    return LogEntry(ts, "system", None, text, effect, speed)

def _fx(text: str, effect="separator") -> LogEntry:
    """Pure effect / decoration line."""
    return LogEntry("", "fx", None, text, effect, 1.0)

def _sep() -> LogEntry:
    return _fx("", "separator")


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 1A — 第一次未轮回
# ─────────────────────────────────────────────────────────────────────────────

def _ch1a() -> dict[str, Scene]:
    scenes = {}

    # ── 清晨来电 ──────────────────────────────────────────────────────────────
    scenes["c1a_morning_call"] = Scene(
        id="c1a_morning_call",
        set_location="Home", set_time="08:00:00 JST",
        entries=[
            _fx("", "reboot"),
            _s("08:00:00", "System booting..."),
            _s("08:00:01", "DATE: 05/02"),
            _s("08:00:02", "WORLDLINE_SHIFT: 0.000001%", "glitch"),
            _s("08:00:03", "USER: root@sos-brigade:/home/kyon"),
            _s("08:00:04", "ACCESS_LEVEL: normal"),
            _sep(),
            _n("08:00:20", "光线从窗帘缝隙里挤进房间。", speed=1.3),
            _n("08:00:25",
               "黄金周的第一天，本应以一种对人类文明来说极其合理的方式开始：睡到自然醒。",
               speed=1.2),
            _n("08:00:35", "电话铃声刺穿了这个合理计划。"),
            _d("08:00:37", "Sister", "阿虚，电话。"),
            _d("08:00:40", "Kyon", "不用说我也知道。"),
            _d("08:00:42", "Kyon",
               "会在假期早上八点打电话来的，不是推销员，就是比推销员更难对付的人。"),
            _sep(),
            _s("08:00:43", "CALL_SOURCE: Haruhi Suzumiya", "warning"),
            _s("08:00:44", "CALL_STATUS: forced_connected", "cursor_fast"),
            _sep(),
            _d("08:00:45", "Haruhi",
               "太慢了！给你二十分钟，立刻到站前的咖啡厅集合！", speed=0.8),
            _d("08:00:46", "Haruhi", "迟到的话死刑！", speed=0.8),
            _d("08:00:50", "Kyon", "我甚至还没说喂。"),
            _d("08:00:52", "Haruhi", "那种形式主义省略掉也没关系！总之快点来！"),
            _s("08:01:10", "CALL_STATUS: disconnected_by_remote"),
            _sep(),
            _d("08:01:15", "Kyon", "开什么玩笑。今天是 5 月 2 日，是黄金周啊。"),
            _d("08:01:18", "Kyon",
               "劳动节的初衷难道不是为了让劳动者有尊严地躺在被窝里睡到中午吗？"),
            _d("08:01:22", "Kyon",
               "虽然在日本既不过劳动节我也算不上什么劳动者，"
               "但在这个神圣的日子里强迫高中生劳动，简直是对现代文明的公然挑衅。",
               speed=1.1),
        ],
        choices=[
            Choice(1, "把头埋进被子里装死", "c1a_blanket"),
            Choice(2, "叹口气，乖乖起床穿衣服", "c1a_leave_home"),
        ],
        hint="[HINT] 两种选择最终都会走向咖啡厅——但阿虚的心情不同",
        commands=[Command("status", "查看当前状态", "status")],
    )

    # ── 被窝抵抗 ──────────────────────────────────────────────────────────────
    scenes["c1a_blanket"] = Scene(
        id="c1a_blanket",
        set_time="08:01:30 JST",
        entries=[
            _n("08:01:30", "你把头埋进被子里，试图用棉织品构筑一道抵抗凉宫春日的防线。",
               "dim"),
            _d("08:01:35", "Kyon",
               "只要我不承认电话存在，电话就没有发生过。"),
            _d("08:01:38", "Kyon",
               "这是一种高度先进的精神胜利法，虽然大概率只能持续三十秒。"),
            _sep(),
            _s("08:02:00", "手机开始连续震动。"),
            _s("08:02:01", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:05", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:10", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:15", "MESSAGE_FROM_HARUHI: 我已经开始计时了。", "warning"),
            _sep(),
            _d("08:02:18", "Kyon", "这已经不是催促了，这是小型精神污染。"),
            _d("08:02:22", "Kyon", "好吧，好吧，真是没办法，我起来就是了。"),
        ],
        choices=[Choice(1, "起床", "c1a_leave_home")],
        hint="[HINT] 被窝终究不是避风港",
    )

    # ── 出门 ──────────────────────────────────────────────────────────────────
    scenes["c1a_leave_home"] = Scene(
        id="c1a_leave_home",
        set_time="08:10:00 JST", set_location="Street",
        entries=[
            _n("08:10:10",
               "你用高中男生所能拥有的最低限度仪容整理能力换好衣服。"),
            _n("08:12:20", "你推着自行车走出家门。"),
            _n("08:12:25",
               "天气晴朗得过分，仿佛连云都被春日命令不准迟到。"),
            _d("08:12:30", "Kyon",
               "如果这世界上真的存在神明，希望她至少能给我报销咖啡厅的账单。"),
            _sep(),
            _s("08:20:00", "ROUTE: home → cafe", "route_trace"),
        ],
        choices=[],
        hint="[HINT] 自动前往咖啡厅……",
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 1B — 轮回后清晨
# ─────────────────────────────────────────────────────────────────────────────

def _ch1b() -> dict[str, Scene]:
    scenes = {}

    scenes["c1b_morning_reboot"] = Scene(
        id="c1b_morning_reboot",
        set_location="Home", set_time="08:00:00 JST",
        entries=[
            _fx("", "reboot"),
            _s("08:00:00", "System rebooting...", "flicker"),
            _s("08:00:01", "DATE: 05/02"),
            _s("08:00:02", "WORLDLINE_SHIFT: 0.000014%", "glitch"),
            _s("08:00:03", "USER: root@sos-brigade:/home/kyon"),
            _s("08:00:04", "WARNING: previous_session_trace_detected", "warning"),
            _s("08:00:05", "WARNING: overwritten", "glitch"),
            _sep(),
            _n("08:00:20", "光线从同一条窗帘缝隙里挤进房间。"),
            _d("08:00:23", "Kyon", "等一下。", speed=1.5),
            _d("08:00:26", "Kyon",
               "这个角度的阳光，这种讨厌的安静，还有我脑子里那种\"接下来要出事\"的感觉。"),
            _n("08:00:35", "电话铃声准时响起。"),
            _d("08:00:36", "Kyon", "果然。", speed=1.8),
            _d("08:00:37", "Sister", "阿虚，电话。"),
            _d("08:00:39", "Kyon", "我知道。"),
            _d("08:00:41", "Kyon",
               "不如说，我从十五秒前就开始知道了。"),
            _sep(),
            _s("08:00:43", "CALL_SOURCE: Haruhi Suzumiya", "warning"),
            _s("08:00:44", "CALL_STATUS: forced_connected", "cursor_fast"),
            _sep(),
            _d("08:00:45", "Haruhi",
               "太慢了！给你二十分钟，立刻到站前的咖啡厅集合！"),
            _d("08:00:46", "Haruhi", "迟到的话死刑！"),
            _d("08:00:48", "Kyon", "春日。"),
            _d("08:00:50", "Haruhi", "干嘛？你该不会还没起床吧？"),
            _d("08:00:52", "Kyon", "你昨天是不是也说过同样的话？"),
            _s("08:00:55", "CALL_NOISE: zzzz···", "jitter"),
            _d("08:00:57", "Haruhi",
               "昨天？你睡糊涂了吧，今天才是假期第一天！"),
            _d("08:00:59", "Haruhi", "总之快来！今天的计划可是足以改变世界的！"),
            _s("08:01:10", "CALL_STATUS: disconnected_by_remote"),
            _sep(),
            _d("08:01:15", "Kyon", "改变世界。", speed=1.5),
            _d("08:01:18", "Kyon",
               "真遗憾，我总觉得它已经被改变过一次了。"),
        ],
        choices=[
            Choice(1, "再次把头埋进被子里", "c1b_blanket"),
            Choice(2, "直接起床，避免重复无意义抵抗", "c1b_leave_home"),
            Choice(3, "输入状态指令，确认自己的精神状态", "c1b_status"),
        ],
        hint="[HINT] 第二次轮回。记忆残留已被检测。",
        commands=[Command("status", "状态确认", "status")],
    )

    scenes["c1b_status"] = Scene(
        id="c1b_status",
        set_time="08:01:30 JST",
        entries=[
            _s("08:01:30", "INPUT: root@sos-brigade:/home/kyon# Status", "cursor_fast"),
            _s("08:01:32", "STATUS_CHECK_RUNNING...", "typewriter_slow"),
            _sep(),
            _s("??:??:??", "Kyon.status = {", "instant"),
            _s("??:??:??", "  sleep:   insufficient,", "typewriter_fast"),
            _s("??:??:??", "  wallet:  endangered,", "typewriter_fast"),
            _s("??:??:??", "  sanity:  suspicious,", "typewriter_fast"),
            _s("??:??:??", "  deja_vu: undeniable", "typewriter_fast"),
            _s("??:??:??", "}", "instant"),
            _sep(),
            _d("08:01:40", "Kyon", "连终端都开始用这种方式嘲笑我了吗？"),
            _s("08:01:42", "System_Log > 建议行动：前往咖啡厅。", "glitch"),
        ],
        choices=[Choice(1, "起床", "c1b_leave_home")],
        hint="[HINT] 状态检查完毕",
    )

    scenes["c1b_blanket"] = Scene(
        id="c1b_blanket",
        set_time="08:01:30 JST",
        entries=[
            _n("08:01:30", "你再次把头埋进被子里。", "dim"),
            _d("08:01:34", "Kyon",
               "如果第一次失败了，第二次也许会因为宇宙同情我而成功。"),
            _d("08:01:37", "Kyon",
               "虽然这个推论的科学性约等于春日的 UFO 计划。"),
            _sep(),
            _s("08:02:01", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:05", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:10", "MESSAGE_FROM_HARUHI: 还没出门？", "typewriter_fast"),
            _s("08:02:11", "MESSAGE_FROM_HARUHI: 你是不是又把头埋进被子里？",
               "warning"),
            _sep(),
            _d("08:02:13", "Kyon", "为什么是\"又\"？"),
            _d("08:02:15", "Haruhi", "直觉。", "glitch"),
            _d("08:02:18", "Kyon",
               "她的直觉已经发展到预知未来的程度了嘛？"),
        ],
        choices=[Choice(1, "承认失败并起床", "c1b_leave_home")],
        hint="[HINT] 被窝 v2.0，同样无效",
    )

    scenes["c1b_leave_home"] = Scene(
        id="c1b_leave_home",
        set_time="08:12:20 JST", set_location="Street",
        entries=[
            _n("08:10:00", "你换好衣服。"),
            _n("08:10:05", "动作熟练得让人不安。"),
            _d("08:10:08", "Kyon", "我是不是已经做过这件事？"),
            _n("08:12:20", "你推着自行车走出家门。"),
            _n("08:12:25",
               "天气晴朗得过分。连云的位置都像是从某个粗心的存档里复制过来的。"),
            _sep(),
            _s("08:12:30", "System_Log > route memory mismatch", "glitch"),
            _s("08:12:31", "System_Log > suggested observation: time and location",
               "glitch_heavy"),
            _sep(),
            _d("08:12:35", "Kyon", "时间和地点？"),
            _d("08:12:38", "Kyon",
               "喂，长门。如果这是你留下的提示，能不能下次直接写成现代日语？"),
            _s("08:20:00", "ROUTE: home → cafe", "route_trace_ghost"),
        ],
        choices=[],
        hint="[HINT] 记忆残留提示：时间与地点是关键",
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 2A — 第一次未轮回：咖啡厅 + 自由探索
# ─────────────────────────────────────────────────────────────────────────────

def _ch2a() -> dict[str, Scene]:
    scenes = {}

    # ── 咖啡厅集合 ────────────────────────────────────────────────────────────
    scenes["c2a_cafe"] = Scene(
        id="c2a_cafe",
        set_location="Cafe", set_time="09:10:14 JST",
        entries=[
            _n("09:10:14", "站前咖啡厅。"),
            _n("09:10:15", "你推门进去时，门铃发出过分轻快的声音。"),
            _n("09:10:18",
               "SOS 团其他成员已经坐在最显眼的位置，很明显，你又是最后一个到的。"),
            _d("09:10:22", "Haruhi",
               "阿虚，你又是最后一个到的，今天你来买单。"),
            _d("09:10:24", "Kyon", "果然。"),
            _sep(),
            _n("09:10:30",
               "春日面前摊着几张打印纸，上面密密麻麻标着红圈、箭头和几个非常不可信的英文单词。"),
            _d("09:10:35", "Kyon", "那是什么？考试重点？"),
            _d("09:10:37", "Haruhi", "比考试重要一百倍！"),
            _d("09:10:39", "Haruhi",
               "这是特离谱先生公开的爱音斯坦岛文件相关资料！"),
            _d("09:10:42", "Kyon",
               "这个组合听起来就像新闻主播念到一半会开始怀疑自己职业选择。"),
            _d("09:10:46", "Haruhi", "重点不是名字！重点是外星人！"),
            _d("09:10:49", "Haruhi",
               "文件里一定藏着政府、财团、秘密组织联合隐瞒外星人存在的证据！"),
            _d("09:10:53", "Koizumi",
               "原来如此。确实是相当具有浪漫色彩的推测。"),
            _d("09:10:56", "Kyon",
               "把\"毫无根据\"说成\"浪漫色彩\"，你的良心真的还在吗？"),
            _d("09:11:00", "Mikuru", "外、外星人吗……"),
            _sep(),
            _n("09:12:00", "春日双手重重拍在桌子上。"),
            _d("09:12:02", "Haruhi",
               "各位！在这个无聊的黄金周，我决定了！", speed=0.9),
            _d("09:12:05", "Haruhi",
               "我们要建造一个 UFO，召唤真正的外星人！", speed=0.9),
            _d("09:12:08", "Kyon",
               "我能不能请问一下，为什么\"黄金周\"和\"UFO\"之间会存在因果关系？"),
            _d("09:12:12", "Haruhi", "因为普通的假期太普通了！"),
            _d("09:12:15", "Haruhi",
               "世界需要惊喜，需要刺激，需要会让人抬头仰望天空的事件！"),
            _d("09:12:19", "Haruhi", "所以行动代号就叫 Terminal Mission！"),
            _d("09:12:22", "Kyon", "这个名字里为什么有 Terminal？"),
            _d("09:12:24", "Haruhi", "因为听起来很像最终作战！"),
            _d("09:12:26", "Koizumi",
               "原来如此，非常有凉宫同学风格的计划。"),
            _d("09:12:29", "Kyon",
               "古泉，你这种毫无原则的附和速度，已经快到让人怀疑你是不是提前看过剧本了。"),
            _sep(),
            _d("09:12:35", "Haruhi", "古泉，去学校天台准备场地！"),
            _d("09:12:37", "Haruhi", "实玖瑠，去拿那个！"),
            _d("09:12:39", "Haruhi", "有希，准备核心元件！"),
            _d("09:12:41", "Haruhi",
               "至于阿虚，你负责买单，然后自由活动！不要偷懒！"),
            _d("09:12:44", "Mikuru",
               "那、那个……我真的要去拿吗？"),
            _d("09:12:47", "Haruhi",
               "当然！这可是决定外星人会不会相信我们的关键！"),
            _d("09:12:50", "Mikuru",
               "我、我觉得外星人应该不会因为那个相信我们……"),
            _d("09:12:53", "Yuki", "已确认。"),
            _d("09:12:55", "Koizumi", "那么，我先告辞了。"),
            _d("09:12:57", "Kyon",
               "等等，为什么你们接受任务的速度都这么快？"),
            _sep(),
            _n("09:39:50",
               "SOS 团成员以不符合咖啡厅礼仪的速度离席。"),
            _n("09:40:00", "桌上只剩下一张五人份的账单。"),
            _d("09:40:05", "Kyon",
               "看来今天的第一个奇迹已经发生了。"),
            _d("09:40:08", "Kyon",
               "五个人的消费，以一种不可思议的方式全部坠落到了我面前。"),
        ],
        choices=[
            Choice(1, "默默拿起账单", "c2a_paid"),
            Choice(2, "对着账单进行抗议", "c2a_protest"),
        ],
        hint="[HINT] Terminal Mission 已启动",
        commands=[Command("status", "查看状态", "status")],
    )

    scenes["c2a_protest"] = Scene(
        id="c2a_protest",
        set_time="09:40:10 JST",
        entries=[
            _d("09:40:10", "Kyon", "为什么每次都是我买单？"),
            _d("09:40:13", "Kyon", "我长得像人形 ATM 机吗？"),
            _d("09:40:16", "Kyon",
               "还是说 SOS 团的预算制度建立在\"阿虚会想办法\"这个极其不可靠的基础上？"),
            _n("09:40:20",
               "店员保持着职业微笑，把账单向你面前推近了三厘米。"),
            _d("09:40:24", "Kyon", "你的笑容很专业。"),
            _d("09:40:27", "Kyon",
               "专业到让我意识到，这张账单不会因为我的质疑而减少一円。"),
            _n("09:40:35", "账单金额没有变化。"),
            _d("09:40:38", "Kyon", "好吧。现实和春日总是不讲理的。"),
        ],
        choices=[Choice(1, "买单", "c2a_paid")],
        hint="[HINT] 现实不会因为抗议而改变",
    )

    scenes["c2a_paid"] = Scene(
        id="c2a_paid",
        set_time="09:42:00 JST",
        entries=[
            _s("09:42:00", "PAYMENT_STATUS: completed"),
            _s("09:42:01", "WALLET_DAMAGE: critical", "warning"),
            _sep(),
            _d("09:42:05", "Kyon",
               "如果有朝一日我写回忆录，这一章一定叫《我的钱钱哪去了》。"),
            _sep(),
            _s("09:45:00", "System_Log > Terminal Mission 已启动。", "success"),
            _s("09:45:01", "System_Log > 地点移动权限已开放。"),
            _s("09:45:02", "System_Log > 可使用命令：Go, Help, Status, Inventory"),
            _sep(),
            _s("09:45:05", "LOCATION_LIST:"),
            _s("09:45:06", "  [A] Street       — 大街"),
            _s("09:45:07", "  [B] Store        — 便利店"),
            _s("09:45:08", "  [C] Nagato_Apt   — 长门公寓"),
            _s("09:45:09", "  [D] Rooftop      — 学校天台"),
            _sep(),
            _d("09:45:15", "Kyon",
               "好吧。既然所有人都擅自行动了，我也只能先看看他们到底在搞什么。"),
        ],
        choices=[
            Choice(1, "去 Street — 大街",       "c2a_street"),
            Choice(2, "去 Store — 便利店",       "c2a_store"),
            Choice(3, "去 Nagato_Apt — 长门公寓", "c2a_nagato"),
            Choice(4, "去 Rooftop — 学校天台",   "c2a_rooftop"),
        ],
        hint="[HINT] 四个地点可以任意顺序探索，物品会在各处找到",
        commands=[
            Command("status",    "查看当前状态",   "status"),
            Command("inventory", "查看背包物品",   "inventory"),
        ],
    )

    # ── 大街 ──────────────────────────────────────────────────────────────────
    scenes["c2a_street"] = Scene(
        id="c2a_street",
        set_location="Street", set_time="10:00:00 JST",
        entries=[
            _n("10:00:00", "商业街。黄金周的人流比平时多出三倍。"),
            _n("10:00:10",
               "你在人群里发现了春日——她正拿着一个放大镜对着路边的电线杆研究。"),
            _d("10:00:15", "Haruhi",
               "阿虚！你看！这上面有符号！肯定是外星人留下的！"),
            _d("10:00:18", "Kyon",
               "那是城管贴的拆迁公告的残留胶带。"),
            _d("10:00:21", "Haruhi", "……可能是伪装成拆迁公告的外星信息。"),
            _d("10:00:24", "Kyon",
               "如果外星人需要伪装成城管才能传递信息，我对这个文明的科技水平感到忧虑。"),
            _sep(),
            _n("10:05:00",
               "春日已经开始对着电线杆拍照，路人绕道而行，用一种\"这孩子怎么了\"的眼神看你们。"),
            _d("10:05:05", "Haruhi",
               "阿虚，我发现了！外星人的 UFO 之所以没有公开出现，是因为它们在等一个信号！"),
            _d("10:05:10", "Kyon", "什么信号？"),
            _d("10:05:12", "Haruhi",
               "就是我们的 Terminal Mission！只要我们的\"外星人演出\"足够真实，"
               "真正的外星人就会被吸引过来验证真伪！"),
            _d("10:05:18", "Kyon",
               "这个逻辑在某种意义上完美自洽，但我说不出它哪里有问题。"),
            _d("10:05:22", "Koizumi",
               "（从旁边走过）其实凉宫同学的直觉往往比理性更接近事实。",
               speed=1.1),
            _d("10:05:25", "Kyon",
               "古泉你什么时候出现在这里的。"),
            _d("10:05:27", "Koizumi",
               "一直都在。只是您没有注意。"),
        ],
        choices=[
            Choice(1, "继续在大街上晃，观察春日", "c2a_street_2"),
            Choice(2, "离开，去其他地点",         "c2a_paid"),
        ],
        hint="[HINT] 大街上可以了解春日的外星人动机",
    )

    scenes["c2a_street_2"] = Scene(
        id="c2a_street_2",
        set_time="10:20:00 JST",
        entries=[
            _n("10:20:00",
               "你跟着春日在商业街走了二十分钟，期间她研究了三根电线杆、一个排水沟盖和一面涂鸦墙。"),
            _d("10:20:10", "Haruhi",
               "好了！情报收集完毕！今晚的演出一定会成功！"),
            _d("10:20:13", "Kyon",
               "你收集到了什么情报？"),
            _d("10:20:15", "Haruhi",
               "外星人在这条街上留下了七处痕迹！"),
            _d("10:20:18", "Kyon",
               "其中有几处是正常的城市基础设施损耗？"),
            _d("10:20:21", "Haruhi", "阿虚，你缺乏浪漫主义精神。"),
            _d("10:20:24", "Kyon",
               "我缺乏的是能够把排水沟盖联想到外星人的神经回路。"),
            _sep(),
            _n("10:25:00", "春日满意地合上笔记本，宣布大街调查完毕。"),
        ],
        choices=[
            Choice(1, "去 Store — 便利店",       "c2a_store"),
            Choice(2, "去 Nagato_Apt — 长门公寓", "c2a_nagato"),
            Choice(3, "去 Rooftop — 学校天台",   "c2a_rooftop"),
        ],
        hint="[HINT] 还有三个地点可以探索",
    )

    # ── 便利店 ────────────────────────────────────────────────────────────────
    scenes["c2a_store"] = Scene(
        id="c2a_store",
        set_location="Store", set_time="10:30:00 JST",
        entries=[
            _n("10:30:00", "车站旁边的便利店。"),
            _n("10:30:05", "店内人不多，收银台的店员正在整理商品。"),
            _n("10:30:15",
               "你在文具区找到了一包怪兽贴纸——怪兽的造型设计得扭曲而认真，"
               "背面写着\"适合儿童3岁以上使用\。"),
            _d("10:30:20", "Kyon",
               "春日让我找\"能配合UFO的装饰物\"，这应该满足条件了。"),
            _d("10:30:23", "Kyon",
               "虽然怪兽和飞碟之间并不存在天然的关联性。"),
        ],
        choices=[
            Choice(1, "买下怪兽贴纸（获得：普通的怪兽贴纸）", "c2a_store_buy"),
            Choice(2, "继续找找，看有没有更好的",            "c2a_store_browse"),
        ],
        hint="[HINT] 便利店可能有道具",
        commands=[Command("inventory", "查看背包", "inventory")],
        grant_items=[],
    )

    scenes["c2a_store_buy"] = Scene(
        id="c2a_store_buy",
        set_time="10:32:00 JST",
        grant_items=["普通的怪兽贴纸"],
        entries=[
            _n("10:32:00", "你拿起那包怪兽贴纸走向收银台。"),
            _s("10:32:05", "ITEM_ACQUIRED: 普通的怪兽贴纸", "success"),
            _d("10:32:08", "Kyon",
               "钱包受到了今天的第二次伤害。"),
            _d("10:32:10", "Kyon",
               "但我现在拥有一包能让三岁以上儿童感到满意的怪兽贴纸。"),
        ],
        choices=[
            Choice(1, "去其他地点",  "c2a_paid"),
        ],
        hint="[HINT] 已获得：普通的怪兽贴纸",
    )

    scenes["c2a_store_browse"] = Scene(
        id="c2a_store_browse",
        set_time="10:35:00 JST",
        entries=[
            _n("10:35:00", "你在店里转了一圈。"),
            _n("10:35:05",
               "零食区、冷藏区、文具区、和一个完全不知道为什么放在便利店里的小型充气玩具架。"),
            _d("10:35:10", "Kyon",
               "这里没有任何东西能让人觉得和\"召唤外星人\"有关系。"),
            _d("10:35:13", "Kyon",
               "怪兽贴纸大概已经是这个店里最接近的选项了。"),
        ],
        choices=[
            Choice(1, "还是买怪兽贴纸", "c2a_store_buy"),
            Choice(2, "什么都不买，离开", "c2a_paid"),
        ],
        hint="[HINT] 没有更好的选项了",
    )

    # ── 长门公寓 ──────────────────────────────────────────────────────────────
    scenes["c2a_nagato"] = Scene(
        id="c2a_nagato",
        set_location="Nagato_Apt", set_time="11:00:00 JST",
        entries=[
            _n("11:00:00", "长门有希的公寓。北高附近的高层公寓，第七百零八号房间。"),
            _n("11:00:10", "你按下门铃，等了三十秒。"),
            _n("11:00:40", "门开了。"),
            _d("11:00:42", "Yuki", "进来。"),
            _n("11:00:45", "房间里一如既往地安静。书架上堆满了书，每一本都厚得让人头疼。"),
            _d("11:01:00", "Kyon",
               "长门，春日让我来拿\"核心元件\"——她说你知道。"),
            _d("11:01:05", "Yuki", "……"),
            _d("11:01:08", "Yuki", "知道。"),
            _n("11:01:10", "长门走到储物间，拿出了一卷LED灯带和一个醒目的大红色按钮。"),
            _d("11:01:15", "Kyon",
               "灯带我能理解——它大概会让纸箱看起来更像飞碟。"),
            _d("11:01:18", "Kyon",
               "但这个大红按钮是……"),
            _d("11:01:21", "Yuki",
               "按下它。会发出声音。"),
            _d("11:01:24", "Kyon", "什么样的声音？"),
            _d("11:01:26", "Yuki", "……让人觉得有什么事要发生的声音。"),
        ],
        choices=[
            Choice(1, "拿走普通灯带（获得：普通的灯带）", "c2a_nagato_take_light"),
            Choice(2, "拿走大红按钮（获得：大红按钮）", "c2a_nagato_take_button"),
            Choice(3, "两样都拿",                        "c2a_nagato_take_both"),
        ],
        hint="[HINT] 长门公寓里有两件物品",
        commands=[Command("inventory", "查看背包", "inventory")],
    )

    scenes["c2a_nagato_take_light"] = Scene(
        id="c2a_nagato_take_light",
        grant_items=["普通的灯带"],
        set_time="11:10:00 JST",
        entries=[
            _n("11:05:00", "你拿起那卷灯带。"),
            _s("11:05:05", "ITEM_ACQUIRED: 普通的灯带", "success"),
            _d("11:05:10", "Kyon",
               "灯带比我想象的轻，但也比想象的旧——大概在某个储物间里放了好几年。"),
            _d("11:05:15", "Yuki", "……它会亮。"),
            _d("11:05:18", "Kyon", "有多少个 LED 是完好的？"),
            _d("11:05:20", "Yuki", "……半数。"),
            _d("11:05:22", "Kyon", "好吧。"),
        ],
        choices=[
            Choice(1, "离开，去其他地点", "c2a_paid"),
        ],
        hint="[HINT] 已获得：普通的灯带",
    )

    scenes["c2a_nagato_take_button"] = Scene(
        id="c2a_nagato_take_button",
        grant_items=["大红按钮"],
        set_time="11:10:00 JST",
        entries=[
            _n("11:05:00", "你拿起那个大红按钮。"),
            _s("11:05:05", "ITEM_ACQUIRED: 大红按钮", "success"),
            _d("11:05:10", "Kyon", "按钮上写着 Terminal Mission。"),
            _d("11:05:13", "Kyon",
               "春日给这个行动取的名字，连道具都配套了。"),
            _d("11:05:16", "Yuki", "……按下它的时机很重要。"),
            _d("11:05:19", "Kyon", "什么时机？"),
            _d("11:05:22", "Yuki", "你会知道的。"),
        ],
        choices=[
            Choice(1, "离开，去其他地点", "c2a_paid"),
        ],
        hint="[HINT] 已获得：大红按钮",
    )

    scenes["c2a_nagato_take_both"] = Scene(
        id="c2a_nagato_take_both",
        grant_items=["普通的灯带", "大红按钮"],
        set_time="11:10:00 JST",
        entries=[
            _n("11:05:00", "你把灯带和大红按钮都收进背包。"),
            _s("11:05:05", "ITEM_ACQUIRED: 普通的灯带", "success"),
            _s("11:05:06", "ITEM_ACQUIRED: 大红按钮",   "success"),
            _d("11:05:10", "Kyon",
               "合理分配背包空间是在 SOS 团生存的必要技能。"),
            _d("11:05:13", "Yuki",
               "……按下它的时机很重要。"),
            _d("11:05:16", "Kyon", "你说的是灯带还是按钮？"),
            _d("11:05:18", "Yuki", "……两者都是。"),
        ],
        choices=[
            Choice(1, "离开，去其他地点", "c2a_paid"),
        ],
        hint="[HINT] 已获得两件物品",
    )

    # ── 学校天台 ──────────────────────────────────────────────────────────────
    scenes["c2a_rooftop"] = Scene(
        id="c2a_rooftop",
        set_location="Rooftop", set_time="15:00:00 JST",
        entries=[
            _n("15:00:00", "北高学校天台。"),
            _n("15:00:10",
               "古泉一树正在天台中央用瓦楞纸箱和胶带搭建某种结构——它的轮廓模糊地像一个圆形。"),
            _d("15:00:18", "Kyon", "这是……UFO？"),
            _d("15:00:21", "Koizumi",
               "凉宫同学的设计图要求圆形，会飞，能发光。"),
            _d("15:00:24", "Koizumi",
               "目前只实现了圆形，另外两项正在努力中。"),
            _d("15:00:27", "Kyon",
               "如果我现在从天台边缘往外看，能看到外星人的样子。"),
            _sep(),
            _n("15:10:00", "古泉从模型旁边的纸箱里拿出一卷普通的风筝线。"),
            _d("15:10:05", "Koizumi",
               "我在找能让模型\"飞起来\"的方法。风筝线配合天台横梁，"
               "应该可以制造出被牵引的效果。"),
            _d("15:10:12", "Kyon",
               "这需要相当精准的操作才能看起来不像一个挂在绳子上的纸箱。"),
            _d("15:10:16", "Koizumi",
               "是的。这正是我需要一个人在旁边协助拉绳的原因。"),
            _d("15:10:20", "Kyon",
               "……你为什么用这种眼神看我？"),
        ],
        choices=[
            Choice(1, "拿走风筝线（获得：普通的风筝线）", "c2a_rooftop_take"),
            Choice(2, "先观察古泉的施工进度",             "c2a_rooftop_watch"),
        ],
        hint="[HINT] 天台有风筝线，也有古泉",
        commands=[Command("inventory", "查看背包", "inventory")],
    )

    scenes["c2a_rooftop_watch"] = Scene(
        id="c2a_rooftop_watch",
        set_time="15:20:00 JST",
        entries=[
            _n("15:15:00",
               "你在天台旁边站了十分钟，看古泉用胶带把一段段瓦楞纸拼接在一起。"),
            _d("15:15:10", "Kyon",
               "客观地说，如果不知道这是飞碟模型，你会怎么形容它？"),
            _d("15:15:13", "Koizumi",
               "大型废品回收站的一日作品展。"),
            _d("15:15:16", "Kyon",
               "你的审美还活着，令人欣慰。"),
            _d("15:15:19", "Koizumi",
               "但凉宫同学的热情也是真实的，这让事情变得有意义——"
               "即使意义的形式非常特殊。"),
            _d("15:15:25", "Kyon", "你真的这么觉得？"),
            _d("15:15:28", "Koizumi", "……大概。当你见过足够多的\"奇迹\"，你会开始尊重每一种制造奇迹的尝试。"),
        ],
        choices=[
            Choice(1, "拿走风筝线（获得：普通的风筝线）", "c2a_rooftop_take"),
        ],
        hint="[HINT] 古泉说了一些让人意外的话",
    )

    scenes["c2a_rooftop_take"] = Scene(
        id="c2a_rooftop_take",
        grant_items=["普通的风筝线"],
        set_time="15:25:00 JST",
        entries=[
            _n("15:25:00", "你拿起那卷风筝线。"),
            _s("15:25:05", "ITEM_ACQUIRED: 普通的风筝线", "success"),
            _d("15:25:10", "Kyon",
               "风筝线比想象的轻。比想象的细。"),
            _d("15:25:13", "Kyon",
               "但目前来说，它是让这个瓦楞纸飞碟\"离地\"的唯一方案。"),
        ],
        choices=[
            Choice(1, "去其他地点", "c2a_paid"),
            Choice(2, "直接前往 Chapter 3 验收",
                   "c3a_rooftop_final",
                   requires_flag=None,
                   requires_item=None),
        ],
        hint="[HINT] 已获得：普通的风筝线",
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 2B — 轮回后咖啡厅 + 智能地图
# ─────────────────────────────────────────────────────────────────────────────

def _ch2b() -> dict[str, Scene]:
    scenes = {}

    scenes["c2b_cafe"] = Scene(
        id="c2b_cafe",
        set_location="Cafe", set_time="09:10:14 JST",
        entries=[
            _n("09:10:14", "站前咖啡厅。"),
            _n("09:10:15", "门铃声响起。"),
            _d("09:10:17", "Kyon",
               "接下来我会看到 SOS 团坐在最显眼的位置。"),
            _n("09:10:18", "SOS 团坐在最显眼的位置。"),
            _d("09:10:22", "Kyon",
               "然后春日面前会有几张打印纸。"),
            _n("09:10:25",
               "春日面前摊着几张打印纸，上面密密麻麻标着红圈、箭头和几个非常不可信的英文单词。"),
            _d("09:10:28", "Kyon",
               "很好。我的人生正在向一种极其不健康的预言能力发展。"),
            _d("09:10:32", "Haruhi", "阿虚！你在门口嘀咕什么？"),
            _d("09:10:35", "Kyon",
               "我在确认这个世界是不是偷懒到连咖啡厅座位都不重新安排。"),
            _d("09:10:38", "Haruhi", "你睡糊涂了吧？"),
            _d("09:10:40", "Kyon",
               "如果只有我一个人这么觉得，那确实很像睡糊涂了。"),
            _sep(),
            _n("09:10:45", "长门抬头看了你一眼。"),
            _d("09:10:47", "Yuki", "误差已出现。", "glitch"),
            _d("09:10:50", "Kyon", "什么误差？"),
            _d("09:10:52", "Yuki", "记忆残留。", "glitch"),
            _d("09:10:55", "Kyon",
               "长门，你能不能把这种让人背后发凉的话放在更适合的场合说？"),
            _d("09:10:58", "Haruhi",
               "你们两个在说什么悄悄话？现在是作战会议时间！"),
            _sep(),
            _n("09:12:00", "春日双手重重拍在桌子上。"),
            _d("09:12:03", "Haruhi",
               "各位！在这个无聊的黄金周，我决定了！"),
            _d("09:12:06", "Haruhi",
               "我们要建造一个 UFO，召唤真正的外星人！"),
            _d("09:12:09", "Kyon", "我就知道。"),
            _d("09:12:11", "Haruhi", "什么你就知道？"),
            _d("09:12:13", "Kyon", "没什么。只是觉得宇宙缺乏创意。"),
            _d("09:12:16", "Haruhi",
               "错！宇宙非常有创意，只是大多数人没有发现它！"),
            _d("09:12:20", "Koizumi",
               "原来如此，非常有凉宫同学风格的计划。"),
            _d("09:12:23", "Kyon",
               "古泉，连你的反应都一字不差地让人安心又绝望。"),
            _sep(),
            _d("09:12:30", "Haruhi",
               "至于阿虚，你负责买单，然后自由活动！不要偷懒！"),
            _sep(),
            _n("09:39:40", "长门说完后，像什么都没发生一样合上书。"),
            _d("09:39:42", "Yuki", "时间与地点。", "glitch_heavy"),
            _d("09:39:45", "Kyon", "什么？"),
            _d("09:39:47", "Yuki",
               "不同结果取决于时间与地点。", "glitch"),
            _sep(),
            _n("09:39:50",
               "SOS 团成员以同样不符合咖啡厅礼仪的速度离席。"),
            _n("09:40:00", "桌上再次只剩下一张五人份的账单。"),
            _d("09:40:05", "Kyon",
               "连账单都这么准时，真是令人讨厌的稳定性。"),
        ],
        choices=[
            Choice(1, "熟练地拿起账单",               "c2b_paid"),
            Choice(2, "即使知道没用，也再次抗议",     "c2b_protest"),
            Choice(3, "输入状态指令，确认既视感",     "c2b_status"),
        ],
        hint="[HINT] 时间与地点——长门的提示",
        commands=[Command("status", "状态确认", "status")],
    )

    scenes["c2b_status"] = Scene(
        id="c2b_status",
        set_time="09:40:05 JST",
        entries=[
            _s("09:40:05", "INPUT: root@sos-brigade:/home/kyon# Status", "cursor_fast"),
            _s("09:40:06", "STATUS_CHECK_RUNNING...", "typewriter_slow"),
            _sep(),
            _s("??:??:??", "Kyon.status = {",                           "instant"),
            _s("??:??:??", "  caffeine:   unavailable,",                "typewriter_fast"),
            _s("??:??:??", "  wallet:     critically_endangered,",      "typewriter_fast"),
            _s("??:??:??", "  deja_vu:    increasing,",                 "typewriter_fast"),
            _s("??:??:??", "  useful_hint: \"time and location\"",      "typewriter_fast"),
            _s("??:??:??", "}",                                          "instant"),
            _sep(),
            _d("09:40:10", "Kyon", "连我的状态栏都开始说谜语。"),
            _s("09:40:12", "System_Log > 观测建议：同一地点，不同时间。", "glitch"),
            _d("09:40:15", "Kyon",
               "这句倒是比长门刚才说得稍微像人话一点。"),
        ],
        choices=[Choice(1, "买单", "c2b_paid")],
        hint="[HINT] 同一地点，不同时间是关键",
    )

    scenes["c2b_protest"] = Scene(
        id="c2b_protest",
        set_time="09:40:10 JST",
        entries=[
            _d("09:40:10", "Kyon",
               "我知道接下来会发生什么。"),
            _d("09:40:13", "Kyon",
               "我会抗议，店员会微笑，账单会向我移动三厘米，最后还是我付钱。"),
            _n("09:40:20",
               "店员保持着职业微笑，把账单向你面前推近了三厘米。"),
            _n("09:40:35", "账单金额没有变化。"),
            _d("09:40:38", "Kyon",
               "好吧。至少这次我有心理准备。"),
            _d("09:40:41", "Kyon",
               "虽然心理准备并不能让钱包变厚。"),
        ],
        choices=[Choice(1, "买单", "c2b_paid")],
        hint="[HINT] 记忆没能改变账单金额",
    )

    scenes["c2b_paid"] = Scene(
        id="c2b_paid",
        set_time="09:42:00 JST",
        entries=[
            _s("09:42:00", "PAYMENT_STATUS: completed"),
            _s("09:42:01", "WALLET_DAMAGE: fatal_but_repeatable", "warning"),
            _sep(),
            _d("09:42:05", "Kyon",
               "\"可重复发生的致命损伤\"这种描述，不应该用于钱包。"),
            _sep(),
            _s("09:45:00", "System_Log > Terminal Mission 已启动。", "success"),
            _s("09:45:01", "System_Log > 地点移动权限已开放。"),
            _s("09:45:02", "System_Log > 可使用命令：Go, Help, Status, Inventory"),
            _s("09:45:03",
               "System_Log > 观测建议：同一地点，不同时间。", "glitch"),
            _s("09:45:04",
               "System_Log > 普通物品并不会自动变成关键物品。", "warning"),
            _sep(),
            _s("09:45:05", "LOCATION_LIST:"),
            _s("09:45:06", "  [A] Street       — 大街（重访）"),
            _s("09:45:07", "  [B] Store        — 便利店（重访）"),
            _s("09:45:08", "  [C] Nagato_Apt   — 长门公寓（重访）"),
            _s("09:45:09", "  [D] Rooftop      — 学校天台（重访）"),
            _sep(),
            _d("09:45:15", "Kyon",
               "\"同一地点，不同时间\"。"),
            _d("09:45:18", "Kyon",
               "翻译过来大概是：先去把能拿的都拿一遍，然后挑对的时间再回去一次。"),
        ],
        choices=[
            Choice(1, "去 Store — 便利店（早访）",     "c2b_store_early"),
            Choice(2, "去 Nagato_Apt — 长门公寓",      "c2b_nagato"),
            Choice(3, "去 Rooftop — 学校天台（早访）", "c2b_rooftop_early"),
            Choice(4, "去 Street — 大街",              "c2b_street"),
        ],
        hint="[HINT] 注意：同一地点早晚去，获得不同物品",
        commands=[
            Command("status",    "查看状态", "status"),
            Command("inventory", "查看背包", "inventory"),
        ],
    )

    # ── 轮回后大街 ────────────────────────────────────────────────────────────
    scenes["c2b_street"] = Scene(
        id="c2b_street",
        set_location="Street", set_time="10:00:00 JST",
        entries=[
            _n("10:00:00",
               "商业街。同样的人流，同样的摊位，同样的春日正在用放大镜研究电线杆。"),
            _d("10:00:10", "Haruhi",
               "阿虚！你看！这上面有符号！"),
            _d("10:00:13", "Kyon",
               "城管贴的拆迁公告残留胶带。"),
            _d("10:00:15", "Haruhi", "你……你怎么知道？"),
            _d("10:00:18", "Kyon",
               "直觉。"),
            _d("10:00:20", "Haruhi",
               "……阿虚你最近越来越奇怪。"),
            _d("10:00:23", "Kyon",
               "在 SOS 团里\"奇怪\"是一种竞争激烈的描述词，我排在哪里？"),
            _sep(),
            _n("10:05:00",
               "春日忽然停下来，盯着一家店铺的橱窗。"),
            _d("10:05:05", "Haruhi",
               "等等……阿虚，你看那个！"),
            _n("10:05:10",
               "橱窗里摆着一套看起来非常廉价但制作用心的外星生物玩偶服——"
               "橡胶面具、绿色身体、不成比例的大头，耳朵会自动弹起来。"),
            _d("10:05:18", "Haruhi",
               "！！！！这就是我们需要的东西！！！"),
            _d("10:05:21", "Kyon",
               "你原来的计划里没有\"真人扮外星人\"这个环节。"),
            _d("10:05:24", "Haruhi",
               "这才是点睛之笔！UFO 落地，外星人走出来——"
               "谁还会怀疑这不是真的外星人！"),
            _d("10:05:29", "Kyon",
               "所有见过外星人题材 B 级电影的人都会怀疑。"),
            _d("10:05:32", "Haruhi",
               "阿虚，你扮外星人！"),
            _d("10:05:34", "Kyon", "不要。"),
            _d("10:05:36", "Haruhi", "你一定能扮得很好！"),
            _d("10:05:38", "Kyon", "这两句话之间没有任何逻辑关系。"),
        ],
        choices=[
            Choice(1, "买下玩偶服（获得：玩偶服）",   "c2b_street_buy"),
            Choice(2, "坚决拒绝",                     "c2b_street_refuse"),
        ],
        hint="[HINT] 玩偶服是本轮回的关键道具之一",
    )

    scenes["c2b_street_refuse"] = Scene(
        id="c2b_street_refuse",
        set_time="10:10:00 JST",
        entries=[
            _d("10:10:00", "Kyon", "我不买。"),
            _d("10:10:02", "Haruhi", "阿虚！"),
            _d("10:10:04", "Kyon",
               "春日，我愿意搬纸箱，愿意贴胶带，愿意在天台上拉风筝线，"
               "但我不愿意穿那套东西。"),
            _d("10:10:10", "Haruhi",
               "……好吧。我尊重你最后一项反对意见。"),
            _d("10:10:13", "Kyon", "谢谢。"),
            _d("10:10:15", "Haruhi",
               "但你要想想，如果终端任务失败了是谁的锅。"),
            _d("10:10:18", "Kyon",
               "……"),
            _d("10:10:22", "Kyon",
               "我去买。"),
        ],
        choices=[
            Choice(1, "去买（获得：玩偶服）", "c2b_street_buy"),
        ],
        hint="[HINT] 拒绝无效",
    )

    scenes["c2b_street_buy"] = Scene(
        id="c2b_street_buy",
        grant_items=["玩偶服"],
        set_time="10:15:00 JST",
        entries=[
            _n("10:15:00", "你走进店里，买下了那套玩偶服。"),
            _s("10:15:05", "ITEM_ACQUIRED: 玩偶服", "success"),
            _d("10:15:10", "Kyon",
               "它比想象中重。橡胶的气味比想象中冲。"),
            _d("10:15:13", "Kyon",
               "耳朵真的会自动弹起来。我不知道这是设计亮点还是质检失误。"),
            _n("10:15:18",
               "春日接过购物袋，摸了摸玩偶耳朵，满意地点了点头。"),
            _d("10:15:22", "Haruhi",
               "完美。阿虚，等你穿上，外星人就会来的。"),
            _d("10:15:25", "Kyon",
               "如果真正的外星人看到这个会主动来，我对这个星系的审美标准深感忧虑。"),
        ],
        choices=[
            Choice(1, "去其他地点", "c2b_paid"),
        ],
        hint="[HINT] 已获得：玩偶服",
    )

    # ── 便利店（早访→普通贴纸，晚访→无新物品）────────────────────────────────
    scenes["c2b_store_early"] = Scene(
        id="c2b_store_early",
        set_location="Store", set_time="10:30:00 JST",
        grant_items=["普通的怪兽贴纸"],
        entries=[
            _n("10:30:00",
               "便利店。你熟练地走向文具区，拿起那包怪兽贴纸。"),
            _d("10:30:05", "Kyon",
               "这次我没有在货架旁边犹豫——上一次犹豫了三分钟才拿起它。"),
            _s("10:30:10", "ITEM_ACQUIRED: 普通的怪兽贴纸", "success"),
            _d("10:30:13", "Kyon",
               "现在我拥有了它，但我知道它贴上去之后边角会翘起来。"),
            _sep(),
            _s("10:30:18",
               "System_Log > 提示：同一地点，时间 ≥ 11:00 时可能有不同发现。",
               "glitch"),
        ],
        choices=[
            Choice(1, "继续去其他地点",          "c2b_paid"),
            Choice(2, "等到11点后再回来看看",    "c2b_store_late"),
        ],
        hint="[HINT] 普通贴纸已入手，但晚些回来会有不同发现",
    )

    scenes["c2b_store_late"] = Scene(
        id="c2b_store_late",
        set_location="Store", set_time="11:05:00 JST",
        entries=[
            _n("11:05:00",
               "你在咖啡厅等到十一点，再次走进便利店。"),
            _n("11:05:10",
               "文具区的货架旁边，一个穿着便利店制服的店员正在整理新到的货物。"),
            _n("11:05:15",
               "在他的货车上，放着一盒看起来相当复杂的\"超能力手办套件\"——"
               "里面有一个小型风扇、一根可以伸缩的透明杆和一组微型滑轮。"),
            _d("11:05:22", "Kyon",
               "……这不是应该放在玩具店的东西。"),
            _n("11:05:25",
               "你拿起盒子，翻过来——背面写着\"超能力飞行装置，用于模型和道具制作\"。"),
            _d("11:05:30", "Kyon",
               "古泉的滑轮组问题解决了。"),
        ],
        choices=[
            Choice(1, "买下超能力飞行装置（关键道具）", "c2b_store_buy_device"),
            Choice(2, "先放着，去别的地方",            "c2b_paid"),
        ],
        hint="[HINT] 关键道具！晚访才能获得",
    )

    scenes["c2b_store_buy_device"] = Scene(
        id="c2b_store_buy_device",
        grant_items=["超能力飞行装置"],
        set_time="11:10:00 JST",
        entries=[
            _n("11:10:00", "你把那套装置放进购物篮。"),
            _s("11:10:05", "ITEM_ACQUIRED: 超能力飞行装置", "success"),
            _d("11:10:10", "Kyon",
               "道具名称叫\"超能力飞行装置\"，实际上是一个工程模型套件。"),
            _d("11:10:13", "Kyon",
               "但放到天台上，配合古泉的滑轮组，它可能真的能让那个纸箱\"飞\"起来。"),
        ],
        choices=[Choice(1, "去其他地点", "c2b_paid")],
        hint="[HINT] 三件关键道具之一已获得",
    )

    # ── 长门公寓（轮回后，大红按钮已是真道具）──────────────────────────────────
    scenes["c2b_nagato"] = Scene(
        id="c2b_nagato",
        set_location="Nagato_Apt", set_time="11:40:00 JST",
        entries=[
            _n("11:40:00", "长门有希的公寓。第七百零八号房间。"),
            _n("11:40:10", "门铃按下去，三十秒后门开了。"),
            _d("11:40:42", "Yuki", "你来了。"),
            _d("11:40:45", "Kyon", "这句话比上次多了两个字。"),
            _d("11:40:48", "Yuki", "……上次？"),
            _d("11:40:51", "Kyon",
               "不，抱歉。总之春日让我来拿东西。"),
            _sep(),
            _n("11:41:00",
               "长门走到储物间，这次她拿出了一个更大的包裹。"),
            _n("11:41:10",
               "打开后，里面是灯带——但这卷灯带比上次的旧一些，连接处被重新焊接过，看起来更可靠。"),
            _d("11:41:18", "Yuki", "信号链路已更新。"),
            _d("11:41:21", "Kyon", "什么信号链路？"),
            _d("11:41:23", "Yuki",
               "广播部的校内广播，时间：17:02:00，持续五秒。"),
            _d("11:41:28", "Kyon",
               "你在安排什么？"),
            _d("11:41:31", "Yuki",
               "……奇迹需要声音。"),
            _sep(),
            _n("11:42:00",
               "她把大红按钮也递过来，按钮上的 Terminal Mission 字样在灯光下发着光。"),
            _d("11:42:05", "Kyon",
               "按下它的时机。你上次说\"你会知道的\"。"),
            _d("11:42:09", "Yuki", "17:02:00。"),
            _d("11:42:12", "Kyon",
               "精确到秒？"),
            _d("11:42:14", "Yuki", "……是的。"),
        ],
        choices=[
            Choice(1, "收下灯带和大红按钮", "c2b_nagato_take"),
        ],
        hint="[HINT] 长门给出了精确时间",
        commands=[Command("inventory", "查看背包", "inventory")],
    )

    scenes["c2b_nagato_take"] = Scene(
        id="c2b_nagato_take",
        grant_items=["普通的灯带", "大红按钮"],
        set_time="11:45:00 JST",
        entries=[
            _n("11:45:00", "你把灯带和大红按钮都收进背包。"),
            _s("11:45:05", "ITEM_ACQUIRED: 普通的灯带", "success"),
            _s("11:45:06", "ITEM_ACQUIRED: 大红按钮",   "success"),
            _d("11:45:10", "Kyon", "17:02:00。"),
            _d("11:45:13", "Kyon",
               "长门交代任务的方式永远是这样——你知道它是重要的，但需要自己拼出意义。"),
            _sep(),
            _d("11:45:18", "Yuki", "……还有一件事。"),
            _d("11:45:21", "Kyon", "什么？"),
            _d("11:45:23", "Yuki",
               "天台横梁。15:25 之前，需要有人去安装滑轮组。"),
            _d("11:45:28", "Kyon",
               "你是在告诉我，我需要在天台那边做一件具体的事。"),
            _d("11:45:32", "Yuki",
               "……是的。"),
        ],
        choices=[
            Choice(1, "去 Rooftop — 学校天台（安装滑轮组）", "c2b_rooftop_early"),
            Choice(2, "先去其他地点",                       "c2b_paid"),
        ],
        hint="[HINT] 长门提示：天台，15:25前",
    )

    # ── 天台（早访→安装滑轮，晚访→完成准备）─────────────────────────────────────
    scenes["c2b_rooftop_early"] = Scene(
        id="c2b_rooftop_early",
        set_location="Rooftop", set_time="15:00:00 JST",
        grant_items=["普通的风筝线"],
        entries=[
            _n("15:00:00", "学校天台。"),
            _n("15:00:10",
               "古泉站在已经被擦过一遍的瓦楞纸 UFO 旁边，连胶带的反光都被藏进缝隙。"),
            _d("15:00:18", "Koizumi",
               "你来了。我已经等你有一会儿了。"),
            _d("15:00:21", "Kyon",
               "你知道我会来？"),
            _d("15:00:24", "Koizumi",
               "……我们对\"已经发生的事\"都有一种奇怪的预感。"),
            _sep(),
            _n("15:05:00",
               "你帮古泉在天台横梁上安装好滑轮组。风筝线顺着滑轮通向模型顶部，"
               "连接处被白色胶带仔细绕了三圈。"),
            _s("15:05:05", "ITEM_ACQUIRED: 普通的风筝线", "success"),
            _sep(),
            _d("15:05:10", "Koizumi",
               "横梁那边已经接好。广播部测试 ok。"),
            _d("15:05:13", "Kyon", "你们连广播都安排上了？"),
            _d("15:05:16", "Koizumi",
               "凉宫同学说过：演出需要音效。我只是想办法实现了她的要求。"),
            _d("15:05:20", "Kyon",
               "古泉，你在这件事里比你表现出来的更认真。"),
            _d("15:05:24", "Koizumi",
               "……也许是的。当奇迹真的有可能发生时，我不希望因为我的懈怠而错过它。"),
        ],
        choices=[
            Choice(1, "继续等到下午验收时间", "c2b_rooftop_late"),
            Choice(2, "先去确认其他道具",    "c2b_paid"),
        ],
        hint="[HINT] 已获得：普通的风筝线，滑轮组已安装",
    )

    scenes["c2b_rooftop_late"] = Scene(
        id="c2b_rooftop_late",
        set_location="Rooftop", set_time="16:00:00 JST",
        set_flags={"rooftop_ready": True},
        entries=[
            _n("16:00:00", "你在天台等到了下午四点。"),
            _n("16:00:10",
               "朝比奈实玖瑠从天台储物间探出半个身子，"
               "抱着一件比她大整整一圈的玩偶服，像在抱一只被晒化了的橡胶卡通玩偶。"),
            _d("16:00:18", "Mikuru",
               "阿虚同学，玩偶服……我已经尽力压平了……"),
            _d("16:00:22", "Mikuru",
               "但是它的耳朵无论怎么按都会弹起来。"),
            _d("16:00:26", "Kyon",
               "学姐，外星人耳朵会自己弹起来这件事，今天先不深究。"),
            _sep(),
            _n("16:00:30",
               "长门坐在天台栏杆边，膝上放着写着 Terminal Mission 的遥控器。"),
            _d("16:00:35", "Yuki",
               "信号链路稳定。"),
            _d("16:00:37", "Yuki", "按下时间：17:02:00。"),
            _sep(),
            _s("16:00:40",
               "System_Log > 道具确认：请检查 Inventory", "cursor_fast"),
        ],
        choices=[
            Choice(1, "确认所有道具，前往最终验收", "c4b_final",
                   requires_flag="rooftop_ready"),
        ],
        hint="[HINT] 确认持有：玩偶服、大红按钮、超能力飞行装置",
        commands=[Command("inventory", "查看背包", "inventory")],
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 3A — 第一次未轮回：道具链
# (便利店→长门→天台，收集三件普通物品)
# ─────────────────────────────────────────────────────────────────────────────
# Chapter 3 leverages chapter 2 scenes for exploration;
# it adds the "all items collected → proceed" gate.

def _ch3a() -> dict[str, Scene]:
    scenes = {}

    # 当三件普通物品都收集完毕时，触发此场景
    scenes["c3a_items_ready"] = Scene(
        id="c3a_items_ready",
        set_time="15:30:00 JST",
        entries=[
            _sep(),
            _s("15:30:00",
               "System_Log > 物品确认完毕：普通的怪兽贴纸 / 普通的灯带 / 普通的风筝线",
               "success"),
            _s("15:30:02",
               "System_Log > 所有 Terminal Mission 道具已就位。"),
            _sep(),
            _d("15:30:10", "Kyon",
               "三件东西放在一起，比分开放的时候更像\"一套\"。"),
            _d("15:30:13", "Kyon",
               "虽然\"一套\"的具体定义在 SOS 团标准里相当模糊。"),
            _d("15:30:17", "Kyon",
               "但好歹——这是一次真诚的尝试。"),
        ],
        choices=[
            Choice(1, "前往天台：执行第一次验收", "c4a_final"),
        ],
        hint="[HINT] 第一章道具链完成，准备验收",
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 4A — 第一次未轮回：天台验收 → 失败 → 轮回
# ─────────────────────────────────────────────────────────────────────────────

def _ch4a() -> dict[str, Scene]:
    scenes = {}

    scenes["c4a_final"] = Scene(
        id="c4a_final",
        set_location="Rooftop", set_time="16:30:00 JST",
        entries=[
            _n("16:30:00", "学校天台。"),
            _n("16:30:05",
               "古泉一树站在用废旧瓦楞纸拼凑成的\"UFO\"旁，挂着一如既往稳定的微笑。"),
            _n("16:30:10",
               "模型勉强呈圆形，边缘还有几处胶带反光。"
               "从两米外看，它像被弃置的搬家用包装；"
               "从十米外看，它依然是被弃置的搬家用包装。"),
            _d("16:30:18", "Kyon", "这叫哪门子 UFO？"),
            _d("16:30:21", "Koizumi",
               "如果从未知飞行物的定义出发，只要无法准确识别，它就可以被称为 UFO。"),
            _d("16:30:25", "Kyon", "我可以非常准确地识别。"),
            _d("16:30:27", "Kyon", "它是纸箱。"),
            _sep(),
            _n("16:35:00",
               "你按春日的\"作战指南\"把普通物品依次安装到模型上。"),
            _n("16:35:05",
               "普通灯带被胶带粘在边缘，只有半数 LED 还能亮。"),
            _n("16:35:10",
               "普通怪兽贴纸贴在侧面，刚一贴上，边角就开始翘起。"),
            _n("16:35:15",
               "普通风筝线一端绑在顶部，另一端被古泉拿在手里。"),
            _sep(),
            _d("16:35:20", "Kyon",
               "客观地说，所有要求的元件都被安装到位。"),
            _d("16:35:23", "Kyon",
               "主观地说，我从来没见过这么不像 UFO 的 UFO。"),
            _sep(),
            _n("17:00:00",
               "凉宫春日带着实玖瑠和长门走上天台。她的步伐比早上更有压迫感。"),
            _d("17:00:05", "Haruhi", "模型呢？灯呢？飞行呢？"),
            _d("17:00:08", "Koizumi", "已经全部就位。"),
            _d("17:00:10", "Haruhi", "那就开始演出！"),
            _sep(),
            _n("17:02:00", "古泉合上灯带的电源开关。"),
            _n("17:02:02", "灯带闪了两下。"),
            _n("17:02:03",
               "一半的 LED 灭掉，剩下的另一半亮度像便利店打烊前的招牌。"),
            _sep(),
            _n("17:02:30", "古泉用力拉动风筝线。纸箱的一端歪歪扭扭地翘起来。"),
            _n("17:02:35",
               "一阵风过来，整个 UFO 被抬起的角度还不如运动会上一面斜挂的旗子。"),
            _sep(),
            _d("17:02:40", "Mikuru",
               "凉、凉宫同学，大家已经……尽力了……"),
            _d("17:02:45", "Haruhi", "……太普通了。", "typewriter_slow"),
            _d("17:02:50", "Haruhi",
               "一点都不像会让外星人出现的东西。"),
            _sep(),
            _n("17:10:00",
               "春日走到模型前，烦躁地踢了一脚。模型边上的灯带啪一声折断。"),
            _n("17:10:02",
               "怪兽贴纸的最后一只触角脱落，被风带到栏杆外。"),
            _sep(),
            _s("17:10:05", "WORLDLINE_SHIFT: unstable", "worldline_shift"),
            _sep(),
            _d("17:10:10", "Kyon",
               "我有一种不祥的预感。"),
            _d("17:10:14", "Kyon",
               "而且这次的不祥，似乎不是平时那种\"春日又要折腾人\"的级别。"),
            _sep(),
            _n("17:10:30",
               "天台的光线慢慢退色。日历上的 5/2 这个数字开始变得不太确定。",
               "typewriter_slow"),
        ],
        choices=[],
        triggers_loop_reset=True,
        hint="[HINT] 世界线不稳定……",
    )

    # 轮回触发后的过渡场景
    scenes["c4a_loop_start"] = Scene(
        id="c4a_loop_start",
        set_time="17:30:00 JST",
        set_worldline="??:??:??[SHIFTING···]",
        entries=[
            _sep(),
            _s("17:30:00", "WORLDLINE_SHIFT: CRITICAL", "worldline_shift"),
            _s("17:30:01", "LOOP_COUNT: +1",              "glitch_heavy"),
            _s("17:30:02", "RESETTING DATE: 05/02...",    "glitch"),
            _sep(),
            _d("17:30:10", "Kyon",
               "……等一下。",
               "typewriter_slow"),
            _d("17:30:15", "Kyon",
               "这种感觉……",
               "typewriter_slow"),
            _n("17:30:20",
               "意识在黑暗里停留了某个不可测量的时间段。",
               "typewriter_slow"),
            _n("17:30:25",
               "然后一切重新开始。",
               "typewriter_slow"),
        ],
        choices=[],
        triggers_loop_reset=True,
        hint="",
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER 4B — 轮回后：最终验收 + 两个结局
# ─────────────────────────────────────────────────────────────────────────────

def _ch4b() -> dict[str, Scene]:
    scenes = {}

    # ── 轮回后最终验收 ────────────────────────────────────────────────────────
    scenes["c4b_final"] = Scene(
        id="c4b_final",
        set_location="Rooftop", set_time="16:30:00 JST",
        entries=[
            _n("16:30:00", "学校天台。"),
            _n("16:30:05",
               "同一个瓦楞纸 UFO 模型，但它已经被人用心擦了一遍，"
               "连胶带的反光都被尽量藏到了缝隙里。"),
            _n("16:30:10",
               "横梁上多出一组小巧的滑轮组。风筝线顺着滑轮通向模型顶部，"
               "连接处被白色胶带仔细绕了三圈。"),
            _sep(),
            _n("16:30:30", "古泉调整完最后一段风筝线，转过头来。"),
            _d("16:30:33", "Koizumi",
               "横梁那边已经接好。广播部测试 ok。"),
            _sep(),
            _n("16:31:00",
               "长门坐在天台栏杆边，膝上放着写着 Terminal Mission 的遥控器。"),
            _n("16:31:05",
               "她没有看你。但你站到她两步以内时，"
               "她递过来的手已经准确停在你的右手边。"),
            _d("16:31:08", "Yuki", "信号链路稳定。"),
            _d("16:31:10", "Yuki", "按下时间：17:02:00。"),
            _sep(),
            _n("16:31:30",
               "朝比奈实玖瑠从天台储物间探出半个身子。"),
            _n("16:31:35",
               "她抱着一件比她大整整一圈的玩偶服，"
               "像在抱一只被晒化了的橡胶卡通玩偶。"),
            _d("16:31:40", "Mikuru",
               "阿虚同学，玩偶服……我已经尽力压平了……"),
            _d("16:31:44", "Mikuru",
               "但是它的耳朵无论怎么按都会弹起来。"),
            _d("16:31:48", "Kyon",
               "学姐，外星人耳朵会自己弹起来这件事，今天先不深究。"),
            _sep(),
            _n("16:55:00", "你把三件关键物品摊在面前。"),
            _n("16:55:05", "玩偶服、大红按钮、超能力飞行装置。"),
            _n("16:55:10",
               "这三个词单独拿出来都荒诞，放在一起，反而像一份完整的演出剧本。"),
            _d("16:55:18", "Kyon",
               "第一次的天台上，这里只有纸箱、灯带、贴纸和风筝线。"),
            _d("16:55:22", "Kyon",
               "同样是这堆东西，今天看上去居然像是真的能飞起来。"),
            _sep(),
            _n("17:01:00",
               "时钟的秒针走过整数。春日马上就要进来了。",
               "typewriter_slow"),
            _d("17:01:05", "Kyon",
               "这是你说过的最后一个时间窗口。",
               "typewriter_slow"),
            _d("17:01:10", "Kyon",
               "错过这一次，下一次就要从被窝里重新开始。",
               "typewriter_slow"),
        ],
        choices=[
            Choice(1, "站着不动", "c4b_ending_normal"),
            Choice(2, "执行终端任务", "c4b_ending_true"),
        ],
        hint="[HINT] 这是最后的时间窗口",
        commands=[Command("inventory", "最后确认背包", "inventory")],
    )

    # ── 结局A：普通轮回 ───────────────────────────────────────────────────────
    scenes["c4b_ending_normal"] = Scene(
        id="c4b_ending_normal",
        set_time="17:01:30 JST",
        entries=[
            _n("17:01:30", "你站在那里，没有动。", "typewriter_slow"),
            _sep(),
            _d("17:01:35", "Kyon",
               "也许下一次吧。",
               "typewriter_slow"),
            _d("17:01:40", "Kyon",
               "也许下一次，一切会更顺一点。",
               "typewriter_slow"),
            _sep(),
            _n("17:02:00",
               "春日推门走上天台。她看了看 UFO，看了看大家，然后看了看站在原地的你。",
               "typewriter_slow"),
            _d("17:02:10", "Haruhi",
               "阿虚，你在发什么呆？",
               "typewriter_slow"),
            _d("17:02:13", "Kyon",
               "没什么。",
               "typewriter_slow"),
            _sep(),
            _n("17:10:00",
               "演出平静地结束了。比第一次更平静，也更没有结果。",
               "typewriter_slow"),
            _n("17:10:10",
               "世界线在安静里变得模糊。",
               "typewriter_slow"),
            _sep(),
            _s("17:10:15", "WORLDLINE_SHIFT: unstable", "worldline_shift"),
            _s("17:10:16", "LOOP_COUNT: +1",            "glitch_heavy"),
        ],
        choices=[
            Choice(1, "等待 Next Day……", "c4a_loop_start"),
        ],
        triggers_loop_reset=True,
        hint="[HINT] 也许下次……",
    )

    # ── 结局B：执行终端任务（真结局）────────────────────────────────────────────
    scenes["c4b_ending_true"] = Scene(
        id="c4b_ending_true",
        set_time="17:01:30 JST",
        set_worldline=WORLDLINE_STABLE,
        entries=[
            _n("17:01:30", "你转身躲到天台储物间后面。"),
            _n("17:01:40",
               "朝比奈学姐把玩偶服递过来，又用力把它往你身上塞。"),
            _d("17:01:44", "Mikuru", "阿、阿虚同学，加油……"),
            _d("17:01:47", "Kyon",
               "学姐，\"加油\这个词在这件衣服面前是完全无效的。"),
            _sep(),
            _n("17:01:50",
               "玩偶服比想象中还要闷热。橡胶味、汗味、和某种说不清的"
               "\"廉价道具仓库味\"在头盔里同时存在。"),
            _d("17:01:55", "Kyon",
               "这件衣服设计的时候，有没有为人体生理需求做过任何让步？"),
            _sep(),
            _n("17:01:58",
               "你把头盔扣紧。视野透过两个被涂了眼影的圆孔，"
               "正对着天台中央的 UFO。"),
            _sep(),
            _n("17:02:00",
               "长门按下手里遥控器上的预备键。",
               "typewriter_slow"),
            _n("17:02:01",
               "瓦楞纸 UFO 边缘的灯带瞬间泛起均匀的红色光晕，"
               "连胶带的反光都被掩盖在光里。",
               "typewriter_slow"),
            _n("17:02:05",
               "校园广播插播的那段五秒\"奇怪音效\"恰好同时响起。"
               "它听起来介于汽车点火和老式打印机之间，"
               "但配合在这一刻，居然让\"飞碟逼近\"四个字在脑子里自动浮现。",
               "typewriter_slow"),
            _sep(),
            _d("17:02:08", "Haruhi",
               "这是……？",
               "typewriter_slow"),
            _sep(),
            _n("17:02:10", "你按下大红按钮，从储物间冲出。"),
            _n("17:02:11", "古泉同时收紧横梁上的滑轮组。"),
            _n("17:02:13",
               "瓦楞纸 UFO 缓缓离开地面，被风筝线拉成一种\"它自己飞起来了\"的姿态。"),
            _n("17:02:15", "你站在 UFO 下方，玩偶服里满是汗水。"),
            _sep(),
            _d("17:02:20", "Kyon",
               "愚——蠢的——地球人啊——！", speed=1.6),
            _sep(),
            _n("17:02:23",
               "你抬起一只手，做出在玩偶服里找了三秒才找到合适角度的手势。"),
            _n("17:02:24", "玩偶服的脚太长。"),
            _n("17:02:25", "你踩到了自己的尾巴。", "typewriter_slow"),
            _n("17:02:26", "你重重地扑倒在地。", "typewriter_slow"),
            _n("17:02:27",
               "外星人头盔顺着惯性滚出去，在天台地面弹了两下。",
               "typewriter_slow"),
            _n("17:02:28",
               "头盔停在凉宫春日推开门进来的脚边。",
               "typewriter_slow"),
            _sep(),
            _d("17:02:30", "Haruhi", "噗……", "typewriter_slow"),
            _d("17:02:32", "Haruhi",
               "哈哈哈哈哈哈哈哈！", speed=0.7),
            _d("17:02:34", "Haruhi",
               "阿虚！你在搞什么啊！！", speed=0.8),
            _sep(),
            _n("17:03:00",
               "凉宫春日笑到弯下腰，扶着膝盖。她已经很久没有这样毫不掩饰地笑过了。"),
            _d("17:03:10", "Kyon",
               "我从地面上抬起头，看着她笑成那个样子。"),
            _d("17:03:15", "Kyon",
               "第一次觉得\"被她笑成这样\"，也不是什么不能接受的结局。",
               "typewriter_slow"),
            _sep(),
            _n("17:04:30",
               "古泉松开滑轮组。瓦楞纸 UFO 慢慢落回原位，像演出谢幕。"),
            _n("17:04:50",
               "朝比奈学姐从储物间探出头，看见地上的你和你身上半挂着的玩偶服，"
               "安心地呼了一口气。"),
            _d("17:04:55", "Mikuru",
               "太、太好了……"),
            _d("17:04:57", "Mikuru",
               "没有受伤的话就好……"),
            _sep(),
            _n("17:05:00", "长门把手里的遥控器关上。"),
            _n("17:05:05",
               "红色按钮上 Terminal Mission 的字样慢慢褪回成普通的红漆。"),
            _d("17:05:08", "Yuki", "终端任务完成。", "typewriter_slow"),
            _sep(),
            _n("17:05:10",
               "春日把外星人头盔捡起来，看了一会儿，然后把它扣回你的脑袋。"),
            _d("17:05:15", "Haruhi",
               "阿虚，下次再办类似的活动，你还要扮外星人。"),
            _d("17:05:18", "Kyon", "这件事不是应该轮换的吗？"),
            _d("17:05:21", "Haruhi",
               "因为你扮得最像一个\"明知道会摔倒还要冲出来\"的外星人。"),
            _d("17:05:25", "Haruhi",
               "这种角色不是谁都能演的。"),
            _d("17:05:28", "Kyon",
               "这句话听起来像是表扬，但我一点也不觉得自己被夸了。",
               "typewriter_slow"),
            _sep(),
            _s("17:30:00", "WORLDLINE_SHIFT: stable",  "worldline_shift"),
            _s("17:30:01", "DATE_UNLOCKED: 05/03",      "success"),
            _sep(),
            _d("17:30:10", "Kyon",
               "看着满头大汗、满身尘土、半个外星人皮套挂在地上的自己，我只好叹了口气。",
               "typewriter_slow"),
            _d("17:30:15", "Kyon",
               "凉宫春日真是一个恶劣的女人。",
               "typewriter_slow"),
            _d("17:30:20", "Kyon",
               "但今天的黄金周，确实已经不再是普通的黄金周了。",
               "typewriter_slow"),
            _sep(),
            _s("17:30:25",
               "════════════════════════════════════════", "instant"),
            _s("17:30:26",
               "         Terminal Mission — COMPLETE       ", "success"),
            _s("17:30:27",
               "════════════════════════════════════════", "instant"),
        ],
        choices=[
            Choice(1, "【TRUE END】重新体验这个故事", "c1a_morning_call"),
        ],
        hint="[HINT] 世界线已稳定。05/03 解锁。",
        set_flags={"true_end": True},
    )

    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# Master build function
# ─────────────────────────────────────────────────────────────────────────────

def build_scenario() -> dict[str, Scene]:
    all_scenes: dict[str, Scene] = {}
    for builder in [_ch1a, _ch1b, _ch2a, _ch2b, _ch3a, _ch4a, _ch4b]:
        all_scenes.update(builder())
    return all_scenes


# ─────────────────────────────────────────────────────────────────────────────
# Command side-effect responses
# ─────────────────────────────────────────────────────────────────────────────

def get_command_response(cmd: str, scene_id: str,
                         inventory: set[str], loop_count: int,
                         flags: dict[str, bool]) -> list[LogEntry]:
    """Return log entries for a typed command."""

    def sys(text, effect="typewriter_fast"):
        return LogEntry("??:??:??", "system", None, text, effect, 0.6)

    def npc(ts, speaker, text):
        return LogEntry(ts, "dialogue", speaker, text, "typewriter", 1.0)

    def err(text):
        return LogEntry("??:??:??", "error", None, text, "typewriter_fast", 0.6)

    c = cmd.strip().lower()

    # ── help ──────────────────────────────────────────────────────────────────
    if c == "help":
        return [
            sys(">> help"),
            sys("  可用指令:"),
            sys("  status    — 查看当前精神状态"),
            sys("  inventory — 查看背包物品"),
            sys("  ls        — 扫描当前区域"),
            sys("  date      — 查看世界线信息"),
            sys("  scan      — 扫描实体（需指定目标）"),
            sys("  read      — 读取物品/文本"),
            sys("  map       — 查看地图"),
            sys("  history   — 查看本次轮回选择记录"),
            sys("  help      — 显示此帮助"),
            sys("  输入数字选择剧情选项。"),
        ]

    # ── status ─────────────────────────────────────────────────────────────────
    if c in ("status", "st"):
        loop_str = str(loop_count) if loop_count < 5 else f"{loop_count} [CRITICAL]"
        deja_str = "none" if loop_count == 0 else (
            "mild" if loop_count == 1 else "overwhelming"
        )
        return [
            sys(">> Status", "cursor_fast"),
            sys("STATUS_CHECK_RUNNING...", "typewriter_slow"),
            LogEntry("??:??:??", "system", None, "Kyon.status = {",    "instant",        1.0),
            sys(f"  loop_count:  {loop_str},",     "typewriter_fast"),
            sys(f"  wallet:      critically_endangered,", "typewriter_fast"),
            sys(f"  sanity:      suspicious,",     "typewriter_fast"),
            sys(f"  deja_vu:     {deja_str},",     "typewriter_fast"),
            sys(f"  items_held:  {len(inventory)},",    "typewriter_fast"),
            sys("}", "instant"),
        ]

    # ── inventory ──────────────────────────────────────────────────────────────
    if c in ("inventory", "inv", "i"):
        if not inventory:
            return [
                sys(">> inventory"),
                sys("  [空] 背包里什么都没有。"),
                sys("  这在 SOS 团的活动里是暂时的状态。"),
            ]
        lines = [sys(">> inventory")]
        for item in sorted(inventory):
            lines.append(sys(f"  [道具] {item}"))
        lines.append(sys(f"  共 {len(inventory)} 件物品。"))
        return lines

    # ── ls ─────────────────────────────────────────────────────────────────────
    if c == "ls":
        scene_map = {
            "c1a_morning_call": [
                sys(">> ls — 扫描 Home"),
                sys("  [环境] 卧室 / 窗帘 / 阳光"),
                sys("  [物品] 手机 x1 — 来自 Haruhi 的未读消息: 0"),
                sys("  [物品] 钱包 x1 — 当前状态: endangered"),
                sys("  [实体] 妹妹 — 状态: 正常/人类"),
            ],
            "c2a_cafe": [
                sys(">> ls — 扫描 Cafe"),
                sys("  [实体] Haruhi Suzumiya — 状态: 高能/危险"),
                sys("  [实体] Koizumi Itsuki — 状态: 微笑中/可疑"),
                sys("  [实体] Asahina Mikuru — 状态: 紧张/时间旅行者(未确认)"),
                sys("  [实体] Nagato Yuki    — 状态: 读书/数据综合体"),
                sys("  [物品] 账单 x1 — 金额: 阿虚全额负担"),
                sys("  [危险] 春日的计划书 — 内容: 荒诞/自洽"),
            ],
            "c2a_rooftop": [
                sys(">> ls — 扫描 Rooftop"),
                sys("  [实体] Koizumi Itsuki — 状态: 施工中/微笑"),
                sys("  [物品] 瓦楞纸 UFO — 完成度: 30% / 可信度: 2%"),
                sys("  [物品] 风筝线 x1 — 状态: 未使用"),
                sys("  [环境] 天台横梁 / 栏杆 / 储物间"),
            ],
        }
        default = [
            sys(">> ls — 扫描当前区域"),
            sys("  [结果] 没有特别值得注意的实体或物品。"),
        ]
        return scene_map.get(scene_id, default)

    # ── date ───────────────────────────────────────────────────────────────────
    if c == "date":
        shift_pct = f"{0.000001 * (10 ** loop_count):.6f}%" if loop_count < 6 else "??%"
        return [
            sys(">> date"),
            sys("  DATE: 2006-05-02"),
            sys(f"  WORLDLINE_SHIFT: {shift_pct}", "glitch" if loop_count > 0 else "typewriter_fast"),
            sys(f"  LOOP_COUNT: {loop_count}",     "glitch" if loop_count > 0 else "typewriter_fast"),
            sys("  α 世界线分歧值: 1.048596"),
        ]

    # ── scan ───────────────────────────────────────────────────────────────────
    if c.startswith("scan"):
        target = c[4:].strip()
        data = {
            "nagato": [
                sys(">> scan nagato"),
                sys("  NAME: 長門有希 / Nagato Yuki"),
                sys("  TYPE: 데이터統合思念体 — Interface"),
                sys("  AFFILIATION: 情報統合思念体"),
                sys("  CURRENT: 文学作品阅读 // 监视 root@kyon"),
                sys("  DANGER_LEVEL: [CLASSIFIED]", "warning"),
            ],
            "haruhi": [
                sys(">> scan haruhi"),
                sys("  NAME: 凉宫春日 / Haruhi Suzumiya"),
                sys("  TYPE: 人类(?) — 神格不明"),
                sys("  WORLDLINE_INFLUENCE: ABSOLUTE"),
                sys("  CURRENT_THREAT: 宇宙崩溃概率与其情绪正相关", "warning"),
            ],
            "koizumi": [
                sys(">> scan koizumi"),
                sys("  NAME: 古泉一树 / Koizumi Itsuki"),
                sys("  TYPE: 超能力者"),
                sys("  AFFILIATION: 机关"),
                sys("  CURRENT: 微笑中 // 真实意图: [UNKNOWN]"),
            ],
            "mikuru": [
                sys(">> scan mikuru"),
                sys("  NAME: 朝比奈实玖瑠 / Asahina Mikuru"),
                sys("  TYPE: 时间旅行者(未来)"),
                sys("  CLEARANCE_LEVEL: [CLASSIFIED BY FUTURE]", "warning"),
                sys("  CURRENT: 紧张中 // 可爱值: OVERFLOW"),
            ],
        }
        return data.get(target, [
            sys(f">> scan {target or '??'}"),
            err(f"  未知目标 '{target}' — 尝试: scan nagato / haruhi / koizumi / mikuru"),
        ])

    # ── read ───────────────────────────────────────────────────────────────────
    if c.startswith("read"):
        return [
            sys(">> read"),
            sys("  [长门的书] 书名: ████████████ / 作者: ████"),
            sys("  [春日的计划书] 内容: UFO × 外星人 × Terminal Mission"),
            sys("  [账单] 金额: 无法面对现实"),
        ]

    # ── map ────────────────────────────────────────────────────────────────────
    if c == "map":
        return [
            sys(">> map"),
            sys("  [A] Home       — 阿虚的家 (起点)"),
            sys("  [B] Street     — 商业街"),
            sys("  [C] Cafe       — 站前咖啡厅"),
            sys("  [D] Store      — 便利店"),
            sys("  [E] Nagato_Apt — 长门公寓 (北高附近 #708)"),
            sys("  [F] Rooftop    — 北高天台 (终点)"),
            sys("  路线提示: 时间与地点决定道具。", "glitch" if loop_count > 0 else "instant"),
        ]

    # ── history ────────────────────────────────────────────────────────────────
    if c == "history":
        return [
            sys(">> history"),
            sys(f"  本轮回编号: #{loop_count}"),
            sys(f"  已探索场景数: (参见系统日志)"),
            sys(f"  当前持有道具: {len(inventory)} 件"),
            sys("  /var/log/sos/loop_history.log — ACCESS_GRANTED", "glitch"),
        ]

    # ── unknown ────────────────────────────────────────────────────────────────
    return [
        err(f">> 未知指令: '{cmd}'"),
        err("   输入 help 查看可用指令列表"),
    ]