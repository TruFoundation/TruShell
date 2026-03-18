from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.table import Table

try:
    from .state import AppState, StateStore
except ImportError:
    from state import AppState, StateStore


def _local_tz() -> timezone | ZoneInfo:
    tzinfo = datetime.now().astimezone().tzinfo
    return tzinfo or timezone.utc


def _parse_when(time_str: str, tz_name: str | None) -> tuple[datetime, str]:
    try:
        tz = _local_tz() if tz_name in (None, "local") else ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ValueError(f"Unknown timezone '{tz_name}'. Use an IANA name like 'Europe/Dublin'.") from e
    tz_store = "local" if tz_name in (None, "local") else tz_name

    time_str = time_str.strip()
    if " " in time_str:
        # "YYYY-MM-DD HH:MM"
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise ValueError('Time must be "YYYY-MM-DD HH:MM" (e.g., "2026-03-03 09:30").') from e
        dt = dt.replace(tzinfo=tz)
        return dt, tz_store

    # "HH:MM" (today; if passed, next day)
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError as e:
        raise ValueError('Time must be "HH:MM" (24-hour, e.g., "07:15").') from e
    now = datetime.now(tz=tz)
    dt = datetime.combine(now.date(), t, tzinfo=tz)
    if dt <= now:
        dt = dt + timedelta(days=1)
    return dt, tz_store


def _dt_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_local_tz())
    return dt.astimezone(timezone.utc)


def _load_alarm_dt(alarm: dict) -> datetime | None:
    iso = alarm.get("when_iso")
    if not isinstance(iso, str):
        return None
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        return None


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class AlarmManager:
    store: StateStore
    state: AppState
    lock: threading.Lock
    notify: Callable[[str], None]

    _stop_evt: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _thread: threading.Thread | None = None

    def list(self) -> list[dict]:
        with self.lock:
            return list(self.state.alarms)

    def add(self, time_str: str, tz_name: str | None = None, label: str | None = None) -> dict:
        when_dt, tz_store = _parse_when(time_str, tz_name)
        alarm = {
            "id": _short_id(),
            "label": label or "",
            "tz": tz_store,
            "when_iso": when_dt.isoformat(timespec="seconds"),
            "enabled": True,
            "fired": False,
        }
        with self.lock:
            self.state.alarms.append(alarm)
            self.store.save(self.state)
        return alarm

    def remove(self, alarm_id: str) -> bool:
        with self.lock:
            before = len(self.state.alarms)
            self.state.alarms = [a for a in self.state.alarms if a.get("id") != alarm_id]
            changed = len(self.state.alarms) != before
            if changed:
                self.store.save(self.state)
            return changed

    def alarms_table(self) -> Table:
        table = Table(title="Alarms")
        table.add_column("ID", style="bold")
        table.add_column("When")
        table.add_column("TZ")
        table.add_column("Label")
        table.add_column("Status")

        with self.lock:
            alarms = list(self.state.alarms)

        if not alarms:
            table.add_row("-", "-", "-", "-", "No alarms")
            return table

        def sort_key(a: dict) -> tuple[int, str]:
            dt = _load_alarm_dt(a)
            dt_s = dt.isoformat() if dt else "9999"
            return (1 if a.get("fired") else 0, dt_s)

        for a in sorted(alarms, key=sort_key):
            dt = _load_alarm_dt(a)
            when = dt.isoformat(timespec="seconds") if dt else "?"
            status = "FIRED" if a.get("fired") else ("ON" if a.get("enabled", True) else "OFF")
            table.add_row(
                str(a.get("id", "")),
                when,
                str(a.get("tz", "local")),
                str(a.get("label", "")),
                status,
            )

        return table

    def start_scheduler(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt = threading.Event()
        self._thread = threading.Thread(target=self._run, name="ChronoTermAlarmScheduler", daemon=True)
        self._thread.start()

    def stop_scheduler(self) -> None:
        self._stop_evt.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=1.5)

    def _run(self) -> None:
        while not self._stop_evt.is_set():
            fired_any = False
            messages: list[str] = []
            now_utc = datetime.now(timezone.utc)

            with self.lock:
                for alarm in self.state.alarms:
                    if not alarm.get("enabled", True) or alarm.get("fired", False):
                        continue
                    dt = _load_alarm_dt(alarm)
                    if dt is None:
                        continue
                    if _dt_utc(dt) <= now_utc:
                        alarm["fired"] = True
                        fired_any = True
                        label = alarm.get("label") or "Alarm"
                        messages.append(f"ALARM: {label} (id={alarm.get('id')})")

                if fired_any:
                    self.store.save(self.state)

            for msg in messages:
                self.notify(msg)

            time.sleep(0.6)

