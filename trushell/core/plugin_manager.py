from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from .plugin_api import TruPlugin

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    pass


_instance: "PluginManager" | None = None


class PluginManager:
    """Singleton manager for TruShell plugins.

    Plugins are discovered under `~/.trushell/plugins/` by default.
    """

    def __init__(self, kernel) -> None:
        self.kernel = kernel
        self.plugin_dir = Path.home() / ".trushell" / "plugins"
        self._plugins: Dict[str, TruPlugin] = {}
        self._plugin_meta: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._blacklist: set[str] = set()

    @classmethod
    def instance(cls, kernel=None) -> "PluginManager":
        global _instance
        if _instance is None:
            if kernel is None:
                raise RuntimeError("PluginManager requires a kernel for first initialization")
            _instance = PluginManager(kernel)
        return _instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance. Used for testing."""
        global _instance
        _instance = None

    def discover(self) -> List[Path]:
        candidates: List[Path] = []
        # user plugin directory (~/.trushell/plugins)
        if self.plugin_dir.exists():
            for child in self.plugin_dir.iterdir():
                if child.is_dir() and (child / "__init__.py").exists():
                    candidates.append(child)
        # repository-bundled plugins (trushell/plugins)
        try:
            repo_plugins = Path(__file__).resolve().parents[1] / "plugins"
            if repo_plugins.exists():
                for child in repo_plugins.iterdir():
                    if child.is_dir() and (child / "__init__.py").exists():
                        candidates.append(child)
        except Exception:
            logger.debug("No repository plugins directory found")
        return candidates

    def _read_metadata(self, plugin_path: Path) -> Dict:
        meta_file = plugin_path / "plugin.json"
        if not meta_file.exists():
            return {}
        try:
            return json.loads(meta_file.read_text(encoding="utf8"))
        except Exception:
            logger.exception("Failed to parse plugin.json for %s", plugin_path)
            return {}

    def _check_requirements(self, meta: Dict, name: str) -> None:
        requires = meta.get("requires", [])
        for pkg in requires:
            try:
                import importlib

                if importlib.util.find_spec(pkg) is None:
                    logger.warning("Plugin '%s' requires '%s'. Install via pip.", name, pkg)
            except Exception:
                logger.warning("Plugin '%s' requires '%s'. Install via pip.", name, pkg)

    def _warn_security(self, plugin_path: Path, name: str) -> None:
        try:
            src = (plugin_path / "__init__.py").read_text(encoding="utf8")
            if "os.system" in src or "subprocess.run" in src:
                logger.warning("Plugin '%s' contains direct system calls; review for security.", name)
        except Exception:
            pass

    def load_all(self) -> None:
        with self._lock:
            candidates = self.discover()
            for path in candidates:
                name = path.name
                if name in self._blacklist:
                    logger.info("Plugin '%s' is blacklisted; skipping", name)
                    self._plugin_meta[name] = {"status": "blacklisted", "version": None}
                    continue

                meta = self._read_metadata(path)
                try:
                    self._check_requirements(meta, name)
                    self._warn_security(path, name)
                    plugin = self._load_plugin_module(path, name, meta)
                    if plugin:
                        self._plugins[name] = plugin
                        self._plugin_meta[name] = {
                            "status": "active",
                            "version": getattr(plugin, "version", meta.get("version")),
                            "description": getattr(plugin, "description", meta.get("description")),
                        }
                        logger.info("Loaded plugin: %s (%s)", name, self._plugin_meta[name]["version"])
                except PluginLoadError as err:
                    logger.exception("Failed to load plugin '%s': %s", name, err)
                    self._plugin_meta[name] = {"status": "error", "error": str(err)}

    def _load_plugin_module(self, path: Path, name: str, meta: Dict) -> Optional[TruPlugin]:
        init_py = path / "__init__.py"
        spec = importlib.util.spec_from_file_location(f"trushell.plugins.{name}", init_py)
        if spec is None or spec.loader is None:
            raise PluginLoadError("cannot create spec")
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        except Exception as exc:
            raise PluginLoadError(exc)

        # Find a plugin class in the module
        plugin_cls = None
        for obj in module.__dict__.values():
            try:
                if isinstance(obj, type) and issubclass(obj, TruPlugin) and obj is not TruPlugin:
                    plugin_cls = obj
                    break
            except Exception:
                continue

        if plugin_cls is None:
            raise PluginLoadError("no TruPlugin subclass found")

        # Instantiate and run on_load
        instance = plugin_cls()

        # Validate name vs builtins
        if instance.name in self.kernel.list_commands():
            logger.warning("Plugin name '%s' conflicts with existing command; plugin may override commands.", instance.name)

        try:
            instance.on_load(self.kernel)
        except Exception as exc:
            logger.exception("Plugin '%s' on_load failed: %s", name, exc)
            raise PluginLoadError(exc)

        return instance

    @property
    def plugins(self) -> Dict[str, TruPlugin]:
        return self._plugins

    def get_plugin(self, name: str) -> Optional[TruPlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict]:
        out: List[Dict[str, Any]] = []
        for plugin in self._plugins.values():
            out.append({
                "name": plugin.name,
                "version": plugin.version,
                "active": True,
                "description": getattr(plugin, "description", ""),
            })
        for name, info in self._plugin_meta.items():
            if name in self._plugins:
                continue
            out.append({
                "name": name,
                "version": info.get("version"),
                "active": False,
                "status": info.get("status"),
                "description": info.get("description", ""),
                "error": info.get("error"),
            })
        return out

    def disable_plugin(self, name: str) -> None:
        with self._lock:
            self._blacklist.add(name)
            plugin = self._plugins.pop(name, None)
            if plugin:
                try:
                    plugin.on_unload()
                except Exception:
                    logger.exception("Error during unload of %s", name)
                self._plugin_meta[name] = {
                    "status": "disabled",
                    "version": getattr(plugin, "version", None),
                    "description": getattr(plugin, "description", ""),
                }


__all__ = ["PluginManager"]
