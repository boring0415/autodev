import subprocess
from .base import Tool, ToolContext, ToolResult


class GitDiffTool(Tool):
    name = "git_diff"

    def run(self, context: ToolContext, **kwargs) -> ToolResult:
        completed = subprocess.run(["git", "diff", "--"], cwd=context.repository_root, text=True, capture_output=True)
        return ToolResult(ok=completed.returncode == 0, output=completed.stdout, error=completed.stderr or None)
