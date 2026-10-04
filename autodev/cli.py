import os
import shutil
import shlex
from pathlib import Path
import typer
from .agent import Agent
from .providers.openai_compatible import OpenAICompatibleProvider
from .state import AgentState
from .tools.registry import default_tools

app = typer.Typer(add_completion=False)


@app.command()
def version() -> None:
    """Print the package version."""
    from . import __version__
    typer.echo(__version__)


@app.command()
def doctor() -> None:
    """Check local prerequisites without contacting the model provider."""
    checks = {
        "python": shutil.which("python") or shutil.which("python3"),
        "docker": shutil.which("docker"),
        "cmake": shutil.which("cmake"),
        "ctest": shutil.which("ctest"),
    }
    for name, executable in checks.items():
        typer.echo(f"{name}: {'ok (' + executable + ')' if executable else 'missing'}")


@app.command()
def run(
    repo: Path = typer.Option(..., "--repo", help="Local repository path"),
    task: str = typer.Option(..., "--task", help="Natural-language software task"),
    max_iterations: int = typer.Option(5, "--max-iterations", min=1),
    verify_command: str = typer.Option("cmake -S . -B /tmp/autodev-build && cmake --build /tmp/autodev-build && ctest --test-dir /tmp/autodev-build --output-on-failure", "--verify-command", help="Shell command run in Docker after edits"),
) -> None:
    """Run the bounded coding-agent loop against a local repository."""
    repo = repo.resolve()
    if not repo.is_dir():
        raise typer.BadParameter("repo must be an existing directory")
    missing = [name for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL") if not os.environ.get(name)]
    if missing:
        raise typer.BadParameter("missing environment variables: " + ", ".join(missing))
    provider = OpenAICompatibleProvider(os.environ["LLM_BASE_URL"], os.environ["LLM_API_KEY"], os.environ["LLM_MODEL"])
    state = AgentState(task=task, repository_path=str(repo), max_iterations=max_iterations)
    command = ["sh", "-lc", verify_command]
    result = Agent(state, provider, default_tools(), repo / ".autodev" / "run.jsonl", command).run()
    typer.echo(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
