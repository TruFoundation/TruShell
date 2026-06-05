from __future__ import annotations

import os
from io import StringIO
from pathlib import Path

from rich.console import Console
from rich.table import Table


def _render_markup_message(message: str) -> str:
    console = Console(record=True, file=StringIO())
    console.print(message)
    return console.export_text(styles=True)


def _is_hidden_path(path: Path, base: Path) -> bool:
    try:
        relative = path.relative_to(base)
    except ValueError:
        return False
    return any(part.startswith(".") for part in relative.parts)


def _relevance_key(path: Path, query: str, base: Path) -> tuple[int, int, int, int, str]:
    lowered_name = path.name.lower()
    exact_name = 0 if lowered_name == query else 1
    ends_with_query = 0 if lowered_name.endswith(query) else 1
    normalized = str(path.relative_to(base).as_posix()).lower()
    index = normalized.find(query)
    index_score = index if index >= 0 else 9999
    depth = len(path.relative_to(base).parts)
    return (exact_name, ends_with_query, index_score, depth, normalized)


def run_jump(args: str) -> str:
    query = args.strip()
    if not query:
        return _render_markup_message(f"[red]No directories found matching '{query}'.[/red]")

    cwd = Path.cwd()
    query_lower = query.lower()
    matches: list[Path] = []

    for path in cwd.rglob("*"):
        if not path.is_dir():
            continue

        if _is_hidden_path(path, cwd):
            continue

        relative = path.relative_to(cwd)
        if len(relative.parts) > 3:
            continue

        if query_lower in str(relative.as_posix()).lower():
            matches.append(path.resolve())

    if not matches:
        return _render_markup_message(f"[red]No directories found matching '{query}'.[/red]")

    matches.sort(key=lambda path: _relevance_key(path, query_lower, cwd))

    if len(matches) == 1:
        return f"__TRUSHELL_CD__: {matches[0]}"

    top_matches = matches[:5]
    console = Console(record=True, file=StringIO())
    table = Table(show_header=True, header_style="bold cyan", row_styles=["white", "grey93"], expand=False)
    table.add_column("Path", style="cyan")

    for path in top_matches:
        table.add_row(str(path))

    console.print(table)
    console.print("[yellow]Multiple matches found. Please be more specific.[/yellow]")
    return console.export_text(styles=True)
