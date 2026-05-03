import math
import random
from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.containers import Container
from textual.reactive import reactive

@dataclass
class Enemy:
    type: str
    x: int
    y: int
    hp: int
    freeze: int
    cooldown: int = 0  # 0 for melee, cooldown timer for ranged


@dataclass
class EnemyProjectile:
    float_x: float
    float_y: float
    x: int
    y: int
    vx: float
    vy: float


@dataclass
class PlayerProjectile:
    float_x: float
    float_y: float
    x: int
    y: int
    vx: float
    vy: float
    type: str
    damage: int
    freeze: int

MIKURU_ART = [" ∩_∩ ", "(T_T)", "/>M<"]

class MikuruTypingSurvival(App[None]):
    CSS = """
    Screen { align: center middle; background: #050505; }

    #crt-monitor {
        width: 96%;
        height: 96%;
        layout: grid;
        grid-size: 2 2; grid-columns: 5fr 2fr; grid-rows: 2fr 1fr;
        background: #001100; color: #33ff33; border: double #33ff33;
    }

    .box { border: solid #33ff33; padding: 0 1; height: 100%; }
    #map-region, #status-region, #ops-region, #input-region { border-title-color: #33ff33; }
    #input-region {
        layout: vertical;
        padding-top: 1;
        align: center middle;
    }

    Input {
        background: #000000; color: #ffffff; border: none;
        border-bottom: solid #33ff33; margin-top: 1; margin-bottom: 1; width: 100%;
        align-horizontal: center;
        text-align: center;
    }
    Input:focus { border-bottom: solid #ffffff; }

    #crt-monitor.hit-flash { background: #330000; border: double #ff0000; }
    #crt-monitor.hit-flash .box { border: solid #ff0000; border-title-color: #ff0000; }
    """

    player_hp = reactive(100)
    kill_count = reactive(0)
    beam_charge = reactive(0)
    time_elapsed = reactive(0)
    beam_ready = reactive(False)
    game_active = reactive(True)

    def __init__(self):
        super().__init__()
        # 初始默认尺寸，稍后在引擎启动时将动态适配左上角框体
        self.map_w = 52
        self.map_h = 13
        self.px = 3
        self.py = 5
        self.enemies: list[Enemy] = []
        self.enemy_projectiles: list[EnemyProjectile] = []
        self.player_projectiles: list[PlayerProjectile] =[]
        self.beam_active_frames = 0

        self.victory_time = 180
        self.feedback_text = "Ready."

        self.classified_cd = 0
        self.teatime_cd = 0

        self.feedback_queue: list[str] = ["Ready."]
        self.feedback_limit = 3



    def compose(self) -> ComposeResult:
        with Container(id="crt-monitor"):
            yield Static(id="map-region", classes="box")
            yield Static(id="status-region", classes="box")
            yield Static(id="ops-region", classes="box")
            with Container(id="input-region", classes="box"):
                yield Static("root@Mikuru:~#  ", id="input-label")
                yield Input(id="command-input")

    def on_mount(self) -> None:
        self.query_one("#map-region").border_title = " RADAR "
        self.query_one("#status-region").border_title = " STATUS "
        self.query_one("#ops-region").border_title = " OPS MANUAL "
        self.query_one("#input-region").border_title = " TERMINAL "

        self.query_one(Input).focus()
        self.update_ops_area()

        self.tick_timer = self.set_interval(0.1, self.engine_tick)
        self.ai_timer = self.set_interval(0.5, self.ai_tick)
        self.clock_timer = self.set_interval(1.0, self.update_clock)
        self.draw_map()
        self.update_status_area()

    def update_clock(self) -> None:
        if not self.game_active:
            return

        if self.classified_cd > 0:
            self.classified_cd -= 1
        if self.teatime_cd > 0:
            self.teatime_cd -= 1

        self.time_elapsed += 1
        self.update_status_area()
        if self.time_elapsed >= self.victory_time:
            self.game_over(victory=True)

    def engine_tick(self) -> None:
        if not self.game_active:
            return

        # --- 动态计算并贴合窗口左上角框 (map-region) 尺寸 ---
        map_region = self.query_one("#map-region")
        if map_region.content_size.width > 0 and map_region.content_size.height > 0:
            # 保证最小可用尺寸防崩溃
            self.map_w = max(10, map_region.content_size.width)
            self.map_h = max(4, map_region.content_size.height)

            # 确保即使缩放窗口，角色也永远被限制在新的边界内
            self.px = max(0, min(self.map_w - 5, self.px))
            self.py = max(0, min(self.map_h - 3, self.py))

        if getattr(self, "beam_active_frames", 0) > 0:
            self.beam_active_frames -= 1

        # --- 敌人直线弹幕物理运算 ---
        surviving_e_proj: list[EnemyProjectile] =[]
        for p in self.enemy_projectiles:
            p.float_x += p.vx
            p.float_y += p.vy
            px, py = int(p.float_x), int(p.float_y)

            # 碰撞检测
            if self.px <= px < self.px + 5 and self.py <= py < self.py + 3:
                self.player_hp -= 5
                self.trigger_hit_flash()
                if self.player_hp <= 0:
                    self.game_over(victory=False)
                continue
            if 0 <= px < self.map_w and 0 <= py < self.map_h:
                p.x, p.y = px, py
                surviving_e_proj.append(p)
        self.enemy_projectiles = surviving_e_proj

        # --- 玩家弹幕自瞄运算 ---
        surviving_p_proj: list[PlayerProjectile] =[]
        for p in self.player_projectiles:
            closest, min_d = None, 999
            for e in self.enemies:
                d = math.hypot(e.x - p.float_x, e.y - p.float_y)
                if d < min_d:
                    min_d, closest = d, e

            if closest and min_d > 0:
                dx = (closest.x + 1) - p.float_x
                dy = closest.y - p.float_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    speed = 2.0
                    p.vx, p.vy = (dx / dist) * speed, (dy / dist) * speed

            steps = 2
            hit = False
            px, py = 0, 0
            for _ in range(steps):
                p.float_x += p.vx / steps
                p.float_y += p.vy / steps
                px, py = int(p.float_x), int(p.float_y)

                for e in self.enemies:
                    if e.x <= px <= e.x + 2 and e.y == py:
                        hit = True
                        e.hp -= p.damage
                        if p.freeze:
                            e.freeze = p.freeze

                        if e.hp <= 0:
                            if e in self.enemies:
                                self.enemies.remove(e)
                            self.handle_kill(1)
                            self.show_feedback("Destroyed!", "green")
                        break
                if hit:
                    break

            if not hit and 0 <= px < self.map_w and 0 <= py < self.map_h:
                p.x, p.y = px, py
                surviving_p_proj.append(p)

        self.player_projectiles = surviving_p_proj
        self.draw_map()

    def ai_tick(self) -> None:
        if not self.game_active:
            return

        spawn_chance = 0.15 + (self.time_elapsed / 500.0) * 0.7
        hp_multiplier = 1.0 + (self.time_elapsed / 500.0) * 2.0

        if random.random() < spawn_chance:
            # 限制敌人生成点：始终在当前左上角框 (self.map_w) 的最右侧出现
            spawn_x = self.map_w - 4
            spawn_y = random.randint(0, self.map_h - 1)
            if random.random() < 0.4:
                self.enemies.append(
                    Enemy(
                        type="ranged",
                        x=spawn_x, y=spawn_y,
                        hp=int(15 * hp_multiplier),
                        cooldown=0, freeze=0,
                    )
                )
            else:
                self.enemies.append(
                    Enemy(
                        type="melee",
                        x=spawn_x, y=spawn_y,
                        hp=int(25 * hp_multiplier),
                        freeze=0, cooldown=0,
                    )
                )

        px_center, py_center = self.px + 2, self.py + 1

        for e in self.enemies:
            if e.freeze > 0:
                e.freeze -= 1
                continue

            dx, dy = px_center - (e.x + 1), py_center - e.y
            dist = abs(dx) + abs(dy)

            if e.type == "melee":
                if dist <= 3:
                    self.player_hp -= 5
                    self.trigger_hit_flash()
                    if self.player_hp <= 0:
                        self.game_over(victory=False)
                else:
                    if abs(dx) > abs(dy):
                        e.x += 1 if dx > 0 else -1
                    else:
                        e.y += 1 if dy > 0 else -1

            elif e.type == "ranged":
                is_aligned_y = self.py <= e.y < self.py + 3
                is_aligned_x = self.px <= e.x < self.px + 5

                if dist <= 30:
                    if e.cooldown <= 0 and (is_aligned_x or is_aligned_y):
                        if is_aligned_y:
                            vx, vy = (1.5 if dx > 0 else -1.5), 0
                        else:
                            vx, vy = 0, (1.5 if dy > 0 else -1.5)

                        self.enemy_projectiles.append(
                            EnemyProjectile(
                                float_x=float(e.x), float_y=float(e.y),
                                x=e.x, y=e.y,
                                vx=vx, vy=vy,
                            )
                        )
                        e.cooldown = 4
                    else:
                        if e.cooldown > 0:
                            e.cooldown -= 1

                        if not is_aligned_y and not is_aligned_x:
                            if abs(dx) > abs(dy):
                                e.y += 1 if dy > 0 else -1
                            else:
                                e.x += 1 if dx > 0 else -1
                        elif dist < 12:
                            e.x += 1 if dx < 0 else -1
                else:
                    e.x -= 1

    def draw_map(self) -> None:
        area = self.query_one("#map-region", Static)
        if not self.game_active:
            return

        grid: list[list[tuple[str, str | None]]] =[
            [(" ", None) for _ in range(self.map_w)] for _ in range(self.map_h)
        ]

        for i, row in enumerate(MIKURU_ART):
            for j, char in enumerate(row):
                if 0 <= self.py + i < self.map_h and 0 <= self.px + j < self.map_w:
                    grid[self.py + i][self.px + j] = (char, "bold magenta")

        for e in self.enemies:
            color = (
                "cyan" if e.freeze > 0 else ("yellow" if e.type == "ranged" else "red")
            )
            symbol = "<R>" if e.type == "ranged" else "<M>"
            for j, char in enumerate(symbol):
                if 0 <= e.y < self.map_h and 0 <= e.x + j < self.map_w:
                    grid[e.y][e.x + j] = (char, color)

        for p in self.enemy_projectiles:
            if 0 <= p.y < self.map_h and 0 <= p.x < self.map_w:
                char = "-" if p.vx != 0 else "|"
                grid[p.y][p.x] = (char, "bold yellow")

        for p in self.player_projectiles:
            if 0 <= p.y < self.map_h and 0 <= p.x < self.map_w:
                char = (
                    ">"
                    if p.type == "attack"
                    else ("@" if p.type == "fire ball" else ("!" if p.type == "classified" else "*"))
                )
                color = (
                    "white"
                    if p.type == "attack"
                    else ("red" if p.type == "fire ball" else ("magenta" if p.type == "classified" else "cyan"))
                )
                grid[p.y][p.x] = (char, f"bold {color}")

        if getattr(self, "beam_active_frames", 0) > 0:
            beam_y = self.py + 1
            for x in range(self.px + 5, self.map_w):
                grid[beam_y][x] = ("=", "bold cyan")
                if x % 2 == 0:
                    if beam_y - 1 >= 0:
                        grid[beam_y - 1][x] = ("+", "cyan")
                    if beam_y + 1 < self.map_h:
                        grid[beam_y + 1][x] = ("+", "cyan")

        lines: list[str] =[]
        for row in grid:
            line_str = ""
            for char, color in row:
                if color:
                    line_str += f"[{color}]{char}[/]"
                else:
                    line_str += char
            lines.append(line_str)
        area.update("\n".join(lines))

    def update_ops_area(self) -> None:
        self.query_one("#ops-region", Static).update("""[b]> TACTICS <[/b]
[white]wasd[/white]        : Move
[white]attack[/white]      : Homing      (DMG:10)
[white]fire ball[/white]   : Burst       (DMG:25)
[white]ice ball[/white]    : Freeze      (DMG:5/2s)
[white]mikuru beam[/white] : Ultimate    (Cost:10)
[white]classified[/white]  : Heavy Shot  (DMG:40, CD:5s)
[white]tea time[/white]    : Heal        (HP+20, CD:8s)
""")

    def update_status_area(self) -> None:
        status = self.query_one("#status-region", Static)
        if not self.game_active:
            return
        m, s = divmod(self.time_elapsed, 60)
        beam_text = (
            "[b][white]READY![/white][/b]"
            if self.beam_ready
            else f"{self.beam_charge}/10"
        )
        bar = f"<{'#' * self.beam_charge}{'-' * (10 - self.beam_charge)}>"

        status.update(f"""[b]OP:[/b] Mikuru
[b]HP:[/b] {self.player_hp}/100
===========================
[b]TIME:[/b] {m:02d}:{s:02d}
[b]FOES:[/b] {len(self.enemies)}
[b]KILL:[/b] {self.kill_count}
===========================
[b]BEAM:[/b]
{bar}
{beam_text}
===========================
[b]SKILL CD:[/b]
classified: {self.classified_cd:.1f}s
tea time : {self.teatime_cd:.1f}s
===========================
[b]Messages:[/b]
{ "\n".join(self.feedback_queue) }
""")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        val = message.value.strip().lower()
        self.query_one(Input).value = ""

        if not self.game_active:
            if val == "quit":
                self.exit()
            else:
                self.show_feedback("Game over. Type 'quit' to exit.", "yellow")
            return

        if val and all(c in "wasd" for c in val):
            for c in val:
                if c == "w":
                    self.py = max(0, self.py - 1)
                elif c == "s":
                    # 基于动态 map_h 的严苛限制
                    self.py = min(self.map_h - 3, self.py + 1)
                elif c == "a":
                    self.px = max(0, self.px - 1)
                elif c == "d":
                    # 基于动态 map_w 的严苛限制
                    self.px = min(self.map_w - 5, self.px + 1)
            self.draw_map()
            self.show_feedback(f"Move:[{val.upper()}]", "cyan")
            return

        if val in ["attack", "fire ball", "ice ball"]:
            px_start, py_start = self.px + 5, self.py + 1
            self.player_projectiles.append(
                PlayerProjectile(
                    float_x=float(px_start), float_y=float(py_start),
                    x=px_start, y=py_start,
                    vx=2.0, vy=0.0,
                    type=val,
                    damage=10 if val == "attack" else (25 if val == "fire ball" else 5),
                    freeze=4 if val == "ice ball" else 0,
                )
            )
            self.show_feedback(f"Cast:{val.upper()}!", "cyan")

        elif val == "mikuru beam":
            if self.beam_ready:
                self.beam_active_frames = 3
                killed = len(self.enemies)
                self.enemies.clear()
                self.enemy_projectiles.clear()
                self.player_projectiles.clear()
                self.handle_kill(killed)
                self.beam_charge, self.beam_ready = 0, False
                self.show_feedback("MIKURU BEAM!!!", "bold #33ff33")
            else:
                self.show_feedback("Beam charging!", "red")
        elif val == "classified":
            if self.classified_cd == 0:
                px_start, py_start = self.px + 5, self.py + 1
                self.player_projectiles.append(
                    PlayerProjectile(
                        float_x=float(px_start), float_y=float(py_start),
                        x=px_start, y=py_start,
                        vx=2.0, vy=0.0,
                        type="classified",
                        damage=40,
                        freeze=0,
                    )
                )
                self.classified_cd = 5
                self.show_feedback("CLASSIFIED SHOT!", "yellow")
            else:
                self.show_feedback(f"classified CD {self.classified_cd:.1f}s", "red")


        elif val == "tea time":
            if self.teatime_cd == 0:
                self.player_hp = min(100, self.player_hp + 20)
                self.teatime_cd = 8
                self.show_feedback("Tea Time +20 HP!", "green")
            else:
                self.show_feedback(f"tea time CD {self.teatime_cd:.1f}s", "red")


        else:
            self.show_feedback("Invalid cmd.", "red")

        self.draw_map()

    def handle_kill(self, count: int):
        self.kill_count += count
        if not self.beam_ready:
            self.beam_charge = min(10, self.beam_charge + count)
            if self.beam_charge == 10:
                self.beam_ready = True

    def trigger_hit_flash(self) -> None:
        monitor = self.query_one("#crt-monitor")
        monitor.add_class("hit-flash")
        self.set_timer(0.1, lambda: monitor.remove_class("hit-flash"))
        self.update_status_area()

    # def show_feedback(self, text: str, color: str = "white") -> None:
    #     self.feedback_text = f"[{color}]{text}[/{color}]"
    #     self.update_status_area()
    def show_feedback(self, text: str, color: str = "white") -> None:
        msg = f"[{color}]{text}[/{color}]"
        self.feedback_queue.append(msg)

        # 超过上限 → 弹出最早的
        if len(self.feedback_queue) > self.feedback_limit:
            self.feedback_queue.pop(0)

        self.update_status_area()



    def game_over(self, victory: bool = False) -> None:
        self.game_active = False
        self.tick_timer.pause()
        self.ai_timer.pause()
        self.clock_timer.pause()

        area = self.query_one("#map-region", Static)
        if victory:
            area.update(
                "\n\n[b][green]   >>> MISSION ACCOMPLISHED <<<\n   SURVIVED 3 MINUTES![/green][/b]"
            )
        else:
            area.update(
                "\n\n[b][red]   >>> SYSTEM FAILURE <<<\n   MIKURU DEFEATED.[/red][/b]"
            )
        self.feedback_queue = ["[yellow]Game over. Type 'quit' to exit.[/yellow]"]
        self.update_status_area()
        self.set_timer(3.0, self.exit)