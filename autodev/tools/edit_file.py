from .base import Tool, ToolContext, ToolResult


class EditFileTool(Tool):
    name = "edit_file"

    def run(self, context: ToolContext, *, path: str, content: str, **kwargs) -> ToolResult:
        try:
            target = context.safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(ok=True, output=str(path), modified_files=[str(path)])
        except (OSError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))
