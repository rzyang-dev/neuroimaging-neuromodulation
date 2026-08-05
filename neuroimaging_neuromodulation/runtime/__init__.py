"""Runtime diagnostics and optional external-provider discovery."""

from .diagnostics import check_system, discover_optional_providers

__all__ = ["check_system", "discover_optional_providers"]
