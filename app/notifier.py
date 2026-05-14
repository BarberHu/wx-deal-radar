from __future__ import annotations

import json
import subprocess


def windows_notify(title: str, message: str) -> None:
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$n=New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon=[System.Drawing.SystemIcons]::Information; "
        "$n.Visible=$true; "
        f"$n.ShowBalloonTip(8000, {json.dumps(title)}, {json.dumps(message)}, "
        "[System.Windows.Forms.ToolTipIcon]::Info); "
        "Start-Sleep -Milliseconds 8500; $n.Dispose()"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
