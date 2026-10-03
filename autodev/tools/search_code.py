from .base import Tool, ToolContext, ToolResult


class SearchCodeTool(Tool):
    name = "search_code"

    def run(self, context: ToolContext, *, query: str, **kwargs) -> ToolResult:
        matches = []
        root = context.repository_root.resolve()
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if query in line:
                        matches.append({"path": path.relative_to(root).as_posix(), "line": number, "text": line})
            except (OSError, UnicodeError):
                continue
        return ToolResult(ok=True, output=matches)
