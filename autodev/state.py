from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Phase(str, Enum):
    ANALYZE = "ANALYZE"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REFLECT = "REFLECT"
    FINISH = "FINISH"
    FAILED = "FAILED"


class CommandResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False


class AgentState(BaseModel):
    task: str
    repository_path: str
    current_phase: Phase = Phase.ANALYZE
    plan: list[str] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = Field(default=5, gt=0)
    tool_history: list[dict[str, Any]] = Field(default_factory=list)
    modified_files: list[str] = Field(default_factory=list)
    last_command_result: CommandResult | None = None
    test_result: CommandResult | None = None
    final_status: str = "pending"
    summary: str = ""
    run_id: str = ""
    started_at: float | None = None
    finished_at: float | None = None
    duration_seconds: float | None = None
    llm_calls: int = 0
    tool_calls: int = 0
    verification_runs: int = 0
    verification_passed: bool = False
