"""Pytest configuration and shared fixtures for TruShell tests."""

import sqlite3

import pytest

from trushell.core import database
from trushell.core.plugin_manager import PluginManager


@pytest.fixture
def in_memory_database(monkeypatch):
    """Use one in-memory SQLite connection for database CRUD tests."""
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.execute(
        """CREATE TABLE todos (
            task TEXT,
            category TEXT,
            date_added TEXT,
            date_completed TEXT,
            status INTEGER,
            position INTEGER
        )"""
    )
    monkeypatch.setattr(database, "get_db_connection", lambda: connection)

    yield connection

    connection.close()


@pytest.fixture(autouse=True)
def reset_plugin_manager():
    """Reset PluginManager singleton after each test to ensure isolation."""
    yield
    PluginManager.reset()
