# AIActGuard

**Drop-in EU AI Act compliance for any agent framework — audit trails, risk classification, and human-approval gates in one decorator.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange)](#)

AIActGuard is a lightweight middleware layer that any existing agent stack can adopt without ripping out its framework. It is **not** another agent orchestrator — it makes the one you already use (LangChain, CrewAI, AutoGen, ...) compliant.

> Each module logs, drafts, tests, or flags something concrete. None of them certify compliance on their own — that's a legal determination. See [Scope](#scope) below.

## Install

```bash
pip install aiactguard[langchain]
```

## Quickstart

```python
from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler

guard = AIActGuardCallbackHandler(
    category="essential_services",
    approver=lambda ctx: input(f"Approve {ctx['tool']}? [y/N] ").lower() == "y",
)

agent_executor.invoke({"input": "..."}, config={"callbacks": [guard]})
```

See [examples/langchain_quickstart.py](examples/langchain_quickstart.py) for a full runnable example.

## Module roadmap

### Core (Phase 1 — in progress)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 1 | Risk classification engine | Art. 6, Annex III | Tags each agent action/tool call against EU AI Act risk tiers using a configurable taxonomy across all eight Annex III high-risk categories |
| 2 | Immutable audit trail | Art. 12 | Every decision, tool call, input/output, model version, and timestamp logged to an append-only store |
| 3 | Human-in-the-loop approval gates | Art. 14 | Configurable interrupt points that pause execution before a high-risk action fires |
| 4 | Explainability capture | Art. 13 | Structures the agent's chain-of-thought/tool-selection rationale into an auditor-readable format |
| 5 | Framework adapters | — | LangChain, LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Claude Agent SDK |
| 6 | Policy-as-code | — | YAML rules defining what counts as high-risk for a given org and what triggers a human gate |

### Documentation & assessment tooling (Phase 2)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 7 | Technical documentation generator | Art. 11, Annex IV | Auto-drafts the Annex IV technical file from audit logs + a guided questionnaire |
| 8 | Conformity readiness checklist | Art. 43 | Gap-analysis against Annex IV/VI requirements — a pre-assessment aid, not the assessment itself |
| 9 | FRIA template generator | Art. 27 | Pre-fills a Fundamental Rights Impact Assessment draft from risk classification and deployment context |
| 10 | Post-market monitoring plan generator | Art. 72 | Monitoring plan template scaffolded from risk tier and logged incident categories |
| 11 | EU database registration data prep | Art. 71 | Auto-compiles the metadata the Art. 71 registration form requires — filing stays manual |

### Robustness & incident tooling (Phase 3)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 12 | Adversarial/red-team test harness | Art. 15 | Runs prompt-injection, jailbreak, and edge-case scenarios against your agent |
| 13 | Bias & fairness scan | Art. 10 | Statistical checks on agent decisions across protected-characteristic proxies at runtime |
| 14 | Serious incident report drafter | Art. 73 | Turns a flagged incident into a structured draft for human review before filing |
| 15 | GPAI transparency card generator | Art. 53 | Auto-generates a model transparency summary from config + usage patterns |

### Multi-agent & multi-standard extensions (Phase 4 — differentiators)

| # | Module | What it does |
|---|---|---|
| 16 | Composite-system risk aggregation | Flags when multiple individually low-risk agents, composed into a pipeline, cross into high-risk territory as a system |
| 17 | NIST AI RMF mapping layer | Maps audit/risk data to NIST AI RMF's Govern/Map/Measure/Manage functions |
| 18 | ISO/IEC 42001 mapping layer | Maps the same data to ISO 42001 AI management system clauses |
| 19 | Plugin architecture for community modules | Defined interface for jurisdiction- or industry-specific community modules |

## Scope

**Explicitly out of scope, and why:**

- **Prohibited-practice determination (Title II)** — legal judgment call, not a runtime check
- **Conformity assessment / CE marking itself** — requires formal procedures, sometimes a notified body; the toolkit preps evidence, it doesn't perform the assessment
- **Quality management system (Art. 17)** — an organizational process, not code
- **GPAI systemic-risk evaluation (Art. 55)** — applies to frontier model providers, not agent builders
- **Actual legal filing/registration submission** — data prep is automated, submission is not

## Contributing

Contributions are welcome, especially jurisdiction- or industry-specific modules (Phase 4's plugin architecture is built for this). Open an issue to discuss before submitting a large PR.

## License

MIT — see [LICENSE](LICENSE).
