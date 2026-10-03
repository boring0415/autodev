from pathlib import Path
from autodev.sandbox.docker_runner import DockerRunner
from .base import Tool, ToolContext, ToolResult


class RunCommandTool(Tool):
    name = "run_command"

    def __init__(self, runner: DockerRunner | None = None):
        self.runner = runner or DockerRunner()

    def run(self, context: ToolContext, *, command: list[str], timeout: int = 30, **kwargs) -> ToolResult:
        result = self.runner.run(command, repository_root=context.repository_root, timeout=timeout)
        return ToolResult(ok=result.exit_code == 0, output=result.model_dump(), error=result.stderr or None)
