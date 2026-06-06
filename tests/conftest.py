"""Pytest configuration and shared fixtures for TruShell tests."""

import pytest
from trushell.core.plugin_manager import PluginManager


@pytest.fixture(autouse=True)
def reset_plugin_manager():
    """Reset PluginManager singleton after each test to ensure isolation."""
    yield
    PluginManager.reset()
