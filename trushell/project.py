from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from pathlib import Path

import typer
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TextArea

from .pyfunny import joke, joke_trex
from .settings import launch_settings
from .todocli import addtask, delete_todo, update_todo, complete_todo, showtask
from .chronoterm.shell import app as chronoterm_app
from .chronoterm.state import StateStore

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

HELP_TEXT = (
    "Available commands: joke, joke_trex, "
    "addtask, deletetask, updatetask, completetask, showtask, "
    "now, time, world, tz, alarm, sw, settings, mkdir, z, exit, help"
)

_Z_STATE_STORE = StateStore()
_Z_ENTRY_LIMIT = 1000
_PREVIOUS_CWD: str | None = None
_CURRENT_DIR: str = os.getcwd()


def _normalize_directory(path: str) -> str:
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))


def _set_current_dir(path: str) -> None:
    global _CURRENT_DIR
    _CURRENT_DIR = _normalize_directory(path)


def _resolve_cd_target(raw_target: str) -> str:
    global _PREVIOUS_CWD
    if raw_target == "-":
        if _PREVIOUS_CWD is None:
            raise ValueError("No previous directory available.")
        return _PREVIOUS_CWD
    return os.path.expanduser(raw_target)


def _ensure_z_state(state):
    if getattr(state, "z_dirs", None) is None:
        state.z_dirs = {}
    return state


def _load_z_state():
    state = _Z_STATE_STORE.load()
    return _ensure_z_state(state)


def _save_z_state(state) -> None:
    _ensure_z_state(state)
    _Z_STATE_STORE.save(state)


def _frecency_score(count: int, last_accessed: float, now: float | None = None) -> float:
    if now is None:
        now = time.time()
    days_since = max(0.0, (now - last_accessed) / 86400)
    return count * (0.95 ** days_since)


def _is_descendant(path: str, root: str) -> bool:
    normalized_path = _normalize_directory(path)
    normalized_root = _normalize_directory(root)
    if normalized_path == normalized_root:
        return True
    try:
        return os.path.commonpath([normalized_root, normalized_path]) == normalized_root
    except ValueError:
        return False


def _cleanup_z_entries(z_dirs: dict[str, dict[str, float | int]]) -> None:
    now = time.time()
    valid_entries: list[tuple[str, dict[str, float | int], float]] = []

    for path, entry in z_dirs.items():
        if not os.path.isdir(path):
            continue
        count = int(entry.get("count", 0))
        last_accessed = float(entry.get("last_accessed", now))
        score = _frecency_score(count, last_accessed, now)
        valid_entries.append((path, entry, score))

    valid_entries.sort(key=lambda item: (-item[2], -float(item[1].get("last_accessed", 0))))
    kept_entries = valid_entries[:_Z_ENTRY_LIMIT]

    z_dirs.clear()
    for path, entry, _ in kept_entries:
        z_dirs[path] = entry


def _add_z_path(path: str) -> None:
    normalized_path = _normalize_directory(path)
    if not os.path.isdir(normalized_path):
        return

    state = _load_z_state()
    entry = state.z_dirs.get(normalized_path, {"count": 0, "last_accessed": 0.0})
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_accessed"] = time.time()
    state.z_dirs[normalized_path] = entry
    _cleanup_z_entries(state.z_dirs)
    _save_z_state(state)


def _find_z_matches(
    pattern: str | None,
    current_only: bool,
    recency_only: bool,
) -> list[tuple[str, dict[str, float | int], float]]:
    state = _load_z_state()
    now = time.time()
    normalized_pattern = pattern.lower() if pattern else None
    cwd = os.getcwd()
    matches: list[tuple[str, dict[str, float | int], float]] = []

    for path, entry in state.z_dirs.items():
        if not os.path.isdir(path):
            continue
        if current_only and not _is_descendant(path, cwd):
            continue
        if normalized_pattern and normalized_pattern not in path.lower():
            continue

        count = int(entry.get("count", 0))
        last_accessed = float(entry.get("last_accessed", now))
        score = _frecency_score(count, last_accessed, now)
        matches.append((path, entry, score))

    if recency_only:
        matches.sort(key=lambda item: -float(item[1].get("last_accessed", 0)))
    else:
        matches.sort(key=lambda item: (-item[2], -float(item[1].get("last_accessed", 0))))

    return matches


def _format_z_list(entries: list[tuple[str, dict[str, float | int], float]]) -> list[str]:
    lines: list[str] = []
    for path, entry, score in entries:
        last_accessed = float(entry.get("last_accessed", 0.0))
        lines.append(f"{score:.4f} {last_accessed:.0f} {path}")
    return lines


