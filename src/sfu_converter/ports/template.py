from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TemplateResolverPort(ABC):
    @abstractmethod
    def resolve_template(self, template_path: str | None) -> Path | None:
        """Resolve a template reference to a readable path."""
