# 🐄 TruShell 
A lightweight, context‑aware shell for developers

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

---

It is written in Python and uses a SQLite database for todos.
When you type a command TruShell does not recognise, it passes it
directly to the host system’s shell (bash, cmd, etc.).


What makes TruShell useful
--------------------------

  *  Built‑in todo manager with stable task numbers
     – add, delete, update, complete, show
     – categories and done/open status stored in SQLite

  *  Time tools without leaving your terminal
     – ‘now’ shows local time
     – ‘world’ lists your saved time zones
     – ‘alarm’ schedules one‑shot reminders
     – ‘sw’ controls a stopwatch (start, pause, lap, reset)

  *  Jokes, because work needs breaks
     – ‘joke’ shows a random joke with cowsay‑style art
     – ‘joke_trex’ for a T‑Rex joke, with optional sound
     – you can change the character via settings

  *  Built‑in full‑screen editor (Textual)
     – ‘edit <filename>’ opens a quick editor inside the REPL

  *  Safe external command execution
     – piped / chained commands are blocked
     – external commands run without a shell when possible
     – optional CPU/memory monitoring if psutil is present


Quick start
-----------

Install from PyPI:

    `pip install trushell`

Then run:

    `trushell`

Inside TruShell, type ‘help’ for a list of commands.
Type ‘exit’ or Ctrl‑D to quit.

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
| `z [options] [pattern]` | Jump to or list frequently used directories by fuzzy path matching. |
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

Core commands (most useful)
----------------------------

Todo management:
    `addtask "task description" "Category"`
    `deletetask <number>`
    `updatetask <number> "new desc" "new category"`
    `completetask <number>`
    `showtasks`

Time & alarms:
    now
    time                     – shows an ASCII clock
    world
    tz list | add <zone> | remove <id>
    alarm list | add HH:MM --label "name" | remove <id>
    sw start | pause | lap | reset | show

Other:
    edit <filename>
    cd <dir>
    settings                 – change preferences interactively
    joke
    joke_trex


Configuration
-------------

Run the ‘settings’ command inside TruShell. You can change:

  *  clock style (LCD, wrist watch, desktop clock)
  *  12h / 24h format
  *  cowsay character for jokes (cow, trex, dragon, tux, kitty, …)
  *  joke sound (choose from available .mp3 or .wav files)

Settings are saved automatically.

## Star History

<a href="https://www.star-history.com/?repos=AkshajSinghal%2FTruShell&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=TruFoundation/TruShell&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=TruFoundation/TruShell&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=TruFoundation/TruShell&type=date&legend=top-left" />
 </picture>
</a>


Where data lives
----------------

Todos and application preferences are stored in SQLite. The database
file is placed in the platform’s standard user data directory:

  *  Linux:   ~/.local/share/trushell/
  *  macOS:   ~/Library/Application Support/trushell/
  *  Windows: %APPDATA%\trushell\

Old JSON state files (from earlier versions) are automatically
renamed to .bak and migrated into SQLite on first run.


Security notes
--------------

TruShell blocks commands that contain ‘|’, ‘>’, ‘&&’, or ‘||’ to prevent
accidental chaining inside the REPL. External commands are executed
using Python’s subprocess without a shell when possible.

If you want to use shell operators, exit TruShell and run the command
in your normal shell.


Development
-----------

Tests:    pytest tests/
Version:  kept in sync between trushell/__init__.py and pyproject.toml

To add a custom sound for jokes, put an .mp3 or .wav file into
trushell/sounds/ – it will appear in the ‘settings’ menu.


License
-------

Apache 2.0 – see LICENSE file in the repository.
