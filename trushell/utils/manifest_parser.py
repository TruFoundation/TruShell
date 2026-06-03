from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .logger import get_logger


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1].strip()
    return value


def _strip_brackets(value: str) -> str:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1].strip()
    return value


def _parse_meta_token(token: str) -> tuple[str, str] | None:
    content = token.strip()[1:-1].strip()
    if ":" not in content:
        return None
    key, value = content.split(":", 1)
    return key.strip().lower(), value.strip()


def parse_manifest(manifest_path: Path, source: str = "manifest") -> list[dict[str, Any]]:
    """Parse a manifest file and return a list of validated command entries."""
    logger = get_logger()
    entries: list[dict[str, Any]] = []

    if not manifest_path.exists():
        logger.warning("Manifest file not found: %s", manifest_path)
        return entries

    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as error:
        logger.warning("Unable to read manifest %s: %s", manifest_path, error)
        return entries

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split(";") if part.strip()]
        command: str | None = None
        function: str | None = None
        path: str | None = None
        meta: dict[str, str] = {}
        malformed = False

        for part in parts:
            if part.startswith("#"):
                break
            if part.startswith("{") and part.endswith("}"):
                parsed = _parse_meta_token(part)
                if parsed is None:
                    logger.warning(
                        "Malformed metadata in %s at line %s: %s",
                        manifest_path,
                        line_number,
                        part,
                    )
                    malformed = True
                    break
                key, value = parsed
                if key in {"cmd", "alias"}:
                    command = value.lower()
                else:
                    meta[key] = value
            elif part.startswith('"') and part.endswith('"'):
                function_name = _strip_quotes(part)
                function_name = function_name.removesuffix("()")
                if not function_name:
                    logger.warning(
                        "Empty function name in %s at line %s: %s",
                        manifest_path,
                        line_number,
                        part,
                    )
                    malformed = True
                    break
                function = function_name
            elif part.startswith("[") and part.endswith("]"):
                raw_path = _strip_brackets(part)
                if not raw_path:
                    logger.warning(
                        "Empty path in %s at line %s: %s",
                        manifest_path,
                        line_number,
                        part,
                    )
                    malformed = True
                    break
                path = os.path.expanduser(raw_path)
            else:
                logger.warning(
                    "Unknown manifest token in %s at line %s: %s",
                    manifest_path,
                    line_number,
                    part,
                )
                malformed = True
                break

        if malformed or command is None or function is None or path is None:
            logger.warning(
                "Skipping invalid manifest entry in %s at line %s.",
                manifest_path,
                line_number,
            )
            continue

        entries.append(
            {
                "command": command,
                "function": function,
                "path": path,
                "meta": meta,
                "source": source,
            }
        )

    return entries
