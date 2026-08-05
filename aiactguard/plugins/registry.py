from __future__ import annotations

from importlib.metadata import entry_points

from .base import Plugin

DEFAULT_ENTRY_POINT_GROUP = "aiactguard.plugins"


class PluginRegistry:
    """In-process registry of community modules, plus discovery of plugins
    published as Python entry points — the same mechanism pytest, flake8,
    and most of the Python ecosystem use for third-party extensibility, so
    it needs no new runtime dependency (`importlib.metadata` is stdlib).

    A published plugin package registers itself in its own `pyproject.toml`:

        [project.entry-points."aiactguard.plugins"]
        gxp = "aiactguard_gxp_plugin:plugin"

    where `plugin` is a module-level object implementing `Plugin`.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin, *, overwrite: bool = False) -> None:
        if not overwrite and plugin.name in self._plugins:
            raise ValueError(f"A plugin named '{plugin.name}' is already registered. Pass overwrite=True to replace it.")
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Plugin:
        try:
            return self._plugins[name]
        except KeyError:
            raise KeyError(f"No plugin named '{name}' is registered. Registered: {sorted(self._plugins)}") from None

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins)

    def discover_entry_points(self, group: str = DEFAULT_ENTRY_POINT_GROUP) -> list[str]:
        """Load and register every plugin published under `group`. Returns
        the names of newly registered plugins."""
        discovered = []
        for entry_point in entry_points(group=group):
            plugin = entry_point.load()
            self.register(plugin, overwrite=True)
            discovered.append(plugin.name)
        return discovered


_default_registry = PluginRegistry()


def register(plugin: Plugin, *, overwrite: bool = False) -> None:
    _default_registry.register(plugin, overwrite=overwrite)


def get(name: str) -> Plugin:
    return _default_registry.get(name)


def list_plugins() -> list[str]:
    return _default_registry.list_plugins()


def discover_entry_points(group: str = DEFAULT_ENTRY_POINT_GROUP) -> list[str]:
    return _default_registry.discover_entry_points(group)
