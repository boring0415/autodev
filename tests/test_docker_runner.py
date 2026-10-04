from pathlib import Path
from unittest.mock import patch
from autodev.sandbox.docker_runner import DockerRunner


def test_docker_command_timeout(tmp_path):
    with patch("autodev.sandbox.docker_runner.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(["docker"], 1)):
        result = DockerRunner().run(["sh", "-c", "sleep 10"], repository_root=Path(tmp_path), timeout=1)
    assert result.timed_out


def test_docker_rejects_invalid_command(tmp_path):
    result = DockerRunner().run([], repository_root=Path(tmp_path), timeout=1)
    assert result.exit_code == 2


def test_missing_docker_is_structured(tmp_path):
    with patch("autodev.sandbox.docker_runner.subprocess.run", side_effect=FileNotFoundError("docker missing")):
        result = DockerRunner().run(["g++", "--version"], repository_root=Path(tmp_path))
    assert result.exit_code == 127
