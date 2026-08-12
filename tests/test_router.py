from alf.router import route
from alf.routes import Route


def test_route_system_question():
    assert route("What operating system am I running?") == Route.SYSTEM


def test_route_os_question():
    assert route("What OS am I running?") == Route.SYSTEM


def test_route_general_question_to_llm():
    assert route("What does pytest -q mean?") == Route.LLM


def test_route_memory_question():
    assert route("What did we decide about SearXNG?") == Route.MEMORY


def test_route_research_question():
    assert route("What is the latest version of Python?") == Route.RESEARCH
