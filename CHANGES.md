# 变更说明：行动点时间系统移植到新主线

## 背景

原 `feature/action-point-time-system` 分支基于旧的 `Engine/haruhi_rpg/` 子包结构开发。  
远程 `main` 在此期间做了一次大重构：删除了 `haruhi_rpg/` 子包，改为扁平的 `Engine/` 结构，UI 框架从自研切换到 Textual。  
本分支 (`feature/ap-system-v2`) 将行动点系统完整移植到新主线结构上。

## 新增文件

### `Engine/models.py`（替换原有）

在原有 `LogEntry`、`Command`、`Choice`、`Scene` 基础上扩展了游戏状态相关的数据结构：

- **LogEntry**: 保留原有 6 字段格式（timestamp, kind, speaker, text, effect, speed），新增 `frontmatter` / `content` 兼容属性供 Textual UI 使用
- **Choice**: 新增 `requires_flag`、`requires_item`、`hidden` 字段，支持条件选项
- **Scene**: 新增 `grant_items`、`consume_items`、`set_flags`、`triggers_loop_reset`、`auto_next_scene`、`terminal_scene` 等游戏逻辑字段
- **SystemStatus**: 世界线、位置、时间、循环计数
- **GameState**: 完整游戏状态，包含背包、标志位、行动点等

### `Engine/scene.py`（替换原有）

从原 `haruhi_rpg/scenario.py` 移植，仅修改 import 路径（`from haruhi_rpg.models` → `from models`）。功能包括：

- **剧本导入系统**: 从 `books/Chapter1-4.md` 解析原始剧本文本，生成 Scene 对象
- **SCENE_IDS**: 剧本标题到场景 ID 的映射（32 个场景）
- **SCENE_META**: 每个场景的元数据（位置、时间、选项、物品、标志位等）
- **时间槽表**: 一周目 4 槽（10:00/12:00/15:00/18:00），二周目 7 槽（09:30~19:30）
- **AP 常量**: `AP_SCENES_LOOP1`、`AP_SCENES_LOOP2`、`MAP_HUBS`、`AP_INIT_SCENES`、`AP_FINAL_TARGETS`
- **LOOP2_ROUTING**: 二周目智能路由表，根据背包状态自动选择首访/重访场景
- **build_scenario()**: 构建并验证完整场景图，导出 `SCENE_DB` 供 main.py 使用

### `Engine/engine.py`（新增）

从原 `haruhi_rpg/engine.py` 移植，仅修改 import 路径。核心功能：

- **行动点系统**: 一周目 4 AP，二周目 7 AP，每次探索消耗 1 点
- **时间推进**: 按行动点消耗推进时间槽，不依赖剧本固定时间戳，避免时间倒退
- **智能路由**: 二周目地图只显示 4 个地点，引擎根据背包自动路由到首访或重访
- **物品消耗链**:
  - 便利店重访：普通的怪兽贴纸 → 玩偶服
  - 长门公寓重访：普通的灯带 → 大红按钮
  - 天台重访：普通的风筝线 → 超能力飞行装置（需同时持有玩偶服和大红按钮）
- **真结局判定**: 进入 c4b_final 时自动检查是否持有全部三件关键物品
- **循环重置**: 行动点耗尽后自动进入验收场景，验收失败触发循环重置

### `Engine/books/`（新增目录）

原始剧本 Markdown 文件，作为剧情文本的唯一数据源：

- `Chapter1.md` — 第一章：早晨来电、赖床、出门（一周目 + 轮回后）
- `Chapter2.md` — 第二章：咖啡厅集合、抗议账单、买单开放地图
- `Chapter3.md` — 第三章：自由探索（大街/便利店/长门公寓/天台，首访 + 重访）
- `Chapter4.md` — 第四章：最终验收、真结局

### `Engine/main.py`（修改）

在原有 Textual UI 基础上接入 GameEngine：

- `transition_to_scene` 改为通过 engine 驱动
- 玩家输入通过 `engine.process_input()` 处理
- StatusBar 从 `engine.state.status` 读取数据
- 保留 Mikuru 小游戏的场景切换逻辑

### `Engine/components.py`（修改）

- `StoryLog.play_entries()` 适配新的 LogEntry 格式（通过 frontmatter/content 兼容属性）
- `OptionsConsole.render_options()` 适配 Choice.name 兼容属性

## 游戏机制说明

### 一周目（4 AP）

- 玩家在咖啡厅买单后获得 4 个行动点
- 可探索 4 个地点：大街、便利店、长门公寓、天台
- 每个地点只能去一次，重复访问会被阿虚吐槽且不消耗 AP
- 4 个 AP 用完后自动进入天台验收 → 验收失败 → 循环重置

### 二周目（7 AP）

- 玩家获得 7 个行动点
- 地图只显示 4 个地点，引擎根据背包自动路由到首访或重访
- 重复访问已完成的地点会浪费 AP
- 最优路径（需要玩家自己推理）：
  1. 便利店首访 → 获得普通的怪兽贴纸
  2. 长门公寓首访 → 获得普通的灯带
  3. 便利店重访 → 贴纸升级为玩偶服
  4. 长门公寓重访 → 灯带升级为大红按钮
  5. 天台首访 → 获得普通的风筝线
  6. 天台重访 → 风筝线升级为超能力飞行装置（需要已有玩偶服+大红按钮）
  7. 大街（可选）
- 7 AP 用完后进入天台验收，持有全部三件关键物品可触发真结局

## 未修改的文件

以下文件保持 main 分支原样，未做任何改动：

- `Engine/mikuru.py` — Mikuru 打字小游戏
- `Engine/pyproject.toml` — 项目配置
- `Engine/.python-version` — Python 版本
- 所有 Godot 相关文件（Assets/、addons/、*.tscn、*.gd 等）
