# AtOffice-Shell

AtOffice-Shell is a small Python terminal project that combines three tools in one workspace:

- `PyFunny` for joke output with ASCII characters and sound effects
- `TodoCLI` for a simple SQLite-backed task manager
- `ChronoTerm` for time, timezone, alarm, and stopwatch commands

The `AtOffice shell` brings these tools together into one REPL so you can run commands from a single prompt.

## Features

### 1. AtOffice REPL

The main combined shell is launched from `project.py`. Inside it, you can:

- tell jokes
- manage todos
- use ChronoTerm commands
- open the interactive settings menu

Prompt:

```text
atoffice-shell:
```

### 2. PyFunny

PyFunny uses `pyjokes`, `cowsay`, and sound effects.

Available commands:

- `joke`
- `joke_trex`

The `joke` command can be customized from the settings menu:

- joke character
- joke sound

### 3. TodoCLI

TodoCLI stores tasks in `todos.db`.

Available commands:

- `addtask "Task name" "Category"`
- `deletetask 1`
- `updatetask 1 "New task" "New category"`
- `completetask 1`
- `showtasks`

### 4. ChronoTerm

ChronoTerm can run on its own or through the AtOffice shell.

Available commands:

- `now`
- `time`
- `world`
- `tz list`
- `tz add Asia/Kolkata`
- `tz remove Asia/Kolkata`
- `alarm list`
- `alarm add "07:30" --label Wakeup`
- `alarm remove <alarm_id>`
- `sw show`
- `sw start`
- `sw pause`
- `sw lap`
- `sw reset`

ChronoTerm settings currently support:

- time template selection
- 12-hour / 24-hour clock format

## How To Run

### Option 1: Run the combined AtOffice shell

From the project root:

```bash
python project.py
```

This starts the shared shell where all supported commands can be used.

### Option 2: Run the ChronoTerm shell directly

From the project root:

```bash
python chronoterm_project.py
```

This starts the dedicated ChronoTerm shell.


## Settings Menu

Inside the AtOffice shell, type:

```text
settings
```

This opens the arrow-key settings menu.

Current editable settings:

- `joke`
  - character
  - sound
- `time`
  - template
  - clock format
- `world`
  - clock format

Settings are saved to a JSON state file through ChronoTerm state storage, so choices persist between runs.

## Project Structure

### Root files

- [project.py](project.py)
  Combined AtOffice REPL
- [chronoterm_project.py](chronoterm_project.py)
  Root entry point for ChronoTerm shell
- [pyfunny.py](pyfunny.py)
  Joke commands
- [todocli.py](todocli.py)
  Todo commands
- [database.py](database.py)
  SQLite operations for todos
- [model.py](model.py)
  Todo model
- [settings.py](settings.py)
  Arrow-key settings menu
- [todos.db](todos.db)
  SQLite database file

### ChronoTerm package

- [chronoterm/shell.py](chronoterm/shell.py)
  Main ChronoTerm commands and REPL
- [chronoterm/timezones.py](chronoterm/timezones.py)
  Timezone formatting and world time tables
- [chronoterm/alarms.py](chronoterm/alarms.py)
  Alarm management
- [chronoterm/stopwatch.py](chronoterm/stopwatch.py)
  Stopwatch logic
- [chronoterm/state.py](chronoterm/state.py)
  Persistent JSON-backed settings/state
- [chronoterm/clock_ascii.py](chronoterm/clock_ascii.py)
  ASCII clock templates
- [chronoterm/sound.py](chronoterm/sound.py)
  Alarm sound helper
- [chronoterm/sounds](chronoterm/sounds)
  Audio files used by jokes and alarms

## Dependencies

Based on the current code, the project uses these main Python packages:

- `typer`
- `rich`
- `pyjokes`
- `cowsay`
- `playsound`
- `pytz`

It also uses standard-library modules such as:

- `sqlite3`
- `json`
- `datetime`
- `pathlib`
- `zoneinfo`

## Example Commands

Inside `atoffice-shell`:

```text
joke
showtasks
addtask "Finish README" "Programming"
time
world
tz add Europe/Dublin
settings
```

Inside `chronoterm>`:

```text
now
time
world
tz list
alarm list
sw start
sw show
```

## Notes

- The project is currently Windows-friendly in a few places, especially the settings menu and sound behavior.
- Some commands depend on audio playback support.
- Todo data is stored locally in SQLite.
- ChronoTerm settings are stored in a JSON file managed by `StateStore`.
