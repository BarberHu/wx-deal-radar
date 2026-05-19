from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import threading
from typing import Callable

from .config import AppConfig, DEFAULT_LOG_PATH
from .notifier import windows_notify
from .rules import RuleHit, evaluate_message
from .wx_client import WxClient


class DealMonitor:
    def __init__(self, config: AppConfig, log_path: Path = DEFAULT_LOG_PATH):
        self.config = config
        self.log_path = log_path
        self.client = WxClient(config.wx_exe)
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.seen: set[tuple[object, object, str]] = set()
        self.last_error = ""
        self.last_check = ""

    def start(self, on_hit: Callable[[RuleHit], None] | None = None) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, args=(on_hit,), daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()

    def running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())

    def scan_once(self) -> list[RuleHit]:
        items = self.client.new_messages(self.config.new_message_limit)
        hits: list[RuleHit] = []
        for item in items:
            hit = evaluate_message(item, self.config)
            if not hit:
                continue
            unique_key = (item.get("timestamp"), item.get("username"), item.get("content", ""))
            if unique_key in self.seen:
                continue
            self.seen.add(unique_key)
            self._append_hit(hit)
            if self.config.enable_windows_notify:
                windows_notify(f"好价命中：{hit.chat}", f"{hit.reason}\n{hit.content[:120]}")
            hits.append(hit)
        self.last_check = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return hits

    def _loop(self, on_hit: Callable[[RuleHit], None] | None) -> None:
        while not self.stop_event.is_set():
            try:
                hits = self.scan_once()
                self.last_error = ""
                if on_hit:
                    for hit in hits:
                        on_hit(hit)
            except Exception as exc:
                self.last_error = str(exc)
            self.stop_event.wait(max(5, self.config.poll_interval_seconds))

    def _append_hit(self, hit: RuleHit) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = asdict(hit)
        row["detected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_hits(log_path: Path = DEFAULT_LOG_PATH, limit: int = 200) -> list[dict]:
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()[-limit:]
    rows = []
    for line in lines:
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(rows))


def clear_hits(log_path: Path = DEFAULT_LOG_PATH) -> None:
    if log_path.exists():
        log_path.unlink()