def _handle_z_command(command: str, arguments: list[str]) -> bool:
    if command != "z":
        return False

    list_only = False
    current_only = False
    recency_only = False
    help_requested = False
    add_path: str | None = None
    pattern_parts: list[str] = []
    it = iter(arguments)

    for arg in it:
        if arg == "-l":
            list_only = True
        elif arg == "-c":
            current_only = True
        elif arg == "-r":
            recency_only = True
        elif arg == "-h":
            help_requested = True
        elif arg == "--add":
            try:
                add_path = next(it)
            except StopIteration:
                typer.secho("❌ --add requires a path.", fg=typer.colors.RED)
                return True
        elif arg.startswith("-"):
            typer.secho(f"❌ Unknown option: {arg}", fg=typer.colors.RED)
            return True
        else:
            pattern_parts.append(arg)

    if help_requested:
        typer.echo(
            "Usage: z [options] [pattern]\n"
            "Options:\n"
            "  -l        list matching directories with scores\n"
            "  -c        only match under current directory\n"
            "  -r        sort by recency instead of frecency\n"
            "  -h        show this help text\n"
            "  --add <path>  manually add a directory to z history\n"
            "If no pattern is provided, z lists the top 10 directories by score."
        )
        return True

    if add_path:
        normalized_path = _normalize_directory(add_path)
        if not os.path.isdir(normalized_path):
            typer.secho(f"❌ Cannot add path: {normalized_path} is not a directory.", fg=typer.colors.RED)
            return True
        _add_z_path(normalized_path)
        typer.echo(f"Added: {normalized_path}")
        return True

    pattern = " ".join(pattern_parts) if pattern_parts else None
    matches = _find_z_matches(pattern, current_only=current_only, recency_only=recency_only)

    if not pattern and not list_only:
        matches = matches[:10]

    if not matches:
        if pattern or list_only:
            typer.secho("❌ No matching directories found.", fg=typer.colors.YELLOW)
        else:
            typer.echo("No directories tracked yet.")
        return True

    lines = _format_z_list(matches if list_only or not pattern else matches)
    if list_only or not pattern:
        for line in lines:
            typer.echo(line)
        return True

    target = matches[0][0]
    try:
        os.chdir(target)
        _set_current_dir(os.getcwd())
        _add_z_path(os.getcwd())
        _run_external_command(["ls"], shell=False, check=False, cwd=_CURRENT_DIR)
        typer.echo(target)
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)
    return True


def _split_command(user_input: str) -> tuple[str, list[str]]:
    stripped = user_input.strip()
    if not stripped:
        return "", []

    try:
        parts = shlex.split(stripped)
    except ValueError:
        return "", []

    if not parts:
        return "", []

    command = parts[0].lower()
    arguments = parts[1:]
    return command, arguments


def _prompt_command() -> tuple[str, str, list[str]]:
    raw_input = input("trushell ❯ ")
    if "\n" in raw_input:
        typer.secho(
            "⚠️ Please enter commands one at a time.",
            fg=typer.colors.YELLOW,
        )
        return "", "", []

    command, arguments = _split_command(raw_input)
    if not command:
        if raw_input.strip():
            typer.secho(
                "⚠️ Invalid syntax: Check your quotes and escapes.",
                fg=typer.colors.YELLOW,
            )
        return "", "", []

    return raw_input, command, arguments


