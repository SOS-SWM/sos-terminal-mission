# SOS Brigade Terminal RPG
## 凉宫春日主题 · 终端风格文字冒险

```
▉ SYSTEM_CORE: Nagato_Interface v1.1.4 ▉ WORLDLINE: 0xFF-05-02[UNSTABLE]
```

### 快速开始

**使用 uv（推荐）**
```bash
cd haruhi-rpg
uv sync           # 安装依赖（需要网络）
uv run haruhi-rpg
```

**使用 pip**
```bash
pip install textual
python -m haruhi_rpg
```

**最低要求**
- Python 3.11+
- textual >= 0.80.0
- 终端尺寸建议：120 × 40 以上

---

### 游戏操作

| 输入 | 说明 |
|------|------|
| `1` / `2` / `3` | 选择剧情选项 |
| `ls` | 扫描当前区域 |
| `date` | 查看世界线信息 |
| `scan` | 扫描实体 |
| `read` | 读取物品 |
| `status` | 查询角色状态 |
| `help` | 显示所有指令 |
| `Ctrl+R` | 重新开始 |
| `Ctrl+C` | 退出 |

---

### 项目结构（模块解耦）

```
haruhi_rpg/
├── models.py      # 纯数据结构 (LogEntry, Scene, GameState...)
├── scenario.py    # 所有剧情内容 (场景、对话、指令响应)
├── engine.py      # 游戏逻辑层 (输入解析、场景跳转)
├── ui.py          # Textual TUI 组件 (StatusBar, NarrativeLog, OptionsPane, InputBar)
└── __main__.py    # 入口点
```

**设计原则**
- `models.py` 不依赖任何其他模块
- `scenario.py` 只依赖 `models`
- `engine.py` 只依赖 `models` + `scenario`
- `ui.py` 只依赖 `models` + `engine`

扩展剧本：只需修改 `scenario.py`，UI 和引擎无需改动。
