from __future__ import annotations

from pathlib import Path


def run_edit_command(args: str) -> None:
    """Open a file in the TruShell editor from a manifest-driven command."""
    if not args.strip():
        print("Usage: edit <filename>")
        return

    file_path = Path(args.strip()).expanduser()
    initial_text = ""
    if file_path.exists():
        try:
            initial_text = file_path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Editor error: {error}")
            return

    try:
        from trushell.cli import TruShellEditor

        TruShellEditor(str(file_path), initial_text=initial_text).run()
    except Exception as error:
        print(f"Editor error: {error}")
