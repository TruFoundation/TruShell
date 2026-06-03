from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Todo:
    task: str
    category: str
    date_added: str = field(default_factory=lambda: datetime.now().isoformat())
    date_completed: str | None = None
    status: int = 1
    position: int | None = None
