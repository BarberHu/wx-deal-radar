from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class WxClient:
    wx_exe: str

    def new_messages(self, limit: int = 200) -> list[dict[str, Any]]:
        proc = subprocess.run(
            [self.wx_exe, "new-messages", "-n", str(limit), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        text = proc.stdout.strip()
        return json.loads(text) if text else []

    def sessions(self, limit: int = 200) -> list[dict[str, Any]]:
        proc = subprocess.run(
            [self.wx_exe, "sessions", "-n", str(limit), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        text = proc.stdout.strip()
        return json.loads(text) if text else []
