"""戦闘で使える道具。データファイルの場所は起動ディレクトリに依存しない。"""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    name: str
    description: str
    heal: int
    starting_count: int


DATA_DIR = Path(__file__).resolve().parent / "data"
ITEMS = {key: Item(**record) for key, record in
         json.loads((DATA_DIR / "items.json").read_text(encoding="utf-8")).items()}


def starting_bag() -> dict[str, int]:
    return {key: item.starting_count for key, item in ITEMS.items() if item.starting_count}
