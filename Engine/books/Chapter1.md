## Chapter 1：黄金周不可能这么安静

本章负责建立游戏开场、终端表现、春日来电和阿虚被迫出门的动机。

本章不使用“二周目追加文本”的复用写法，而是拆成两套完整脚本：

- **第一次未轮回版本**：玩家尚不知道循环，重点是日常节奏和被春日卷入事件。
- **第二次及更多轮回版本**：玩家和阿虚开始产生既视感，终端出现轻微异常，但主线仍推进到咖啡厅。

## Chapter 1A：第一次未轮回

### 场景ID：`第一次未轮回：清晨来电`
**Location**: `home`  
**Trigger**: `new_game && loop_count == 0`  
**Purpose**: 第一次开场。建立终端 UI、日期、阿虚房间和春日来电。

#### Lines

```text
[08:00:00] System booting...
[08:00:01] DATE: 05/02
[08:00:02] WORLDLINE_SHIFT: 0.000001%
[08:00:03] USER_HOST: kyon@SOS
[08:00:04] ACCESS_LEVEL: normal

[08:00:20] 光线从窗帘缝隙里挤进房间。
[08:00:25] 黄金周的第一天，本应以一种对人类文明来说极其合理的方式开始：睡到自然醒。
[08:00:35] 电话铃声刺穿了这个合理计划。

Sister > 阿虚，电话。

[08:00:38] 昨天熬夜看电视忘在了客厅的电话被可爱的妹妹拿了进来递到了我耳边。

Kyon > 不用说我也知道，会在假期早上八点打电话来的，不是推销员，就是比推销员更难对付的人。

[08:00:43] CALL_SOURCE: Haruhi Suzumiya
[08:00:44] CALL_STATUS: forced_connected

Haruhi > 太慢了！给你二十分钟，立刻到站前的咖啡厅集合！
Haruhi > 迟到的话死刑！

Kyon > 我甚至还没说喂。

Haruhi > 那种形式主义省略掉也没关系！总之快点来！

[08:01:10] CALL_STATUS: disconnected_by_remote

Kyon > 开什么玩笑。今天是 5 月 2 日，是黄金周啊。
Kyon > 劳动节的初衷难道不是为了让劳动者有尊严地躺在被窝里睡到中午吗？
Kyon > 虽然在日本既不过劳动节我也算不上什么劳动者，但在这个神圣的日子里强迫高中生劳动，简直是对现代文明的公然挑衅！

```
#### 选项

```text
[1] 把头埋进被子里装死。
[2] 叹口气，乖乖起床穿衣服。
```

#### Next

- `[1]` -> `第一次未轮回：被窝抵抗`
- `[2]` -> `第一次未轮回：出门去咖啡厅`

### 场景ID：`第一次未轮回：被窝抵抗`

**Location**: `home`  
**Trigger**: 在 `第一次未轮回：清晨来电` 选择 `[1]`  
**Purpose**: 第一次给玩家“拒绝春日”的错觉，展示春日的压迫感，但不改变主线。

#### Lines

```text
[08:01:30] 你把头埋进被子里，试图用棉织品构筑一道抵抗凉宫春日的防线。

Kyon > 只要我不承认电话存在，电话就没有发生过。
Kyon > 这是一种高度先进的精神胜利法，虽然大概率只能持续三十秒。

[08:02:00] 手机开始连续震动。
[08:02:01] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:05] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:10] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:15] MESSAGE_FROM_HARUHI: 我已经开始计时了。

Kyon > 这已经不是催促了，这是小型精神污染。
Kyon > 好吧，好吧，真是没办法，我起来就是了。

```

#### Presentation Notes

```text
log_scroll_slow during blanket_resistance
```

#### 选项

```text
[1] 起床。
```

#### Next

- `[1]` -> `第一次未轮回：出门去咖啡厅`

### 场景ID：`第一次未轮回：出门去咖啡厅`

**Location**: `home`  
**Trigger**: 从 `第一次未轮回：清晨来电` 或 `第一次未轮回：被窝抵抗` 进入  
**Purpose**: 第一次出门前的过渡，完成从日常到事件的切换。

#### Lines

```text
[08:10:10] 你用高中男生所能拥有的最低限度仪容整理能力换好衣服，推着自行车走出家门。
[08:12:25] 天气晴朗得过分，仿佛连云都被春日命令不准迟到。

Kyon > 如果这世界上真的存在神明，希望她至少能给我报销咖啡厅的账单。

[08:20:00] ROUTE: home -> cafe
```

#### Presentation Notes

```text
route_trace when ROUTE is printed
```

#### 选项

无。

#### Next

- 自动进入 `第一次未轮回：咖啡厅集合`





## Chapter 1B：第二次及更多轮回

### 场景ID：`轮回后：清晨重启`

**Location**: `home`  
**Trigger**: `loop_reset && loop_count >= 1`  
**Purpose**: 第二轮及以后开场。完整重写早晨事件，表现既视感、终端异常和阿虚对重复的怀疑。

#### Lines

