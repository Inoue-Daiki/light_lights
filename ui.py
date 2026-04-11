from __future__ import annotations

import os


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_enter() -> None:
    input("\nエンターキーで続行")