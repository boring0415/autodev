import json
import time
import uuid
from pathlib import Path
from typing import Any
from .logging import JsonlLogger
from .state import AgentState, Phase
from .tools.base import Tool, ToolContext


class Agent:
    """Bounded JSON-action loop. The provider proposes one observable action per turn."""

    def __init__(self, state: AgentState, provider: Any = None, tools: dict[str, Tool] | None = None,
                 log_path: Path | None = None, verify_command: list[str] | None = None):
        self.state = state
        self.provider = provider
        self.tools = tools or {}
        self.context = ToolContext(repository_root=Path(state.repository_path))
        self.logger = JsonlLogger(log_path, str(uuid.uuid4())) if log_path else None
        self.verify_command = verify_command

    def can_iterate(self) -> bool:
        return self.state.iteration < self.state.max_iterations

    def run(self) -> AgentState:
        started = time.perf_counter()
        self.state.started_at = time.time()
        if not self.state.run_id:
            self.state.run_id = self.logger.run_id if self.logger else str(uuid.uuid4())
        while self.can_iterate() and self.state.current_phase not in (Phase.FINISH, Phase.FAILED):
            if self.state.current_phase is Phase.VERIFY and self.verify_command:
                self._run_verification()
                continue
            self.state.iteration += 1
            prompt = self._prompt()
            if self.logger:
                self.logger.event(phase=self.state.current_phase.value, event="llm_call", iteration=self.state.iteration)
            self.state.llm_calls += 1
            try:
                raw = self.provider.generate([{"role": "user", "content": prompt}])
                action = json.loads(raw)
                self._apply(action)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                self.state.current_phase = Phase.FAILED
                self.state.final_status = f"invalid agent action: {exc}"
            if self.logger:
                self.logger.event(phase=self.state.current_phase.value, event="iteration_end", iteration=self.state.iteration,
                                  final_status=self.state.final_status,
                                  elapsed_seconds=round(time.perf_counter() - started, 4))
        if self.state.current_phase not in (Phase.FINISH, Phase.FAILED):
            self.state.current_phase = Phase.FAILED
            self.state.final_status = "max_iterations reached"
        self.state.finished_at = time.time()
        self.state.duration_seconds = round(time.perf_counter() - started, 4)
        return self.state

    def _run_verification(self) -> None:
        tool = self.tools.get("run_command")
        if tool is None:
            raise ValueError("verification requires run_command tool")
        result = tool.run(self.context, command=self.verify_command, timeout=120)
        data = result.model_dump()
        self.state.tool_calls += 1
        self.state.verification_runs += 1
        self.state.tool_history.append({"tool": "run_command", "arguments": {"command": self.verify_command, "timeout": 120}, "result": data})
        from .state import CommandResult
        if isinstance(result.output, dict):
            self.state.last_command_result = CommandResult(**result.output)
            self.state.test_result = self.state.last_command_result
        if self.logger:
            self.logger.event(phase=Phase.VERIFY.value, event="tool_call", iteration=self.state.iteration,
                              tool="run_command", arguments={"command": self.verify_command, "timeout": 120}, result=data)
        self.state.verification_passed = result.ok and self.state.last_command_result is not None and self.state.last_command_result.exit_code == 0
        self.state.current_phase = Phase.REFLECT if not self.state.verification_passed else Phase.FINISH
        if self.state.verification_passed:
            self.state.final_status = "verified"
            self.state.summary = "verification command passed"

    def _prompt(self) -> str:
        tool_specs = {
            "list_files": "{}",
            "read_file": '{"path":"relative/path"}',
            "search_code": '{"query":"text"}',
            "edit_file": '{"path":"relative/path","content":"entire file"}',
            "run_command": '{"command":["cmake","--build","build"],"timeout":60}',
            "git_diff": "{}",
        }
        available = "; ".join(f"{name}: {spec}" for name, spec in tool_specs.items() if name in self.tools)
        return ("You are AutoDev, an autonomous coding agent. Return exactly one JSON object. "
                "Allowed actions: "
                '{"action":"tool","phase":"ANALYZE|PLAN|EXECUTE|VERIFY|REFLECT", "tool":"name", "arguments":{}}, '
                '{"action":"plan","items":["..."]}, '
                '{"action":"finish","status":"success|failure","summary":"..."}.\n'
                f"Available tools and argument examples: {available}.\n"
                f"Task: {self.state.task}\nState: {self.state.model_dump_json()}")

    def _apply(self, action: dict[str, Any]) -> None:
        kind = action.get("action")
        if kind == "plan":
            self.state.plan = [str(item) for item in action.get("items", [])]
            self.state.current_phase = Phase.EXECUTE
            return
        if kind == "finish":
            requested_status = str(action.get("status", "success"))
            if requested_status == "success" and self.verify_command and not self.state.verification_passed:
                self.state.current_phase = Phase.REFLECT
                self.state.final_status = "verification required before success"
                self.state.summary = "model finish rejected by verification gate"
            else:
                self.state.summary = str(action.get("summary", ""))
                self.state.final_status = requested_status
                self.state.current_phase = Phase.FINISH
            return
        if kind != "tool":
            raise ValueError("unsupported action")
        tool_name = action["tool"]
        tool = self.tools[tool_name]
        arguments = action.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("tool arguments must be an object")
        result = tool.run(self.context, **arguments)
        result_data = result.model_dump()
        self.state.tool_calls += 1
        self.state.tool_history.append({"tool": tool_name, "arguments": arguments, "result": result_data})
        if self.logger:
            self.logger.event(phase=self.state.current_phase.value, event="tool_call", iteration=self.state.iteration,
                              tool=tool_name, arguments=arguments, result=result_data)
        self.state.modified_files.extend(f for f in result.modified_files if f not in self.state.modified_files)
        self.state.current_phase = Phase(action.get("phase", self.state.current_phase.value))
        if tool_name == "edit_file" and result.ok and self.verify_command:
            self.state.current_phase = Phase.VERIFY
        if tool_name == "run_command" and isinstance(result.output, dict):
            from .state import CommandResult
            command_result = CommandResult(**result.output)
            self.state.last_command_result = command_result
            self.state.test_result = command_result
