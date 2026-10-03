from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class ToolContext(BaseModel):
    repository_root: Path

    def safe_path(self, relative_path: str) -> Path:
        root = self.repository_root.resolve()
        candidate = (root / relative_path).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("path escapes repository root")
        return candidate


class ToolResult(BaseModel):
    ok: bool
    output: Any = None
    error: str | None = None
    modified_files: list[str] = Field(default_factory=list)


class Tool(ABC):
    name: str

    @abstractmethod
    def run(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        raise NotImplementedError
