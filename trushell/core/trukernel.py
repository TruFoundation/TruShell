from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger
from ..utils.manifest_parser import parse_manifest
from .plugin_manager import PluginManager

# Sentinel value returned when user types 'exit'
EXIT_SENTINEL = "__TRUSHELL_EXIT__"


_kernel_instance: TruKernel | None = None

class TruKernel:
    """Central manifest-driven dispatch engine for TruShell."""

    def __init__(self) -> None:
        global _kernel_instance
        self.logger = get_logger(__name__)
        self.base_dir = Path(__file__).resolve().parents[2]
        self.registry: dict[str, dict[str, Any]] = {}
        self._loaded_modules: dict[str, Any] = {}
        # Initialize plugin manager
        self.plugin_manager = PluginManager.instance(self)
        self._load_manifests()
        # Load plugins after manifests so plugin-registered commands can override
        try:
            self.plugin_manager.load_all()
        except Exception:
            self.logger.exception("PluginManager failed to load plugins")
        _kernel_instance = self  # Store reference for get_kernel()

    # ------------------------------------------------------------------ #
    #  Manifest Loading
    # ------------------------------------------------------------------ #
    def _manifest_path(self, filename: str) -> Path:
        return self.base_dir / "trushell" / "config" / filename

    def _load_manifests(self) -> None:
        builtins = parse_manifest(
            self._manifest_path("builtin_commands.md"), source="builtin"
        )
        plugins = parse_manifest(
            self._manifest_path("plugins.md"), source="plugin"
        )
        aliases = parse_manifest(
            self._manifest_path("my_command_config.md"), source="alias"
        )

        for entry in builtins:
            self._register(entry)
        for entry in plugins:
            self._register(entry)
        for entry in aliases:
            self._register(entry, override=True)

        # Run on_load plugins during init
        for entry in plugins:
            if entry["meta"].get("lifecycle") == "on_load":
                self._execute_entry(entry, args="", init=True)

    def _register(self, entry: dict[str, Any], override: bool = False) -> None:
        command = entry["command"]
        if override or command not in self.registry:
            self.registry[command] = entry
            self.logger.debug(
                "Registered '%s' from %s", command, entry.get("source")
            )
        else:
            self.logger.debug(
                "Command '%s' already registered from %s; skipping %s",
                command,
                self.registry[command].get("source"),
                entry.get("source"),
            )

    # ------------------------------------------------------------------ #
    #  Module Importing (Lazy + Cached)
    # ------------------------------------------------------------------ #
    def _resolve_module_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path
        return (self.base_dir / path).resolve()

    def _import_module(self, path: str):
        resolved = self._resolve_module_path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Module not found: {resolved}")

        # Use resolved path string as key — no hash collision risk
        module_key = str(resolved)
        if module_key in self._loaded_modules:
            return self._loaded_modules[module_key]

        spec = importlib.util.spec_from_file_location(module_key, resolved)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec: {resolved}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        self._loaded_modules[module_key] = module
        self.logger.debug("Loaded module: %s", resolved)
        return module

    # ------------------------------------------------------------------ #
    #  Command Execution
    # ------------------------------------------------------------------ #
    def _execute_entry(
        self, entry: dict[str, Any], args: str = "", init: bool = False
    ) -> str | bool:
        """Execute a registered command entry.

        Returns:
            EXIT_SENTINEL  – user typed 'exit', REPL should stop
            True           – command executed successfully
            False          – command failed (logged, error printed)
        """
        command = entry["command"]
        try:
            module = self._import_module(entry["path"])
            func = getattr(module, entry["function"])
        except (FileNotFoundError, ImportError, AttributeError) as err:
            if not init:
                print("Command not available. Check manifest and module path.")
            self.logger.warning(
                "Failed to load '%s' from %s: %s", command, entry["path"], err
            )
            return False

        try:
            result = func(args)
            # Check for exit sentinel
            if result == EXIT_SENTINEL:
                self.logger.info("Exit command received")
                return EXIT_SENTINEL

            # Special-case TruShell directory jump helper
            if isinstance(result, str) and result.startswith("__TRUSHELL_CD__: "):
                target_path = result.split(": ", 1)[1].strip()
                try:
                    os.chdir(target_path)
                    print(os.getcwd())
                    return True
                except OSError as error:
                    print(f"cd: {error}")
                    self.logger.warning("Failed to change directory to %s: %s", target_path, error)
                    return False

            # Only print if the function explicitly returned a value
            # This prevents the kernel from printing 'None' when functions
            # perform their own prints and return None.
            if result is not None:
                print(result)

            self.logger.debug("Dispatched '%s' → %s", command, entry["path"])
            return True
        except SystemExit:
            # Should never happen if commands use sentinel, but guard anyway
            self.logger.info("SystemExit caught from '%s'", command)
            return EXIT_SENTINEL
        except Exception as err:
            self.logger.exception("Unhandled exception in '%s'", command)
            print(f"Command error: {err}")
            return False

    def execute_command(self, raw_command: str) -> str | bool:
        """Parse and dispatch a single user input line.

        Returns:
            EXIT_SENTINEL – stop the REPL loop
            True          – command handled (success or logged failure)
            False         – command not found AND os passthrough also failed
        """
        trimmed = raw_command.strip()
        if not trimmed:
            return True  # blank line is fine

        parts = trimmed.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Run pre_exec hooks from active plugins. Plugins may modify command/args.
        try:
            for inst in self.plugin_manager.plugins.values():
                try:
                    modified = inst.pre_exec(command, args)
                    if modified and isinstance(modified, tuple) and len(modified) == 2:
                        command, args = modified
                except Exception:
                    self.logger.exception("pre_exec hook failed for plugin %s", getattr(inst, "name", "?"))
        except Exception:
            self.logger.exception("Error running plugin pre_exec hooks")

        # 1. Try manifest registry
        entry = self.registry.get(command)
        if entry is not None:
            result = self._execute_entry(entry, args=args)
            # post_exec hooks
            try:
                output = "" if result is True or result is False else str(result)
                for inst in self.plugin_manager.plugins.values():
                    try:
                        inst.post_exec(command, output)
                    except Exception:
                        self.logger.exception("post_exec hook failed for plugin %s", getattr(inst, "name", "?"))
            except Exception:
                self.logger.exception("Error running plugin post_exec hooks")
            return result

        # 2. Fall back to OS passthrough for unknown commands
        result = self._os_passthrough(command, args)
        # post_exec hooks for os passthrough
        try:
            output = "" if result is True or result is False else str(result)
            for inst in self.plugin_manager.plugins.values():
                try:
                    inst.post_exec(command, output)
                except Exception:
                    self.logger.exception("post_exec hook failed for plugin %s", getattr(inst, "name", "?"))
        except Exception:
            self.logger.exception("Error running plugin post_exec hooks")
        return result

    # ------------------------------------------------------------------ #
    #  OS Passthrough Fallback
    # ------------------------------------------------------------------ #
    def _os_passthrough(self, command: str, args: str) -> bool:
        """Try to run an unregistered command via the host OS shell.

        Special-cases 'cd' because it must change the Python process CWD.
        """
        full_cmd = f"{command} {args}".strip()

        if command == "cd":
            return self._handle_cd(args)

        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if result.returncode == 127:
                    print("Command not found. Type 'help' for available commands.")
                elif stderr:
                    print(stderr, end="", file=sys.stderr)
                return False
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return True
        except FileNotFoundError:
            print(f"Command not found: {command}")
            self.logger.warning("OS command not found: %s", command)
            return False
        except Exception as err:
            print(f"OS command error: {err}")
            self.logger.exception("OS passthrough failed: %s", full_cmd)
            return False

    def _handle_cd(self, args: str) -> bool:
        """Change directory in the Python process so subprocesses inherit it."""
        target = os.path.expandvars(os.path.expanduser(args.strip())) if args else os.path.expanduser("~")
        try:
            os.chdir(target)
            print(os.getcwd())  # Visual feedback that cd worked
            return True
        except FileNotFoundError:
            print(f"cd: no such file or directory: {target}")
            return False
        except PermissionError:
            print(f"cd: permission denied: {target}")
            return False
        except NotADirectoryError:
            print(f"cd: not a directory: {target}")
            return False

    # ------------------------------------------------------------------ #
    #  Public Helpers
    # ------------------------------------------------------------------ #
    def list_commands(self) -> list[str]:
        return sorted(self.registry)


def get_kernel() -> TruKernel:
    """Return the global TruKernel instance.

    Used by commands like help that need a live registry.
    """
    global _kernel_instance
    if _kernel_instance is None:
        _kernel_instance = TruKernel()
    return _kernel_instance