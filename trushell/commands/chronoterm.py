from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def _format_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def run_now(_: str) -> str:
    """Return the current local time."""
    return _format_time(datetime.now())


def run_time(_: str) -> str:
    """Return the current local time (alias for now)."""
    return run_now("")


def run_world(_: str) -> str:
    """Return current world times in several major zones."""
    zones = {
        "UTC": ZoneInfo("UTC"),
        "New York": ZoneInfo("America/New_York"),
        "London": ZoneInfo("Europe/London"),
        "Tokyo": ZoneInfo("Asia/Tokyo"),
    }
    return "\n".join(f"{label}: {_format_time(datetime.now(tz))}" for label, tz in zones.items())


def run_tz(args: str) -> str:
    """Show a specific timezone or the list of included zones."""
    if not args.strip():
        return "Usage: tz <timezone>"
    try:
        zone = ZoneInfo(args.strip())
        return _format_time(datetime.now(zone))
    except Exception:
        return f"Unknown timezone: {args.strip()}"


def run_alarm(args: str) -> str:
    """Handle simple alarm command placeholders."""
    if not args.strip():
        return "No alarms configured. Use alarm <time> to set one."
    return f"Alarm command received: {args.strip()}"


def run_sw(args: str) -> str:
    """Handle stopwatch-like commands."""
    command = args.strip() or "status"
    return f"Stopwatch command: {command}"