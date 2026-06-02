🐄 TruShell - a lightweight, context‑aware shell for developers
===========================================================

TruShell is not a full replacement for bash or zsh. It is a small
utility shell that sits next to your normal terminal and helps you
track tasks, check times, set alarms, and run ordinary commands.

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

To run from source:
```
    git clone https://github.com/AkshajSinghal/trushell
    cd trushell
    pip install -e .
    PYTHONPATH=. python -m trushell
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
trushell/chronoterm/sounds/ – it will appear in the ‘settings’ menu.


License
-------

Apache 2.0 – see LICENSE file in the repository.
