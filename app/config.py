from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config.json"
DEFAULT_LOG_PATH = ROOT / "data" / "hits.jsonl"


@dataclass
class ProductRule:
    name: str
    keywords: list[str]
    max_price: float | None = None


@dataclass
class AppConfig:
    wx_exe: str
    poll_interval_seconds: int = 30
    new_message_limit: int = 200
    enable_windows_notify: bool = True
    target_groups: list[str] = field(default_factory=list)
    global_keywords: list[str] = field(default_factory=list)
    blacklist_words: list[str] = field(default_factory=list)
    products: list[ProductRule] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        products = [ProductRule(**item) for item in data.get("products", [])]
        return cls(
            wx_exe=data.get("wx_exe", r"D:\NVM\nvm\node_global\wx.exe"),
            poll_interval_seconds=int(data.get("poll_interval_seconds", 30)),
            new_message_limit=int(data.get("new_message_limit", 200)),
            enable_windows_notify=bool(data.get("enable_windows_notify", True)),
            target_groups=list(data.get("target_groups", [])),
            global_keywords=list(data.get("global_keywords", [])),
            blacklist_words=list(data.get("blacklist_words", [])),
            products=products,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "wx_exe": self.wx_exe,
            "poll_interval_seconds": self.poll_interval_seconds,
            "new_message_limit": self.new_message_limit,
            "enable_windows_notify": self.enable_windows_notify,
            "target_groups": self.target_groups,
            "global_keywords": self.global_keywords,
            "blacklist_words": self.blacklist_words,
            "products": [product.__dict__ for product in self.products],
        }


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    if not path.exists():
        example = path.with_name("config.example.json")
        if example.exists():
            path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    return AppConfig.from_dict(json.loads(path.read_text(encoding="utf-8-sig")))


def save_config(config: AppConfig, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
