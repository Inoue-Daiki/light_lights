from __future__ import annotations

import os
import subprocess
from typing import Callable

PromptChoice = Callable[[str, set[str]], str]


def clear_screen() -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "cls"], check=False)
    else:
        subprocess.run(["clear"], check=False)


def wait_for_enter() -> None:
    input("\nエンターキーで続行")
    clear_screen()


def prompt_choice(prompt: str, options: set[str]) -> str:
    while True:
        answer = input(prompt).strip().lower()
        if answer in options:
            return answer
        print("入力が不正です。もう一度入力してください。")