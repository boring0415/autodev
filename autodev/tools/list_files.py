from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class ListFilesTool(Tool):
    name = "list_files"

    def run(self, context: ToolContext, **kwargs) -> ToolResult:
        root = context.repository_root.resolve()
        paths = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
        return ToolResult(ok=True, output=paths)
