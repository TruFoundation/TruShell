from __future__ import annotations

import shlex
import threading
import typer
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.table import Table

try:
    from .alarms import AlarmManager
    from .state import StateStore
    from .stopwatch import Stopwatch
    from .timezones import TimezoneManager
    from .sound import play_alarm
except ImportError:
    from alarms import AlarmManager
    from state import StateStore
    from stopwatch import Stopwatch
    from timezones import TimezoneManager
    from sound import play_alarm

app = typer.Typer(help="ChronoTerm — Type 'shell' for interactive mode or use commands directly.")
console = Console()



def _tz_table(tzs: list[str]) -> Table:
    table = Table(title="Favorite Time Zones")
    table.add_column("IANA Name", style="bold cyan")
    if not tzs:
        table.add_row("(none)")
    else:
        for name in tzs:
            table.add_row(name)
    return table

# --- Persistent App State ---

class ChronoTerm:
    def __init__(self):
        self._state_lock = threading.RLock()
        self._io_lock = threading.Lock()
        
        self.store = StateStore()
        self.state = self.store.load()
        
        self.tz = TimezoneManager(store=self.store, state=self.state, lock=self._state_lock)
        self.sw = Stopwatch()
        self.alarms = AlarmManager(
            store=self.store,
            state=self.state,
            lock=self._state_lock,
            notify=self._notify_alarm,
        )
        self.alarms.start_scheduler()

    def _notify_alarm(self, msg: str) -> None:
        with self._io_lock:
            play_alarm()
            console.print(Text(f"\n🔔 {msg}", style="bold red"))

# Global instance
chrono = ChronoTerm()

# --- Commands ---

@app.command()
def now():
    """Show current local time."""
    console.print(chrono.tz.now_table())

@app.command()
def world():
    """Show current time in your favorite time zones."""
    console.print(chrono.tz.world_table())

@app.command()
def tz(
    action: str = typer.Argument("list", help="list | add | remove"),
    name: Optional[str] = typer.Argument(None, help="IANA Name (e.g. Europe/London)")
):
    """Manage favorite time zones."""
    if action == "list":
        console.print(_tz_table(chrono.tz.list()))
    elif action == "add" and name:
        try:
            chrono.tz.add(name)
            console.print(f"[green]Added:[/green] {name}")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
    elif action == "remove" and name:
        if chrono.tz.remove(name):
            console.print(f"[yellow]Removed:[/yellow] {name}")
        else:
            console.print(f"[red]Timezone not found in favorites.[/red]")

@app.command()
def alarm(
    action: str = typer.Argument("list", help="add | list | remove"),
    time: Optional[str] = typer.Argument(None, help="Time as HH:MM or YYYY-MM-DD HH:MM"),
    tz: Optional[str] = typer.Option(None, "--tz", help="Specific timezone"),
    label: Optional[str] = typer.Option(None, "--label", help="Alarm label")
):
    """Manage alarms."""
    if action == "list":
        console.print(chrono.alarms.alarms_table())
    elif action == "add" and time:
        try:
            a = chrono.alarms.add(time_str=time, tz_name=tz, label=label)
            console.print(f"[green]Alarm set:[/green] {a['id']} at {a['when_iso']}")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
    elif action == "remove" and time:
        if chrono.alarms.remove(time):
            console.print(f"[yellow]Removed alarm:[/yellow] {time}")
        else:
            console.print(f"[red]Alarm ID not found.[/red]")

@app.command()
def sw(
    action: str = typer.Argument("show", help="start | pause | lap | reset | show")
):
    """Stopwatch controls."""
    if action == "start":
        chrono.sw.start()
    elif action == "pause":
        chrono.sw.pause()
    elif action == "reset":
        chrono.sw.reset()
    elif action == "lap":
        chrono.sw.lap()
        play_alarm()
    
    console.print(f"Stopwatch: [bold]{chrono.sw.status()}[/bold] {chrono.sw.render()}")
    if action == "show":
        laps = chrono.sw.render_laps()
        for idx, lap in enumerate(laps, start=1):
            console.print(f"  Lap {idx}: {lap}")

@app.command()
def shell():
    """Enter interactive REPL mode."""
    console.print(chrono.tz.now_table())
    console.print("[bold cyan]Interactive Shell Started. Type 'exit' to quit.[/bold cyan]")
    
    while True:
        try:
            text = console.input("[bold blue]chronoterm>[/bold blue] ").strip()
            if not text:
                continue
            if text.lower() in ["exit", "quit"]:
                break
            
            # This calls the typer app with the input string
            app(shlex.split(text))
        except SystemExit:
            # Prevent shell from closing when a command finishes
            continue
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

def run_shell() -> None:
    try:
        shell()
    finally:
        chrono.alarms.stop_scheduler()

def run():
    try:
        app()
    finally:
        chrono.alarms.stop_scheduler()

if __name__ == "__main__":
    run()
