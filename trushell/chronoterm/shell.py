from __future__ import annotations

import shlex
from datetime import datetime
from typing import Optional

import pytz
import typer
from rich.console import Console
from rich.text import Text
from rich.table import Table

from .alarms import AlarmManager
from .clock_ascii import clock_ascii
from .sound import play_alarm
from .state import StateStore
from .stopwatch import Stopwatch
from .timezones import TimezoneManager

app = typer.Typer(help="ChronoTerm — time, timezone, alarm, and stopwatch commands.")
console = Console()


class ChronoTerm:
    def __init__(self) -> None:
        self.store = StateStore()
        self.state = self.store.load()
        self.tz = TimezoneManager(store=self.store, state=self.state)
        self.sw = Stopwatch()
        self.alarms = AlarmManager(store=self.store, state=self.state, lock=self.tz.lock, notify=self._notify_alarm)
        self.alarms.start_scheduler()

    def _notify_alarm(self, msg: str) -> None:
        play_alarm()
        console.print(Text(f"\n🔔 {msg}", style="bold red"))


_chrono: ChronoTerm | None = None


def _get_chrono() -> ChronoTerm:
    """Lazy singleton: create ChronoTerm on first access, not at import time."""
    global _chrono
    if _chrono is None:
        _chrono = ChronoTerm()
    return _chrono


def _refresh_state() -> None:
    chrono = _get_chrono()
    chrono.state = chrono.store.load()
    chrono.tz.state = chrono.state
    chrono.alarms.state = chrono.state


def _current_clock_display(clock_format: str) -> tuple[str, str | None]:
    if clock_format == "12h":
        return datetime.now().strftime("%I:%M"), datetime.now().strftime("%p")
    return datetime.now().strftime("%H:%M"), None


def _print_stopwatch_status(action: str) -> None:
    console.print(f"Stopwatch: [bold]{_get_chrono().sw.status()}[/bold] {_get_chrono().sw.render()}")
    if action == "show":
        laps = _get_chrono().sw.render_laps()
        for idx, lap in enumerate(laps, start=1):
            console.print(f"  Lap {idx}: {lap}")


def _is_local_timezone_name(name: str) -> bool:
    local_now = datetime.now().astimezone()
    zone_now = datetime.now(pytz.timezone(name))
    return zone_now.utcoffset() == local_now.utcoffset() and zone_now.tzname() == local_now.tzname()


def _tz_table(tzs: list[str]) -> Table:
    table = Table(title="Favorite Time Zones")
    table.add_column("IANA Name", style="bold cyan")
    if not tzs:
        table.add_row("(none)")
    else:
        for name in tzs:
            label = name
            if _is_local_timezone_name(name):
                label = f"[bold green]{name} (Local)[/bold green]"
            table.add_row(label)
    return table


@app.command()
def now() -> None:
    _refresh_state()
    console.print(_get_chrono().tz.now_table())


@app.command()
def time() -> None:
    _refresh_state()
    state = _get_chrono().store.load()
    clock_text, meridiem = _current_clock_display(state.clock_format)
    console.print(clock_ascii(clock_text, state.time_template))
    if meridiem is not None:
        console.print(f"[bold cyan]{meridiem}[/bold cyan]")
    play_alarm()


@app.command()
def world() -> None:
    _refresh_state()
    console.print(_get_chrono().tz.world_table())


@app.command()
def tz(action: str = typer.Argument("list", help="list | add | remove"), name: Optional[str] = typer.Argument(None, help="IANA Name (e.g. Europe/London)")) -> None:
    _refresh_state()
    if action == "list":
        console.print(_tz_table(_get_chrono().tz.list()))
    elif action == "add" and name:
        try:
            _get_chrono().tz.add(name)
            timezone_obj = pytz.timezone(name)
            aware_datetime = datetime.now(timezone_obj).strftime("%H:%M")
            console.print(f"[green]Added:[/green] {name} [{aware_datetime}]")
        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
    elif action == "remove" and name:
        if _get_chrono().tz.remove(name):
            console.print(f"[yellow]Removed:[/yellow] {name}")
        else:
            console.print(f"[red]Timezone not found in favorites.[/red]")


@app.command()
def alarm(action: str = typer.Argument("list", help="list | add | remove"), time: Optional[str] = typer.Argument(None, help="Time as HH:MM or YYYY-MM-DD HH:MM"), tz: Optional[str] = typer.Option(None, "--tz", help="Specific timezone"), label: Optional[str] = typer.Option(None, "--label", help="Alarm label")) -> None:
    _refresh_state()
    if action == "list":
        console.print(_get_chrono().alarms.alarms_table())
    elif action == "add" and time:
        try:
            alarm_obj = _get_chrono().alarms.add(time_str=time, tz_name=tz, label=label)
            console.print(f"[green]Alarm set:[/green] {alarm_obj['id']} at {alarm_obj['when_iso']}")
        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
    elif action == "remove" and time:
        if _get_chrono().alarms.remove(time):
            console.print(f"[yellow]Removed alarm:[/yellow] {time}")
        else:
            console.print(f"[red]Alarm ID not found.[/red]")


@app.command()
def sw(action: str = typer.Argument("show", help="start | pause | lap | reset | show")) -> None:
    if action == "start":
        _get_chrono().sw.start()
    elif action == "pause":
        _get_chrono().sw.pause()
    elif action == "reset":
        _get_chrono().sw.reset()
    elif action == "lap":
        _get_chrono().sw.lap()
    _print_stopwatch_status(action)


@app.command()
def shell() -> None:
    console.print(_get_chrono().tz.now_table())
    console.print("[bold cyan]Interactive ChronoTerm Shell Started. Type 'exit' to quit.[/bold cyan]")

    while True:
        try:
            text = console.input("[bold blue]chronoterm>[/bold blue] ").strip()
            if not text:
                continue
            if text.lower() in ["exit", "quit"]:
                break
            app(shlex.split(text))
        except SystemExit:
            continue
        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")


def run_shell() -> None:
    try:
        shell()
    finally:
        _get_chrono().alarms.stop_scheduler()


def run() -> None:
    try:
        app()
    finally:
        _get_chrono().alarms.stop_scheduler()


if __name__ == "__main__":
    run()
