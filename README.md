# 🐄 TruShell

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/trushell.svg)](https://pypi.org/project/trushell/)

**TruShell** is a lightweight, productivity shell for developers. Written in Python, it blends a powerful interactive REPL with built-in tools for task management, time tracking, data visualization, and system navigation. When you type a command TruShell doesn’t recognize, it seamlessly passes it to your host system’s shell (bash, zsh, cmd, etc.), making it a frictionless drop-in replacement for your daily terminal workflow.

## Features

*   **Interactive REPL**: A polished command-line interface with history support, tab completion, and emoji-rich prompts (with fallbacks for compatibility).
*   **Seamless OS Passthrough**: Unrecognized commands are automatically executed by your host operating system's shell.
*   **Task Management**: Built-in todo list with add, complete, update, delete, and show capabilities, persisted in SQLite.
*   **ChronoTerm Suite**:
    *   `now` / `time`: Display current local time.
    *   `world`: World clock for multiple timezones.
    *   `tz`: Timezone conversion utilities.
    *   `alarm`: Set and manage alarms.
    *   `sw`: Stopwatch functionality.
*   **Data Visualization**: `csv-view` command for quick inspection of CSV files directly in the terminal.
*   **Developer Tools**:
    *   `edit`: Launch a full-screen TUI text editor (powered by Textual) for quick file edits.
    *   `j`: Quick directory jumping/navigation.
*   **Fun & Morale**:
    *   `joke`: Get a random programming joke.
    *   `joke-trex`: Get a T-Rex themed joke.
*   **Extensible Plugin System**: Load custom plugins from `~/.trushell/plugins/` or bundled repository plugins to extend functionality.
*   **Settings TUI**: A user-friendly terminal UI for managing application preferences.
*   **Cross-Platform**: Works on Linux, macOS, and Windows.

## Architecture

TruShell is built on a modern, modular architecture centered around the **TruKernel**:

*   **TruKernel**: The core dispatch engine that manages command registration, execution, and plugin lifecycle. It uses a manifest-driven approach (`builtin_commands.md`) to register commands.
*   **Plugin Manager**: Discovers and loads plugins dynamically. Plugins can register new commands, override built-ins, and hook into `pre_exec` and `post_exec` events.
*   **SQLite Storage**: Todos, alarms, stopwatch state, and user preferences are stored in a SQLite database located in the platform-specific user data directory:
    *   **Linux**: `~/.local/share/trushell/`
    *   **macOS**: `~/Library/Application Support/trushell/`
    *   **Windows**: `%APPDATA%\trushell\`
*   **Libraries**:
    *   **[Typer](https://typer.tiangolo.com/)**: For CLI entry points and argument parsing.
    *   **[Rich](https://rich.readthedocs.io/)**: For beautiful terminal output (tables, styled text).
    *   **[Textual](https://textual.textualize.io/)**: For the full-screen TUI editor and settings interface.
    *   **[prompt_toolkit](https://prompt-toolkit.readthedocs.io/)**: For advanced readline features, history, and completion in the REPL.

## Installation

### Prerequisites

*   Python 3.10 or higher.

### Install via pip

```bash
pip install trushell
```

### Install from Source

```bash
git clone https://github.com/TruFoundation/TruShell.git
cd TruShell
pip install .
```

## Usage

Start TruShell by running:

```bash
trushell
```

You will enter the interactive REPL:

```
trushell /home/user/project ❯ 
```

### Built-in Commands

| Command | Description |
| :--- | :--- |
| `help [command]` | Show help message or details for a specific command. |
| `exit` / `quit` | Exit TruShell. |
| `task` | Manage todos (subcommands: `add`, `complete`, `delete`, `show`, `update`). |
| `joke` | Tell a random joke. |
| `joke-trex` | Tell a T-Rex joke. |
| `now` | Show current local time. |
| `time` | Alias for `now`. |
| `world` | Show world clocks. |
| `tz` | Convert time between timezones. |
| `alarm` | Manage alarms. |
| `sw` | Stopwatch controls. |
| `csv-view <file>` | View a CSV file in a formatted table. |
| `edit <file>` | Open a file in the built-in TUI editor. |
| `j <dir>` | Jump to a directory (shortcut for `cd`). |
| `settings` | Open the settings TUI. |
| `<any other command>` | Passed directly to your host shell (e.g., `ls`, `git status`, `python script.py`). |

### Examples

```bash
# Add a todo
trushell ~/dev ❯ task add "Fix login bug" "Work"

# List todos
trushell ~/dev ❯ task show

# Check the time in Tokyo
trushell ~/dev ❯ world Tokyo

# Edit a file
trushell ~/dev ❯ edit main.py

# Run a system command
trushell ~/dev ❯ git status
```

## 🔌 Plugin Development

TruShell supports plugins written in Python. To create a plugin:

1.  Create a directory in `~/.trushell/plugins/` (e.g., `my_plugin`).
2.  Add an `__init__.py` file containing a class that inherits from `TruPlugin`.
3.  (Optional) Add a `plugin.json` for metadata.

Example `__init__.py`:

```python
from trushell.core.plugin_api import TruPlugin

class MyPlugin(TruPlugin):
    name = "my_plugin"
    version = "0.1.0"
    
    def on_load(self, kernel):
        print("MyPlugin loaded!")
        
    def pre_exec(self, command: str, args: str) -> tuple[str, str]:
        # Modify command before execution
        return command, args
        
    def post_exec(self, command: str, output: str):
        # Process output after execution
        pass
```

## Development

### Setup

```bash
git clone https://github.com/TruFoundation/TruShell.git
cd TruShell
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

TruShell uses `ruff` and `black` for linting and formatting.

```bash
ruff check .
black .
```

## 📂 Project Structure

```
trushell/
├── cli.py              # CLI entry point and REPL loop
├── __main__.py         # Allows running as python -m trushell
├── commands/           # Built-in command implementations
│   ├── core.py         # Help, exit
│   ├── tasks.py        # Todo management
│   ├── chronoterm.py   # Time, alarms, stopwatch
│   ├── data.py         # CSV viewer
│   ├── editor.py       # TUI editor
│   ├── joke.py         # Jokes
│   ├── nav.py          # Navigation helpers
│   └── settings.py     # Settings TUI
├── core/               # Core architecture
│   ├── trukernel.py    # Command dispatch engine
│   ├── plugin_manager.py # Plugin loading and management
│   ├── database.py     # SQLite helpers
│   └── models.py       # Data models
├── plugins/            # Bundled example plugins
├── sounds/             # Audio assets for alarms
└── config/             # Configuration manifests
    ├── builtin_commands.md
    └── plugins.md
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## Star History

If TruShell helps streamline your workflow, consider giving it a star on GitHub! It helps others discover the project and motivates continued development.

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

Apache 2.0 – see [LICENSE](LICENSE.md) file in the repository.
