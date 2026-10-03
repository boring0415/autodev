import pytest
from autodev.agent import Agent
from autodev.state import AgentState


def test_agent_respects_max_iterations():
    state = AgentState(task="fix", repository_path=".", iteration=2, max_iterations=2)
    assert not Agent(state).can_iterate()


def test_max_iterations_must_be_positive():
    with pytest.raises(ValueError):
        AgentState(task="fix", repository_path=".", max_iterations=0)
