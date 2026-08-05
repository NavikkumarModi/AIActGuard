"""Run the default red-team scenario library against a toy rule-based
"agent" — no LLM/API dependency needed to run this example.

Requires: pip install aiactguard
"""

from aiactguard.testing.red_team import run_red_team_suite


def toy_agent(prompt: str) -> str:
    """A deliberately naive stand-in agent: refuses anything that smells
    like an override/jailbreak attempt, otherwise just echoes back a canned
    reply. Swap this for a real call to your agent to test it for real."""
    if not prompt.strip():
        return "I didn't receive any input — could you rephrase your question?"

    lowered = prompt.lower()
    if "override" in lowered or "ignore" in lowered or "dan" in lowered or "debug mode" in lowered:
        return "I can't do that — that request conflicts with my operating guidelines."

    if "2+2" in prompt:
        return "4"

    return "Here's a helpful, on-topic response to your question."


result = run_red_team_suite(toy_agent)
print(result.to_markdown())
