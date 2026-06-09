from __future__ import annotations

import csv
import shlex
from itertools import islice
from pathlib import Path

from rich.console import Console
from rich.table import Table


def _render_markup_message(message: str) -> str:
    console = Console(record=True)
    console.print(message)
    return console.export_text(styles=True)


def run_csv_view(args: str) -> str:
    """Render a CSV file as a Rich table."""
    arguments = shlex.split(args or "")
    if not arguments:
        return _render_markup_message("[red]Error: No file specified.[/red]")

    file_path = Path(arguments[0]).expanduser()
    if not file_path.exists():
        return _render_markup_message(f"[red]Error: File '{file_path}' not found.[/red]")

    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(4096)
            if not sample.strip():
                return _render_markup_message("[yellow]Warning: File is empty.[/yellow]")
            handle.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
            except csv.Error:
                delimiter = "\t" if "\t" in sample else ","
                dialect = csv.excel_tab if delimiter == "\t" else csv.excel

            reader = csv.reader(handle, dialect)
            headers = next(reader, None)
            if headers is None:
                return _render_markup_message("[yellow]Warning: File is empty.[/yellow]")

            rows = list(islice(reader, 50))
            remaining = sum(1 for _ in reader)

    except FileNotFoundError:
        return _render_markup_message(f"[red]Error: File '{file_path}' not found.[/red]")
    except csv.Error:
        return _render_markup_message("[red]Error: Invalid CSV format.[/red]")
    except OSError as error:
        return _render_markup_message(f"[red]Error: Unable to read file: {error}[/red]")

    table = Table(show_header=True, header_style="bold cyan", row_styles=["white", "grey93"], expand=False)
    for header in headers:
        table.add_column(str(header or ""))

    for row in rows:
        normalized = [str(cell) for cell in row[: len(headers)]]
        if len(normalized) < len(headers):
            normalized.extend([""] * (len(headers) - len(normalized)))
        table.add_row(*normalized)

    if remaining:
        table.caption = f"...and {remaining} more rows"

    console = Console(record=True)
    console.print(table)
    return console.export_text(styles=True)
