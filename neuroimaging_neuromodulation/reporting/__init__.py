"""Result reporting and provenance utilities."""

from .html import render_target_report
from .manifest import write_target_manifest

__all__ = ["render_target_report", "write_target_manifest"]