```text
[08:00:00] System rebooting...
[08:00:01] DATE: 05/02
[08:00:02] WORLDLINE_SHIFT: 0.000014%
[08:00:03] USER_HOST: kyon@SOS
[08:00:04] WARNING: previous_session_trace_detected
[08:00:05] WARNING: overwritten

[08:00:20] 光线从同一条窗帘缝隙里挤进房间。

Kyon > 等一下。
Kyon > 这个角度的阳光，这种讨厌的安静，还有我脑子里那种“接下来要出事”的感觉。

[08:00:35] 电话铃声准时响起。

Kyon > 果然。

Sister > 阿虚，电话。

Kyon > 我知道。
Kyon > 不如说，我从十五秒前就开始知道了。

[08:00:43] CALL_SOURCE: Haruhi Suzumiya
[08:00:44] CALL_STATUS: forced_connected

Haruhi > 太慢了！给你二十分钟，立刻到站前的咖啡厅集合！
Haruhi > 迟到的话死刑！

Kyon > 春日。

Haruhi > 干嘛？你该不会还没起床吧？

Kyon > 你昨天是不是也说过同样的话？

[08:00:58] CALL_NOISE: zzzz

Haruhi > 昨天？你睡糊涂了吧，今天才是假期第一天！
Haruhi > 总之快来！今天的计划可是足以改变世界的！

[08:01:10] CALL_STATUS: disconnected_by_remote

Kyon > 改变世界。
Kyon > 真遗憾，我总觉得它已经被改变过一次了。

```

#### Presentation Notes

```text
terminal_flicker_once at scene_start
input_lock during call_connected
text_jitter_light on CALL_NOISE
input_unlock after call_disconnected
```

#### 选项

```text
[1] 再次把头埋进被子里。
[2] 直接起床，避免重复无意义抵抗。
[3] 输入状态指令，确认自己的精神状态。
```

#### Next

- `[1]` -> `轮回后：再次抵抗`
- `[2]` -> `轮回后：带着既视感出门`
- `[3]` -> `轮回后：确认状态`

### 场景ID：`轮回后：确认状态`

**Location**: `home`  
**Trigger**: 在 `轮回后：清晨重启` 选择 `[3]`  
**Purpose**: 通过 `Status` 命令表现阿虚意识到异常，同时保持幽默节奏。

#### Lines

```text
[08:01:30] STATUS_CHECK_RUNNING...

KYON.STATUS = {
  SLEEP: INSUFFICIENT,
  WALLET: ENDANGERED,
  SANITY: SUSPICIOUS,
  DEJA_VU: UNDENIABLE
}

Kyon > 连终端都开始用这种方式嘲笑我了吗？

[08:01:40] SYSTEM: 建议行动：前往咖啡厅。
```

#### Presentation Notes

```text
cursor_blink_fast during STATUS_CHECK_RUNNING
```

#### 选项

```text
[1] 起床。
```

#### Next

- `[1]` -> `轮回后：带着既视感出门`

### 场景ID：`轮回后：再次抵抗`

**Location**: `home`  
**Trigger**: 在 `轮回后：清晨重启` 选择 `[1]`  
**Purpose**: 第二轮以后重复“装死”选择，但台词变为阿虚明知无效仍想试一次。

#### Lines

```text
[08:01:30] 你再次把头埋进被子里。

Kyon > 如果第一次失败了，第二次也许会因为宇宙同情我而成功。
Kyon > 虽然这个推论的科学性约等于春日的 UFO 计划。

[08:02:01] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:05] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:10] MESSAGE_FROM_HARUHI: 还没出门？
[08:02:11] MESSAGE_FROM_HARUHI: 你是不是又把头埋进被子里？

Kyon > 为什么是“又”？

[08:02:12] MESSAGE_FROM_HARUHI: 直觉。

Kyon > 她的直觉已经发展到这种程度了嘛？

```

#### Presentation Notes

```text
screen_dim_10 during repeated_blanket_resistance
```

#### 选项

```text
[1] 承认失败并起床。
```

#### Next

- `[1]` -> `轮回后：带着既视感出门`

### 场景ID：`轮回后：带着既视感出门`

**Location**: `home`  
**Trigger**: 从 `轮回后：清晨重启`、`轮回后：确认状态` 或 `轮回后：再次抵抗` 进入  
**Purpose**: 第二轮及以后出门过渡。加入路线既视感和轻微系统提示，为后续时间窗口解谜埋钩子。

#### Lines

```text
[08:10:00] 你换好衣服。
[08:10:05] 动作熟练得让人不安。

Kyon > 我是不是已经做过这件事？

[08:12:20] 你推着自行车走出家门。
[08:12:25] 天气晴朗得过分。连云的位置都像是从某个粗心的存档里复制过来的。

[08:12:30] SYSTEM: 记忆路线不匹配。
[08:12:31] SYSTEM: 观测建议：时间和地点。

Kyon > 时间和地点？
Kyon > 喂，长门。如果这是你留下的提示，能不能下次直接写成现代日语？

[08:20:00] ROUTE: home -> cafe
```

#### Presentation Notes

```text
text_glitch_tiny after suggested_observation
route_trace_with_afterimage when ROUTE is printed
```

#### 选项

无。

#### Next

- 自动进入 `轮回后：咖啡厅再次集合`





