# SOS Terminal Mission

一个把 Python 终端文字冒险嵌入 Godot CRT 显示壳中的混合项目。仓库根目录负责 Godot 外层界面、着色器和终端嵌入，`Engine/` 目录负责真正的剧情、状态机、Textual UI、音频和小游戏逻辑。

## 项目组成

### 1. Godot 外壳

根目录是一个 Godot 4.6 项目，默认主场景配置在 `project.godot` 中，启动后会加载 `main.tscn`，再进入 `screen.tscn`，通过 `addons/godot_xterm` 提供的 `Terminal` / `PTY` 节点在屏幕内嵌一个可交互终端。

这个壳层主要负责：

- 显示器外观与布局
- CRT 材质与视觉包装
- 嵌入式终端窗口
- 将终端输入输出映射到 Godot 画面中

### 2. Python 游戏引擎

`Engine/` 是真正可运行的终端 RPG，使用：

- `textual` 构建终端 UI
- `pygame` 播放 BGM 与音效
- Markdown 剧本文本驱动场景
- 一个 Mikuru 打字生存小游戏和结局字幕场景

更详细的运行方式和模块说明见 [Engine/README.md](Engine/README.md#L1)。

## 仓库结构

```text
sos-terminal-mission/
├── project.godot             # Godot 项目配置，指定主场景与插件
├── main.tscn                 # 外层显示器主场景
├── screen.tscn               # 带 CRT 贴图与内嵌终端的屏幕场景
├── terminal.gd               # 启动终端进程，进入 Engine 并运行 Python 游戏
├── texture_rect.gd           # 终端贴图相关脚本
├── Assets/                   # 字体、CRT 材质、显示器贴图
├── addons/godot_xterm/       # Godot 内嵌终端扩展
└── Engine/                   # Python 终端 RPG 本体
```

## 启动方式

### 方式一：直接运行 Python 游戏

如果你只想调试剧情、终端 UI 或 Python 逻辑，直接运行 `Engine/` 即可：

```bash
cd Engine
uv sync
uv run python main.py
```

这条路径最适合开发 `Engine` 内的剧情、状态机和 Textual 界面。

### 方式二：通过 Godot 外壳启动

如果你想看到最终的 CRT 包装效果，可以直接运行根目录 Godot 项目。

Godot 侧会通过 `terminal.gd` 自动执行：

- Windows: `cmd.exe /c cd Engine && uv run main.py`
- 非 Windows: `sh -c cd Engine/ && uv run main.py`
- Release 模式: 直接尝试启动 `main.exe`

这意味着 Godot 外壳默认依赖：

- 已安装 `uv`
- `Engine/` 依赖已完成安装
- 开发态下本机能直接启动 Python 版本游戏

## 开发依赖

### Godot 层

- Godot 4.6
- 已启用 `addons/godot_xterm/plugin.cfg`

### Python 层

- Python 3.12+
- `textual`
- `pygame`
- `uv`（推荐）

## 开发建议

- 改剧情文本或游戏逻辑：优先看 `Engine/`
- 改显示器外观、终端嵌入和 CRT 效果：优先看根目录场景与 `Assets/`
- 改 Godot 内嵌终端行为：查看 `terminal.gd` 与 `addons/godot_xterm/`
- 做最终整体验收：从 Godot 项目启动，确认内嵌终端、字体、输入和显示效果都正常
