from __future__ import annotations

import os
from pathlib import Path

from trushell.core.trukernel import TruKernel


def test_execute_entry_handles_trushell_cd_sentinel(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.chdir(tmp_path)

    module_path = tmp_path / "jump_module.py"
    module_path.write_text(
        "def jump(args):\n"
        "    return '__TRUSHELL_CD__: ' + args\n",
        encoding="utf-8",
    )

    entry = {
        "command": "j",
        "path": str(module_path),
        "function": "jump",
    }

    kernel = TruKernel()
    try:
        result = kernel._execute_entry(entry, args=str(target))
        assert result is True
        assert Path(os.getcwd()) == target
    finally:
        # Reset cwd for the rest of the test session if needed
        monkeypatch.chdir(tmp_path)
