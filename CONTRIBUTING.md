# Contributing to AIActGuard

## Setup

```bash
git clone https://github.com/NavikkumarModi/AIActGuard.git
cd AIActGuard
python3 -m venv .venv
.venv/bin/pip install -e ".[langchain,crewai,claude-agent-sdk,langgraph,autogen,openai-agents,postgres,dev]"
```

## Running tests

```bash
.venv/bin/pytest -q
```

Tests for the CrewAI and Claude Agent SDK adapters are duck-typed against those frameworks' object shapes, so they run without the frameworks installed. Tests that need a real framework install (see `tests/*_live.py`) skip themselves via `pytest.importorskip` if it's missing locally — CI installs everything so they always run there.

`tests/test_postgres_store.py` needs a reachable Postgres database — set `AIACTGUARD_TEST_POSTGRES_DSN`, or it defaults to `postgresql:///aiactguard_test` (create it with `createdb aiactguard_test`). Skips cleanly if none is reachable; CI runs a real Postgres service.

## Design principles (read before adding a module)

- **Draft, flag, or check — never certify.** Every module in this project is explicit that it doesn't perform a legal or formal determination (conformity assessment, prohibited-practice determination, etc.). See the README's Scope section for the current boundary list.
- **Show what you can't infer, don't fabricate it.** Report generators take a `questionnaire` dict for fields the code can't know (system description, who's affected, intended purpose) and render a visible `NEEDS INPUT` marker when one's missing — see `aiactguard/core/questionnaire.py`. Follow this pattern for new report-style modules.
- **Dependency-light.** Core (`aiactguard/core/`, `aiactguard/policy/`, `aiactguard/storage/`) has no framework dependencies (`PostgresAuditStore` is the one exception, behind the `postgres` extra). Adapters duck-type against the target framework's object shapes where the framework allows it (`crewai_adapter.py`, `claude_agent_sdk_adapter.py`), avoiding a hard import; where the framework's messages need a real `isinstance` check to route on (LangChain, AutoGen, OpenAI Agents SDK), the adapter hard-imports it behind a helpful `ImportError`. `langgraph_adapter.py`'s `make_guard()` has zero LangGraph dependency at all — only `interrupt_approver` needs it, and imports it lazily inside the function body.
- **Reuse `GuardCore`.** Any new integration surface that needs to classify → gate → log an action should go through `aiactguard.core.guard.GuardCore`, not reimplement that sequence — see how the existing adapters use it.
- **Reuse `MarkdownReport`.** Every report/mapping/testing module renders its output through `aiactguard.core.markdown.MarkdownReport` rather than hand-building a `lines.append(...)` list — keep new generators consistent with that.

## Adding a jurisdiction- or industry-specific module

Most likely this belongs as a **plugin**, not a core addition — see the README's "Writing a plugin" section and [examples/plugins/example_gxp_plugin.py](examples/plugins/example_gxp_plugin.py). Core stays scoped to the EU AI Act; plugins are where GxP, financial-services, or other domain-specific modules live.

## Before submitting a PR

- Open an issue first for anything non-trivial, so we can agree on scope before you write code.
- Run the full test suite.
- Update the README's module roadmap table or Contributing section if you're adding user-facing behavior.
