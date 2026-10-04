import json
from pathlib import Path
from autodev.agent import Agent
from autodev.state import AgentState, Phase
from autodev.tools.base import Tool, ToolContext, ToolResult


class Edit(Tool):
    name = "edit_file"
    def run(self, context: ToolContext, *, path: str, content: str):
        context.safe_path(path).write_text(content, encoding="utf-8")
        return ToolResult(ok=True, output="edited", modified_files=[path])


class Runner(Tool):
    name = "run_command"
    def run(self, context: ToolContext, *, command: list[str], timeout: int):
        return ToolResult(ok=True, output={"stdout": "passed", "stderr": "", "exit_code": 0, "timed_out": False})


class Provider:
    def generate(self, messages):
        return json.dumps({"action": "tool", "phase": "EXECUTE", "tool": "edit_file", "arguments": {"path": "a.txt", "content": "ok"}})


def test_edit_enters_verify_and_finishes_after_command(tmp_path: Path):
    state = AgentState(task="fix", repository_path=str(tmp_path), max_iterations=3)
    result = Agent(state, Provider(), {"edit_file": Edit(), "run_command": Runner()},
                   verify_command=["ctest"]).run()
    assert result.current_phase is Phase.FINISH
    assert result.test_result.exit_code == 0
    assert result.tool_calls == 2
    assert result.iteration == 1
    assert result.verification_runs == 1


def test_finish_success_cannot_bypass_verification(tmp_path: Path):
    class FinishProvider:
        def generate(self, messages):
            return json.dumps({"action": "finish", "status": "success", "summary": "claimed"})

    state = AgentState(task="fix", repository_path=str(tmp_path), max_iterations=2)
    result = Agent(state, FinishProvider(), {"run_command": Runner()}, verify_command=["ctest"]).run()
    assert result.current_phase is Phase.FAILED
    assert result.final_status == "max_iterations reached"
