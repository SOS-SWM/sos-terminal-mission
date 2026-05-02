"""Entry point: python -m haruhi_rpg  OR  uv run haruhi-rpg"""
from haruhi_rpg.ui import HaruhiApp


def main() -> None:
    app = HaruhiApp()
    app.run()


if __name__ == "__main__":
    main()