def _run_external_command(
    command: str | list[str],
    shell: bool = True,
    check: bool = False,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run an external command and optionally profile resource usage.

    When shell=False, the command must be provided as a list of arguments so it is
    executed directly without shell interpretation.
    """
    if cwd is None:
        cwd = _CURRENT_DIR

    if psutil is None:
        return subprocess.run(command, shell=shell, check=check, cwd=cwd)

    process = subprocess.Popen(command, shell=shell, cwd=cwd)
    monitor = psutil.Process(process.pid)
    monitor.cpu_percent(None)
    peak_rss = 0
    peak_cpu = 0.0
    start = time.perf_counter()

    while True:
        try:
            process.wait(timeout=0.05)
            break
        except subprocess.TimeoutExpired:
            try:
                peak_rss = max(peak_rss, monitor.memory_info().rss)
                peak_cpu = max(peak_cpu, monitor.cpu_percent(None))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    if process.returncode is None:
        process.wait()

    try:
        peak_rss = max(peak_rss, monitor.memory_info().rss)
        peak_cpu = max(peak_cpu, monitor.cpu_percent(None))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    elapsed = time.perf_counter() - start
    if peak_rss or peak_cpu:
        typer.secho(
            f"🧪 {elapsed:.2f}s  CPU peak {peak_cpu:.1f}%  RAM peak {peak_rss / 1024**2:.1f} MiB",
            fg=typer.colors.GREEN,
        )

    if check and process.returncode not in (None, 0):
        raise subprocess.CalledProcessError(process.returncode, command)

    return subprocess.CompletedProcess(args=command, returncode=process.returncode)


class TruShellEditor(App):
    """Simple full-screen text editor for TruShell files."""

    inherit_bindings = True

    CSS = """
    Screen { padding: 0; }
    #editor { height: 1fr; }
    Footer { height: 1; }
    """

    BINDINGS = [
        ("ctrl+shift+s", "save_file", "Ctrl+Shift+S Save"),
        ("ctrl+shift+q", "quit_app", "Ctrl+Shift+Q Quit"),
    ]

    def __init__(self, file_path: str, initial_text: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file_path = file_path
        self.file_content = initial_text if initial_text is not None else ""

        if initial_text is None and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    self.file_content = handle.read()
            except OSError as error:
                self.file_content = f"Error reading file: {error}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield TextArea(self.file_content, id="editor_text_area")
        yield Footer()

    def on_mount(self) -> None:
        text_area = self.query_one("#editor_text_area", TextArea)
        text_area.focus()

    def action_save_file(self) -> None:
        text_area = self.query_one("#editor_text_area", TextArea)
        try:
            with open(self.file_path, "w", encoding="utf-8") as handle:
                handle.write(text_area.text)
        except (PermissionError, OSError) as error:
            self.notify(f"Failed to save file: {error}", severity="error")

    def action_quit_app(self) -> None:
        self.exit()


def _handle_joke_command(command: str) -> bool:
    if command in {"joke", "joke_trex", "joke-trex"}:
        if command == "joke":
            typer.echo(joke())
        else:
            typer.echo(joke_trex())
        return True
    return False


def _handle_todo_command(command: str, arguments: list[str]) -> bool:
    if command == "deletetask" and len(arguments) == 1 and arguments[0].isdigit():
        delete_todo(int(arguments[0]) - 1)
        return True

    if command == "addtask" and len(arguments) == 2:
        addtask(arguments[0], arguments[1])
        return True

    if command == "updatetask" and len(arguments) == 3 and arguments[0].isdigit():
        update_todo(int(arguments[0]), arguments[1], arguments[2])
        return True

    if command == "completetask" and len(arguments) == 1 and arguments[0].isdigit():
        complete_todo(int(arguments[0]) - 1)
        return True

    if command == "showtasks" and not arguments:
        showtask()
        return True

    return False


def _handle_edit_command(command: str, arguments: list[str]) -> bool:
    if command != "edit":
        return False

    if not arguments:
        typer.secho("⚠️ Syntax: edit <filename>", fg=typer.colors.YELLOW)
        return True

    file_path = Path(arguments[0])
    initial_text = file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    try:
        TruShellEditor(str(file_path), initial_text=initial_text).run()
    except Exception as error:
        typer.secho(f"Editor error: {error}", fg=typer.colors.RED)

    return True


def _handle_mkdir_command(command: str, arguments: list[str]) -> bool:
    if command != "mkdir":
        return False

    if not arguments:
        typer.secho(
            '⚠️ Syntax: mkdir [-p] <directory> [<directory> ...]',
            fg=typer.colors.YELLOW,
        )
        return True

    create_parents = False
    directories: list[str] = []
    for arg in arguments:
        if arg == "-p":
            create_parents = True
        else:
            directories.append(arg)

    if not directories:
        typer.secho(
            '⚠️ Syntax: mkdir [-p] <directory> [<directory> ...]',
            fg=typer.colors.YELLOW,
        )
        return True

    for directory in directories:
        try:
            os.makedirs(os.path.expanduser(directory), exist_ok=create_parents)
        except OSError as error:
            typer.secho(f"❌ mkdir failed: {error}", fg=typer.colors.RED)
    return True


def _handle_ls_command(command: str, arguments: list[str]) -> bool:
    if command != "ls":
        return False

    directory = os.getcwd() if not arguments else os.path.expanduser(arguments[0])
    try:
        entries = sorted(os.listdir(directory))
        for entry in entries:
            typer.echo(entry)
    except OSError as error:
        typer.secho(f"❌ ls failed: {error}", fg=typer.colors.RED)
    return True


def _handle_local_command(command: str, arguments: list[str]) -> str:
    if command == "addtask" and len(arguments) < 2:
        typer.secho(
            '⚠️ Missing arguments. Syntax: addtask "task-name" "category"',
            fg=typer.colors.YELLOW,
        )
        return "handled"

    if command in {"exit", "quit"}:
        return "exit"
    if _handle_joke_command(command):
        return "handled"
    if _handle_todo_command(command, arguments):
        return "handled"
    if _handle_mkdir_command(command, arguments):
        return "handled"
    if _handle_ls_command(command, arguments):
        return "handled"
    if command == "settings":
        launch_settings()
        return "handled"
    if command == "help":
        typer.echo(HELP_TEXT)
        return "handled"
    return "unhandled"


def _handle_chronoterm_command(raw_command: str, normalized_command: str) -> bool:
    if not re.match(r"^(now|time|world|tz|alarm|sw)\b", normalized_command):
        return False

    try:
        chronoterm_app(shlex.split(raw_command))
    except SystemExit:
        pass
    return True


def _handle_cd_command(command: str, arguments: list[str]) -> bool:
    """Handle cd natively so the shell's working directory changes permanently."""
    global _PREVIOUS_CWD
    if command != "cd":
        return False

    if not arguments:
        typer.secho("Syntax: cd <directory_path>", fg=typer.colors.YELLOW)
        return True

    target_arg = arguments[0]
    try:
        target = _resolve_cd_target(target_arg)
        previous = os.getcwd()
        os.chdir(target)
        _PREVIOUS_CWD = previous
        _set_current_dir(os.getcwd())
        _add_z_path(os.getcwd())
        _run_external_command(["ls"], shell=False, check=False, cwd=_CURRENT_DIR)
    except ValueError as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)
    except OSError as error:
        typer.secho(f"❌ Cannot navigate: {error}", fg=typer.colors.RED)

    return True


