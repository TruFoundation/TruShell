# 🐄 TruShell

> **A modern, Linux-native productivity shell that integrates seamlessly with your workflow**

TruShell is not just another terminal—it's a **productivity powerhouse** that combines task management, time utilities, jokes for breaks, and a native shell experience. Built for developers who want to stay in flow without switching contexts.

## Why TruShell?

- **All-in-one workspace** - Tasks, time, alarms, and shell in one place
- **Beautiful prompts** - Customizable `trushell ❯` prompt with ASCII art
-  **Linux-first design** - Respects Unix philosophy, works alongside bash/zsh/fish
- **Persistent state** - SQLite-backed todos and settings survive restarts
- **Fun breaks** - Cow/T-Rex jokes with sound effects when you need a laugh
- **Global awareness** - World clocks, timezone manager, alarms, stopwatch
- **Built-in editor** - Quick file editing without leaving the shell

## Installation

### Using pip (Recommended)
```
pip install trushell
```

### From Source
```bash
git clone https://github.com/AkshajSinghal/trushell.git
cd at-office-shell
pip install -e .
```

## Quick Start

```bash
$ trushell
Entering TruShell. Type 'exit' to quit.
trushell ❯ help
Available commands: joke, joke_trex, addtask, deletetask, updatetask, completetask, showtask, now, time, world, tz, alarm, sw, settings, exit, help

trushell ❯ addtask "Review PR" "Work"
Task added.

trushell ❯ showtasks
Todos 💻
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
 # ┃ Todo         ┃ Category ┃ Done   ┃
┡━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ 1 │ Review PR    │ Work     │ ❌     │
└───┴──────────────┴──────────┴────────┘

trushell ❯ time
  __
 / _)
/_)_
 /_)

trushell ❯ joke
 _________________________
< Your Python code works! >
 -------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||

trushell ❯ ls -la  # Native OS commands work too!
total 48
drwxr-xr-x  5 user user 4096 May 29 10:30 .
...
```

## Command Reference

###  Fun & Breaks
| Command | Description | Example |
|---------|-------------|---------|
| `joke` | Random joke with ASCII cow | `joke` |
| `joke-trex` | T-Rex joke with sound | `joke-trex` |

### Task Management
| Command | Description | Example |
|---------|-------------|---------|
| `addtask "<task>" "<category>"` | Add a new todo | `addtask "Fix bug" "Dev"` |
| `deletetask <position>` | Delete task by number | `deletetask 2` |
| `updatetask <pos> "<task>" "<cat>"` | Update task text/category | `updatetask 1 "New text" "Cat"` |
| `completetask <position>` | Mark task as done | `completetask 1` |
| `showtasks` | Display all tasks | `showtasks` |

###  Time & Productivity
| Command | Description | Example |
|---------|-------------|---------|
| `now` | Current local time | `now` |
| `time` | ASCII clock display | `time` |
| `world` | Show favorite timezones | `world` |
| `tz list` | List saved timezones | `tz list` |
| `tz add <IANA>` | Add timezone | `tz add Europe/London` |
| `tz remove <name>` | Remove timezone | `tz remove London` |
| `alarm list` | List alarms | `alarm list` |
| `alarm add "<HH:MM>" --label "X"` | Set alarm | `alarm add "07:30" --label "Morning"` |
| `sw start` | Start stopwatch | `sw start` |
| `sw pause` | Pause stopwatch | `sw pause` |
| `sw lap` | Record lap time | `sw lap` |
| `sw reset` | Reset stopwatch | `sw reset` |
| `sw show` | Show current time | `sw show` |

###  Configuration
| Command | Description | Example |
|---------|-------------|---------|
| `settings` | Interactive settings UI | `settings` |
| `edit <file>` | Edit file in built-in editor | `edit config.txt` |

### Shell Features
| Command | Description | Example |
|---------|-------------|---------|
| `cd <dir>` | Change directory (native) | `cd ~/projects` |
| Any OS command | Falls back to system shell | `ls`, `git status`, etc. |
| `help` | Show available commands | `help` |
| `exit` or `quit` | Exit TruShell | `exit` |

## Customization

Configure your experience with the `settings` command:

```bash
trushell ❯ settings
```

Adjust:
- **Clock style** - Choose ASCII art format
- **Time template** - Customize time display format
- **Joke character** - Switch between cow, trex, dragon, etc.
- **Sound effects** - Enable/disable joke sounds

Settings are stored persistently in your user data directory.

## Architecture

TruShell is built with a modular architecture:

```
trushell/
├── cli.py              # CLI entrypoint & command routing
├── project.py          # Interactive shell REPL loop
├── todocli.py          # Todo management commands
├── pyfunny.py          # Jokes & ASCII art
├── settings.py         # Persistent configuration
├── database.py         # SQLite storage layer
└── chronoterm/         # Time utilities
    ├── shell.py        # ChronoTerm command handler
    ├── state.py        # State management
    └── sounds/         # Sound effect files
```

**Key Design Principles:**
- **SQLite-backed storage** - Todos and settings persist across sessions
- **Platform-safe paths** - Uses OS-specific app data directories
- **Native fallback** - Unrecognized commands pass through to system shell
- **Textual UI** - Modern terminal UI framework for settings & editor

##  TruShell vs Traditional Shells

| Feature | Bash/Zsh/Fish | TruShell |
|---------|---------------|----------|
| Task Management | External tools needed | Built-in |
| Time Utilities | Manual setup | World clocks, alarms, stopwatch |
| Productivity Focus | General purpose | Optimized for workflow |
| Fun Breaks | None | Jokes with ASCII art |
| Learning Curve |  Moderate-High | Low (familiar commands) |
| Extensibility | Plugins/scripts | Python-based |

**TruShell complements your existing shell**—use it for productivity tasks while keeping bash/zsh for system administration.

## ️ Development

### Prerequisites
- Python 3.10+
- [Poetry](https://python-poetry.org/) or pip

### Setup
```bash
git clone https://github.com/AkshajSinghal/trushell.git
cd at-office-shell
poetry install
# or
pip install -e .
```

### Run Tests
```bash
pytest tests/
```

### Build Package
```bash
python -m build
twine upload dist/*
```

## Contributing

Contributions are welcome! Please:
1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Check existing [issues](https://github.com/AkshajSinghal/trushell/issues)
3. Fork and create a pull request

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community guidelines.

## Dependencies

- **[Typer](https://typer.tiangolo.com/)** - Modern CLI framework
- **[Textual](https://textual.textualize.io/)** - Terminal UI toolkit
- **[pyjokes](https://github.com/pyjokes/pyjokes)** - Joke library
- **[cowsay](https://github.com/vaichidrewar/cowsay-python)** - ASCII art
- **[playsound](https://github.com/TaylorSMarks/playsound)** - Audio playback
- **SQLite3** - Built-in database (no extra install needed)

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by the Unix philosophy of small, composable tools
- Built with love for the Linux community
- Thanks to all contributors and early testers

---

## 🌟 Star this repo if TruShell boosts your productivity!

[![GitHub stars](https://img.shields.io/github/stars/AkshajSinghal/trushell?style=social)](https://github.com/AkshajSinghal/at-office-shell)
---

**Made for Linux users who value productivity and fun.**
