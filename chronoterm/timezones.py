from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from rich.table import Table

try:
    from .state import AppState, StateStore
except ImportError:
    from state import AppState, StateStore


def _local_now() -> datetime:
    return datetime.now().astimezone()


def format_dt(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _safe_zoneinfo(name: str) -> ZoneInfo:
    return ZoneInfo(name)


@dataclass
class TimezoneManager:
    store: StateStore
    state: AppState
    lock: threading.Lock | None = None

    def list(self) -> list[str]:
        return list(self.state.timezones)

    def add(self, tz_name: str) -> None:
        _safe_zoneinfo(tz_name)
        if self.lock:
            with self.lock:
                if tz_name not in self.state.timezones:
                    self.state.timezones.append(tz_name)
                    self.store.save(self.state)
            return

        if tz_name not in self.state.timezones:
            self.state.timezones.append(tz_name)
            self.store.save(self.state)

    def remove(self, tz_name: str) -> bool:
        if self.lock:
            with self.lock:
                if tz_name in self.state.timezones:
                    self.state.timezones.remove(tz_name)
                    self.store.save(self.state)
                    return True
                return False

        if tz_name in self.state.timezones:
            self.state.timezones.remove(tz_name)
            self.store.save(self.state)
            return True
        return False

    def now_table(self) -> Table:
        now = _local_now()
        table = Table(title="Current Time")
        table.add_column("Zone", style="bold")
        table.add_column("Time")
        table.add_row(str(now.tzinfo) if now.tzinfo else "Local", format_dt(now))
        return table

    def world_table(self) -> Table:
        now = _local_now()
        table = Table(title="World Time")
        table.add_column("Zone", style="bold")
        table.add_column("Time")
        table.add_row(str(now.tzinfo) if now.tzinfo else "Local", format_dt(now))
        for name in self.state.timezones:
            z = _safe_zoneinfo(name)
            table.add_row(name, format_dt(now.astimezone(z)))
        return table

