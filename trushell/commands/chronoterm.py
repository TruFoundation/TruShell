from __future__ import annotations

import shlex

from trushell.chronoterm.shell import app as chronoterm_app


def _run_chrono_command(raw_command: str) -> None:
    try:
        chronoterm_app(shlex.split(raw_command))
    except SystemExit:
        return
    except Exception as error:
        print(f"ChronoTerm error: {error}")


def run_now(_: str) -> None:
    _run_chrono_command("now")


def run_time(_: str) -> None:
    _run_chrono_command("time")


def run_world(_: str) -> None:
    _run_chrono_command("world")


def run_tz(args: str) -> None:
    if not args.strip():
        _run_chrono_command("tz list")
        return
    _run_chrono_command(f"tz {args.strip()}")


def run_alarm(args: str) -> None:
    if not args.strip():
        _run_chrono_command("alarm list")
        return
    _run_chrono_command(f"alarm {args.strip()}")


def run_sw(args: str) -> None:
    command = "sw" if not args.strip() else f"sw {args.strip()}"
    _run_chrono_command(command)
