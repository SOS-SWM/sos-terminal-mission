# SOS Terminal Mission

基于《凉宫春日的忧郁》世界观制作的终端叙事 RPG。当前版本使用 Python + Textual 构建 CRT 风格界面，剧情文本来自 `books/Chapter1.md` 到 `books/Chapter4.md`，并在主线过程中穿插一个 Mikuru 打字生存小游戏与结局字幕。

## 当前状态

- 项目目录名与包名为 `sos-terminal-mission`
- 运行入口是 `main.py`
- UI 框架为 `textual`
- 音频播放依赖 `pygame`
- 剧情数据源为 `books/*.md`

## 环境要求

- Python 3.12+
- 建议在支持 ANSI 颜色与较大窗口的终端中运行
- 需要可用音频设备；启动时会初始化 `pygame.mixer`

## 安装与运行

### 使用 `uv`

```bash
cd Engine
uv sync
uv run python main.py
```

### 使用 `pip`

```bash
cd Engine
pip install textual pygame
python main.py
```

## 打包

项目包含 PyInstaller 规格文件 `main.spec`，会把 `books/` 一并打包：

```bash
cd Engine
uv run pyinstaller main.spec
```

开发依赖已在 `pyproject.toml` 的 `dev` 组中声明。

## 游戏玩法

这是一个以剧情选择为主、终端指令为辅的文字冒险。

- 场景推进主要靠输入数字选项，例如 `1`、`2`、`3`
- 信息查询使用终端指令，不负责直接移动场景
- 文本播放过程中可输入 `skip` 快速显示当前场景剩余文本
- 当日志过长时，可用方向键和 `Page Up` / `Page Down` 滚动
- 部分关键节点会要求直接按回车继续

### 可用指令

| 指令                      | 说明                 |
| ------------------------- | -------------------- |
| `help`                    | 显示帮助             |
| `status` / `st`           | 查看当前状态         |
| `inventory` / `inv` / `i` | 查看背包             |
| `map`                     | 查看地点列表         |
| `date`                    | 查看日期与世界线     |
| `ls`                      | 查看终端中的可读文件 |
| `cat loop.log`            | 读取循环日志         |
| `skip`                    | 跳过当前场景动画文本 |

`go ...` 在当前版本只是剧本文本提示，真正移动仍然必须通过数字选项完成。

## 主要结构

```text
Engine/
├── main.py         # Textual 主界面、BGM 切换、剧情与小游戏衔接入口
├── engine.py       # 游戏状态推进、选项处理、行动点逻辑
├── scene.py        # 从 books/ 解析剧情，并提供指令响应
├── models.py       # 场景、日志、状态等数据模型
├── components.py   # 状态栏、日志区、输入区、选项区等 UI 组件
├── mikuru.py       # Mikuru 打字生存小游戏
├── credit.py       # 通关后的字幕滚动场景
├── books/          # Chapter1-4 剧情 Markdown，作为文本源
├── assets/         # BGM 与音效资源
├── pyproject.toml  # 依赖与 Python 版本声明
└── main.spec       # PyInstaller 打包配置
```

## 核心机制

### 1. 剧情驱动 + 指令辅助

`GameEngine` 只处理游戏逻辑：数字输入走剧情选项，文本命令走信息查询。这样 UI 层和场景逻辑保持解耦。

### 2. 行动点与循环路线

- 第一轮探索阶段使用 4 个行动点
- 后续循环探索阶段使用 7 个行动点
- 地图中的地点访问会消耗行动点
- 二周目存在首访 / 重访路由，部分关键物品需要按顺序升级获取

### 3. 剧本文本外置

剧情正文不硬编码在主程序里，而是从 `books/` 下的 Markdown 解析为 `Scene`。这意味着修改文案、扩展章节时，通常优先改剧情文档和 `scene.py` 的场景元数据。

### 4. 支线小游戏与结局画面

主线在特定场景会切入 `MikuruTypingSurvival`。通关后会进入 `EndingCreditScene` 显示结局字幕与音乐。

## 开发说明

- 如果要改剧情文本，优先查看 `books/` 与 `scene.py`
- 如果要改状态推进或分支条件，查看 `engine.py`
- 如果要改终端界面表现，查看 `components.py` 与 `main.py`
- 如果要调整小游戏，查看 `mikuru.py`
