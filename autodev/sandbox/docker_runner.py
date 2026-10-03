import subprocess
from pathlib import Path
from pydantic import BaseModel


class DockerResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False


class DockerRunner:
    def __init__(self, image: str = "python:3.12-slim"):
        self.image = image

    def run(self, command: list[str], *, repository_root: Path, timeout: int = 30) -> DockerResult:
        if not command or any(not isinstance(part, str) or not part for part in command):
            return DockerResult(stderr="command must be a non-empty list of strings", exit_code=2)
        if timeout <= 0:
            return DockerResult(stderr="timeout must be positive", exit_code=2)
        docker_command = [
            "docker", "run", "--rm", "--network", "none",
            "--cpus", "1", "--memory", "512m", "--pids-limit", "128",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "-v", f"{repository_root.resolve()}:/workspace", "-w", "/workspace",
            self.image, *command,
        ]
        try:
            completed = subprocess.run(docker_command, text=True, capture_output=True, timeout=timeout)
            return DockerResult(stdout=completed.stdout, stderr=completed.stderr, exit_code=completed.returncode)
        except subprocess.TimeoutExpired as exc:
            return DockerResult(stdout=exc.stdout or "", stderr=exc.stderr or "", timed_out=True)
