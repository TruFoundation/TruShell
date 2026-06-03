from __future__ import annotations

import sys
import typer

from . import __version__
from .core.trukernel import TruKernel
from .project import run_interactive_shell

app = typer.Typer(name="trushell", help="TruShell manifest-driven launcher.")
kernel = TruKernel()


def app_with_lower() -> None:
    """Entry point that normalizes the first argument to lowercase for case-insensitive invocation."""
    if len(sys.argv) > 1:
        sys.argv[1] = sys.argv[1].lower()
        if sys.argv[1] not in {"--help", "-h", "version"}:
            raw = " ".join(sys.argv[1:])
            kernel.execute_command(raw)
            return
    app()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Launch the REPL when no command is provided."""
    if ctx.invoked_subcommand is None:
        run_interactive_shell()


@app.command("version")
def version() -> None:
    """Show the installed TruShell version."""
    typer.echo(__version__)