def is_dangerous_command(command: str) -> bool:
    """Detect unsafe shell operators or expansions in user input.

    Quotes, spaces, and escaped quote sequences are allowed, but shell
    metacharacters are blocked before external execution.
    """
    if not command.strip():
        return False

    try:
        shlex.split(command)
    except ValueError:
        return True

    dangerous_pattern = re.compile(r"\|\||&&|>>|[|<>;`$&{}()]")
    return bool(dangerous_pattern.search(command))


def _handle_os_fallback(raw_command: str) -> bool:
    """Pass unrecognized commands to the host OS safely using shell=False."""
    command = raw_command.strip()
    if not command:
        return False

    if command.startswith("!"):
        shell_command = command[1:].strip()
        if not shell_command:
            typer.secho("❌ No command provided after '!'.", fg=typer.colors.RED)
            return True
        try:
            _run_external_command(shell_command, shell=True, check=False, cwd=_CURRENT_DIR)
        except (OSError, subprocess.SubprocessError) as error:
            typer.secho("❓ Command not recognized by TruShell or your host OS.", fg=typer.colors.YELLOW)
            typer.secho(f"OS fallback error: {error}", fg=typer.colors.RED)
        return True

    if is_dangerous_command(command):
        typer.secho(
            "⚠️ TruShell blocks shell operators and expansions for safety.",
            fg=typer.colors.YELLOW,
        )
        typer.secho(
            "Use simple external commands without |, >, <, ;, &&, ||, $, `, or $().",
            fg=typer.colors.YELLOW,
        )
        return True

    try:
        parsed_command = shlex.split(command)
    except ValueError:
        typer.secho(
            "❌ Could not parse command. Check your quoting and try again.",
            fg=typer.colors.RED,
        )
        return True

    if not parsed_command:
        return False

    try:
        completed = _run_external_command(parsed_command, shell=False, check=False, cwd=os.getcwd())
    except (OSError, subprocess.SubprocessError) as error:
        typer.secho("❓ Command not recognized by TruShell or your host OS.", fg=typer.colors.YELLOW)
        typer.secho(f"OS fallback error: {error}", fg=typer.colors.RED)
        return True

    if completed.returncode != 0:
        typer.secho(
            f"⚠️ External command exited with status {completed.returncode}.",
            fg=typer.colors.YELLOW,
        )
    return True


def parse_and_execute_command(raw_command: str) -> bool:
    """Parse a command and execute TruShell built-ins or safe external commands."""
    stripped = raw_command.strip()
    if not stripped:
        return True

    command, arguments = _split_command(stripped)
    if not command:
        typer.secho(
            "⚠️ Invalid syntax: Check your quotes and escapes.",
            fg=typer.colors.YELLOW,
        )
        return True

    local_result = _handle_local_command(command, arguments)
    if local_result == "exit":
        return False
    if local_result == "handled":
        return True

    if _handle_chronoterm_command(stripped, command):
        return True
    if _handle_z_command(command, arguments):
        return True
    if _handle_cd_command(command, arguments):
        return True
    if _handle_edit_command(command, arguments):
        return True

    return _handle_os_fallback(stripped)


def run_interactive_shell() -> None:
    """Persistent REPL loop for the TruShell core."""
    typer.secho("Entering TruShell. Type 'exit' to quit.", fg=typer.colors.CYAN)

    while True:
        try:
            raw_command, command, arguments = _prompt_command()
        except (KeyboardInterrupt, EOFError):
            typer.echo("")
            break

        if not command:
            continue

        if not parse_and_execute_command(raw_command):
            break
