import json
import shutil
import subprocess
from pathlib import Path
import pytest
from autodev.agent import Agent
from autodev.state import AgentState, Phase
from autodev.tools.registry import default_tools


pytestmark = pytest.mark.integration


def _docker_available() -> bool:
    return shutil.which("docker") is not None and subprocess.run(["docker", "info"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _docker_available(), reason="Docker engine unavailable")
@pytest.mark.parametrize("tool", ["g++", "cmake", "ctest"])
def test_cpp_sandbox_tool_smoke(tool):
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--cpus", "1", "--memory", "512m",
         "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
         "autodev-cpp-sandbox:latest", tool, "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not _docker_available(), reason="Docker engine unavailable")
def test_real_cpp_agent_loop_in_docker(tmp_path: Path):
    source = Path(__file__).parents[1] / "benchmarks" / "cpp_bug_001"
    repo = tmp_path / "repo"
    shutil.copytree(source, repo)
    original = (repo / "main.cpp").read_text(encoding="utf-8")
    fixed = original.replace(
        "std::accumulate(values.begin(), values.end(), 0) / values.size()",
        "static_cast<double>(std::accumulate(values.begin(), values.end(), 0)) / values.size()",
    )

    class ScriptedProvider:
        def __init__(self):
            self.actions = [
                {"action": "tool", "phase": "ANALYZE", "tool": "list_files", "arguments": {}},
                {"action": "tool", "phase": "ANALYZE", "tool": "read_file", "arguments": {"path": "main.cpp"}},
                {"action": "plan", "items": ["replace integer division with floating point division"]},
                {"action": "tool", "phase": "EXECUTE", "tool": "edit_file", "arguments": {"path": "main.cpp", "content": fixed}},
                {"action": "tool", "phase": "REFLECT", "tool": "edit_file", "arguments": {"path": "main.cpp", "content": fixed}},
            ]

        def generate(self, messages):
            if self.actions:
                return json.dumps(self.actions.pop(0))
            return json.dumps({"action": "finish", "status": "failure", "summary": "scripted retry exhausted"})

    state = AgentState(task="fix calculate_average", repository_path=str(repo), max_iterations=6)
    result = Agent(state, ScriptedProvider(), default_tools(), repo / ".autodev" / "run.jsonl",
                    ["sh", "-lc", "cmake -S . -B /tmp/autodev-build && cmake --build /tmp/autodev-build && ctest --test-dir /tmp/autodev-build --output-on-failure"]).run()
    assert result.current_phase is Phase.FINISH, result.model_dump_json()
    assert result.verification_passed, result.model_dump_json()
    assert result.test_result is not None and result.test_result.exit_code == 0
    assert (repo / "main.cpp").read_text(encoding="utf-8") == fixed
