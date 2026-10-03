import json
from pathlib import Path
from autodev.agent import Agent
from autodev.state import AgentState, Phase
from autodev.tools.base import Tool, ToolContext, ToolResult


class FakeTool(Tool):
    name = "fake"
    def run(self, context: ToolContext, **kwargs):
        return ToolResult(ok=True, output={"seen": True})


class FakeProvider:
    def __init__(self):
        self.responses = [
            json.dumps({"action": "plan", "items": ["inspect"]}),
            json.dumps({"action": "tool", "phase": "ANALYZE", "tool": "fake", "arguments": {}}),
            json.dumps({"action": "finish", "status": "success", "summary": "done"}),
        ]
    def generate(self, messages):
        return self.responses.pop(0)


def test_agent_loop_is_bounded_and_logs(tmp_path: Path):
    state = AgentState(task="demo", repository_path=str(tmp_path), max_iterations=3)
    log_path = tmp_path / "run.jsonl"
    result = Agent(state, FakeProvider(), {"fake": FakeTool()}, log_path).run()
    assert result.current_phase is Phase.FINISH
    assert result.iteration == 3
    assert result.llm_calls == 3
    assert result.tool_calls == 1
    assert result.duration_seconds is not None
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 7
