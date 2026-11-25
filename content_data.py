"""Local, editable game definitions (UTF-8 JSON)."""
import json
from pathlib import Path

def load_content(name: str):
    return json.loads((Path(__file__).resolve().parent / "content" / name).read_text(encoding="utf-8"))
