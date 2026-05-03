from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.timer import Timer
from textual.widgets import Static

import pygame


ROOT_DIR = Path(__file__).resolve().parent
ENDING_BGM = ROOT_DIR / "assets" / "haruhi.mp3"

CREDIT_LINES = [
    "[b][white]SOS TERMINAL MISSION[/white][/b]",
    "",
    "[cyan]ENDING CREDIT SEQUENCE[/cyan]",
    "",
    "Story / System Design",
    "[white]Machillka, Sheshenxian, Asttear and the SOS Brigade[/]",
    "",
    "Terminal Operations",
    "[white]Textual Runtime[/]",
    "",
    "Emergency Support",
    "[white]Mikuru Beam Department[/]",
    "",
    "Worldline Stabilization",
    "[purple]You[/]",
    "",
    "[yellow]No matter how many loops it took,[/yellow]",
    "[yellow]the signal finally made it through.[/yellow]",
]


class EndingCreditScene(App[None]):
    CSS = """
    Screen {
        align: center middle;
        background: #050505;
    }

    #crt-monitor {
        width: 96%;
        height: 96%;
        layout: vertical;
        background: #001100;
        color: #33ff33;
        border: double #33ff33;
        padding: 1 2;
    }

    .box {
        border: solid #33ff33;
        padding: 0 1;
        height: auto;
    }

    #credits-region,
    #footer-region {
        border-title-color: #33ff33;
    }

    #credits-region {
        content-align: left middle;
        height: 1fr;
    }

    #footer-region {
        margin-top: 1;
        height: 3;
        content-align: center middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.credit_index = 0
        self.visible_lines: list[str] = []
        self.roll_complete = False
        self.roll_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Container(id="crt-monitor"):
            yield Static(id="credits-region", classes="box")
            yield Static(id="footer-region", classes="box")

    def on_mount(self) -> None:
        self.query_one("#credits-region").border_title = " ENDING CREDIT "

        self.query_one("#footer-region").border_title = " TRANSMISSION "
        self.query_one("#footer-region", Static).update("SOS Brigade Presents...")

        self._play_bgm()
        self._roll_next_line()

    def _play_bgm(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(ENDING_BGM))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(loops=-1, fade_ms=1000)

    def _render_credits(self) -> None:
        self.query_one("#credits-region", Static).update("\n".join(self.visible_lines))

    def _stop_roll_timer(self) -> None:
        if self.roll_timer is None:
            return

        try:
            self.roll_timer.stop()
        except Exception:
            pass

        self.roll_timer = None

    def _roll_next_line(self) -> None:
        self.roll_timer = None

        if self.credit_index >= len(CREDIT_LINES):
            self.roll_complete = True
            self.query_one("#footer-region", Static).update(
                "Transmission complete. Thank you for your playing!"
            )
            return

        self.visible_lines.append(CREDIT_LINES[self.credit_index])
        self.credit_index += 1
        self._render_credits()

        if self.credit_index < len(CREDIT_LINES):
            self.roll_timer = self.set_timer(0.8, self._roll_next_line)
        else:
            self.roll_complete = True
            self.query_one("#footer-region", Static).update(
                "Transmission complete. Thank you for your playing!"
            )

    def on_unmount(self) -> None:
        self._stop_roll_timer()
        if pygame.mixer.get_init():
            pygame.mixer.music.fadeout(800)


if __name__ == "__main__":
    EndingCreditScene().run()
