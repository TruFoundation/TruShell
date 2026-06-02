# 🐄 TruShell

TruShell is a small productivity shell for people who want task tracking and time
tools next to ordinary terminal commands. It is not meant to replace bash, zsh,
fish, or PowerShell; it sits beside them and handles the lightweight workflow
bits that are easy to forget during a coding session.

## What It Does

- Keeps todos in SQLite with stable display positions.
- Shows local time, world clocks, alarms, and a stopwatch through ChronoTerm.
- Falls back to host operating-system commands when a command is not handled by
  TruShell.
- Opens a Textual editor for quick file edits from the REPL.
- Supports short joke breaks with configurable cowsay characters and optional
  local sound files.

## Install

```bash
pip install trushell
```

For local development:

```bash
git clone https://github.com/AkshajSinghal/trushell.git
cd trushell
pip install -e ".[dev]"
```

After installation, the `trushell` console script is added to your shell `PATH` and can be run directly.

If you are working from the source tree without installing, run:

```bash
PYTHONPATH=. python -m trushell
```

## Quick Start

```bash
$ trushell
Entering TruShell. Type 'exit' to quit.
trushell> help
Available commands: joke, joke_trex, addtask, deletetask, updatetask, completetask, showtask, now, time, world, tz, alarm, sw, settings, exit, help

trushell> addtask "Review PR" "Work"
Task added.

trushell> showtasks
Todos
 #    Todo                 Category      Done
 1    Review PR            Work          open

trushell> time
             ___________________
            |  _______________  |
            | |     14:30     | |
            | |_______________| |
            |  ___ ___ ___ ___  |
            |_|___|___|___|___|_|

trushell> ls
```

## Commands

### Todo

| Command | Description |
| --- | --- |
| `addtask "<task>" "<category>"` | Add a new todo. |
| `deletetask <position>` | Delete by the number shown in `showtasks`. |
| `updatetask <position> "<task>" "<category>"` | Update task text and category. |
| `completetask <position>` | Mark a task as done. |
| `showtasks` | Print the current todo list. |

### Time

| Command | Description |
| --- | --- |
| `now` | Show current local time. |
| `time` | Show the configured ASCII clock. |
| `world` | Show saved time zones. |
| `tz list` | List saved time zones. |
| `tz add <IANA>` | Add a time zone such as `Europe/London`. |
| `tz remove <IANA>` | Remove a saved time zone. |
| `alarm list` | List alarms. |
| `alarm add "<HH:MM>" --label "Name"` | Add an alarm. |
| `alarm remove <id>` | Remove an alarm by ID. |
| `sw start`, `sw pause`, `sw lap`, `sw reset`, `sw show` | Stopwatch controls. |

### Shell And Settings

| Command | Description |
| --- | --- |
| `settings` | Change persisted preferences. |
| `edit <file>` | Open the built-in Textual editor. |
| `cd <dir>` | Change TruShell's current directory. |
| `help` | Print command help. |
| `exit` or `quit` | Leave the REPL. |

Unrecognized commands are executed directly through the host OS without shell
operator expansion. Commands containing pipes, redirects, or chained operators
are rejected for now because they need a proper parser before they can be passed
through safely.

## Storage

Todos and application preferences are stored in SQLite under the platform's user
data directory. Older JSON state files are migrated into SQLite on first load and
renamed to a `.bak` file so the original settings are not silently discarded.

## Architecture Notes

TruShell uses a few terminal libraries, each for a narrow job:

- Typer owns command parsing and CLI entry points.
- Rich owns formatted terminal output such as tables and styled status text.
- Textual is used only for the full-screen editor, where a widget toolkit is
  more appropriate than line-by-line terminal output.

The main modules are:

```text
trushell/
  cli.py                 direct CLI commands
  project.py             interactive REPL and host-command fallback
  todocli.py             todo commands
  database.py            SQLite connection and persistence helpers
  settings.py            prompt-based preference editor
  pyfunny.py             jokes, cowsay rendering, and sound selection
  chronoterm/
    shell.py             time-related commands
    state.py             SQLite-backed app state with JSON migration
    alarms.py            alarm scheduling
    timezones.py         world clock helpers
    stopwatch.py         stopwatch state
    sound.py             platform-specific audio fallback
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```

The package metadata is in `pyproject.toml`; the runtime version exported by
`trushell.__version__` should be kept in sync with it.

For custom joke sounds, prefer `.mp3` and `.wav` assets for the broadest
cross-platform playback support across the available audio backends.

## License

Apache-2.0. See [LICENSE](LICENSE) for details.
