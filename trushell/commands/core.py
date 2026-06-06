from __future__ import annotations

import importlib
import inspect
import os
import subprocess


def run_help(args: str) -> None:
    """Display available commands by reading the manifest registry.
    
    If args contains a command name, print its docstring if available.
    Otherwise, list all available commands.
    """
    # Import here to avoid circular dependency if trukernel imports core
    """Display available commands or the docstring for a specific command."""
    from trushell.core.trukernel import get_kernel

    kernel = get_kernel()
    
    command_name = args.strip().lower() if args else None
    
    # If a specific command is requested, show its help
    if command_name and command_name in kernel.registry:
        entry = kernel.registry[command_name]
        try:
            module = kernel._import_module(entry["path"])
            func = getattr(module, entry["function"], None)
            if func and func.__doc__:
                print(f"Help for '{command_name}':")
                print(func.__doc__)
                return
        except Exception:
            pass
        print(f"No detailed help available for '{command_name}'.")
        return
    
    # Otherwise, list all commands
    cmds = sorted(kernel.registry.keys())
    print("Available commands:")
    col_width = max(len(c) for c in cmds) + 2
    cols = 4
    for i, cmd in enumerate(cmds):
        print(f"  {cmd:<{col_width}}", end="")
        if (i + 1) % cols == 0:
            print()
    if len(cmds) % cols != 0:
        print()
    print("\nType 'help <command>' for more info.")


def run_exit(_: str) -> str:
    """Signal TruKernel to exit the REPL loop cleanly.
    
    Returns a special sentinel string instead of raising SystemExit.
    The kernel checks for this return value and breaks its loop.
    """
    return "__TRUSHELL_EXIT__"


def run_settings(args: str) -> None:
    """Open the TruShell settings manager."""
    try:
        from trushell.core.settings import launch_settings
        launch_settings()
    except ImportError:
        print("Settings module not available.")
    except Exception as e:
        print(f"Settings error: {e}")


def run_os_passthrough(args: str) -> int:
    """Generic wrapper that passes args directly to the OS shell.
    
    Args:
        args: The full argument string after the command name.
              e.g., for 'ls -la /tmp', args = '-la /tmp'
    
    Returns:
        The subprocess return code (0 = success).
    """
    if not args:
        print("Usage: <command> [args]")
        return 1
    try:
        result = subprocess.run(args, shell=True)
        return result.returncode
    except FileNotFoundError:
        print(f"Command not found in PATH.")
        return 127
    except Exception as e:
        print(f"OS command error: {e}")
        return 1


def run_cd_command(args: str) -> None:
    """Change directory. Updates Python process CWD so subsequent
    os_passthrough commands inherit the new directory.
    
    Note: This does NOT update the terminal emulator's displayed path.
    That is an inherent limitation of Python-based shells.
    """
    if not args:
        target = os.path.expanduser("~")
    else:
        target = os.path.expandvars(os.path.expanduser(args.strip()))
    
    try:
        os.chdir(target)
        # Print new path so user knows cd succeeded
        print(os.getcwd())
    except FileNotFoundError:
        print(f"cd: no such file or directory: {target}")
    except PermissionError:
        print(f"cd: permission denied: {target}")
    except NotADirectoryError:
        print(f"cd: not a directory: {target}")