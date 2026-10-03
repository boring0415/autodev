from .base import Tool, ToolContext, ToolResult


class ReadFileTool(Tool):
    name = "read_file"

    def run(self, context: ToolContext, *, path: str, **kwargs) -> ToolResult:
        try:
            target = context.safe_path(path)
            return ToolResult(ok=True, output=target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))
