"""Registry mapping source type names to adapter classes, for (de)serialising recipes."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from tidesurgedata.sources.base import BaseSource

__all__ = ["BUILTIN_MODULES", "register_source", "registered_sources", "source_from_spec"]

#: Modules whose adapters are registered on first use of the registry. Importing them is cheap:
#: adapters import optional dependencies inside functions.
BUILTIN_MODULES: tuple[str, ...] = (
    "tidesurgedata.sources.fake",
    "tidesurgedata.sources.noaa_coops",
    "tidesurgedata.sources.usgs",
    "tidesurgedata.sources.ea_tide",
    "tidesurgedata.sources.ea_rivers",
    "tidesurgedata.sources.gesla",
    "tidesurgedata.sources.dynamical",
)

_REGISTRY: dict[str, type[BaseSource]] = {}

S = TypeVar("S", bound=type[BaseSource])


def register_source(name: str) -> Callable[[S], S]:
    """Class decorator registering an adapter under ``name`` and setting ``registry_name``.

    Raises
    ------
    ValueError
        If ``name`` is already registered.
    TypeError
        If the class does not subclass :class:`BaseSource`.
    """

    def decorator(cls: S) -> S:
        if not (isinstance(cls, type) and issubclass(cls, BaseSource)):
            raise TypeError(f"{cls!r} must subclass BaseSource to be registered.")
        if name in _REGISTRY:
            raise ValueError(
                f"Source name {name!r} is already registered to {_REGISTRY[name].__qualname__}."
            )
        cls.registry_name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def _load_builtins() -> None:
    for module in BUILTIN_MODULES:
        importlib.import_module(module)


def registered_sources() -> dict[str, type[BaseSource]]:
    """Return a copy of the registry, including all built-in adapters."""
    _load_builtins()
    return dict(_REGISTRY)


def _decode(value: Any) -> Any:
    if isinstance(value, Mapping) and set(value) == {"type", "params"}:
        return source_from_spec(value)
    return value


def source_from_spec(spec: Mapping[str, Any]) -> BaseSource:
    """Build a source from ``{"type": name, "params": {...}}`` (see ``BaseSource.to_spec``).

    Raises
    ------
    KeyError
        If the type is not registered; the message lists known names.
    """
    _load_builtins()
    name = spec["type"]
    try:
        cls = _REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Unknown source type {name!r}. Known types: {', '.join(sorted(_REGISTRY))}"
        ) from None
    params = {k: _decode(v) for k, v in (spec.get("params") or {}).items()}
    return cls(**params)
