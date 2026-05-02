
from dataclasses import dataclass, field
from typing import List

@dataclass
class LogEntry:
    frontmatter: str         # 具体的时间戳 [xx:xx:xx] 或者 记录谁说的 Yuki >
    content: str

@dataclass
class Command:                # Command 是对全局状态的查询, 所以实际上并不需要额外记录什么  > command name
    name: str
    next_scene_id: str | None # 移动行为 会移动到下一个场景

@dataclass
class Choice:
    name: str
    next_scene_id: str        # 每个 选择 对应唯一 下一个场景 ID

@dataclass
class Scene:
    id: str
    location: str = ""
    entries: List[LogEntry] = field(default_factory=list)
    commands: List[Command] = field(default_factory=list)
    choices: List[Choice] = field(default_factory=list)
    hint: str = ""