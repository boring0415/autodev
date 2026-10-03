import json
from pathlib import Path
from autodev.agent import Agent
from autodev.state import AgentState, Phase
from autodev.tools.base import Tool, ToolContext, ToolResult


class RepoTool(Tool):
    name = "repo_edit"
    def run(self, context: ToolContext, *, path: str, content: str):
        target = context.safe_path(path)
        target.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, output="edited", modified_files=[path])


class ScriptedProvider:
    def __init__(self):
        self.actions = [
            {"action": "plan", "items": ["edit bug"]},
            {"action": "tool", "phase": "EXECUTE", "tool": "repo_edit", "arguments": {"path": "main.cpp", "content": "fixed"}},
            {"action": "finish", "status": "success", "summary": "verified"},
        ]
    def generate(self, messages):
        return json.dumps(self.actions.pop(0))


def test_full_minimal_edit_loop(tmp_path: Path):
    (tmp_path / "main.cpp").write_text("bug", encoding="utf-8")
    state = AgentState(task="fix bug", repository_path=str(tmp_path), max_iterations=3)
    result = Agent(state, ScriptedProvider(), {"repo_edit": RepoTool()}, tmp_path / "run.jsonl").run()
    assert result.current_phase is Phase.FINISH
    assert (tmp_path / "main.cpp").read_text(encoding="utf-8") == "fixed"
    assert result.modified_files == ["main.cpp"]
    assert "tool_call" in (tmp_path / "run.jsonl").read_text(encoding="utf-8")
