# AIActGuard — Compliance & Governance Middleware for Agentic AI

**Working tagline:** *"Drop-in EU AI Act compliance for any agent framework — audit trails, risk classification, and human-approval gates in one decorator."*

---

## 1. Why this, why now

- The EU AI Act's obligations for high-risk AI systems became fully enforceable on **August 2, 2026** — three days before this doc was written. Every enterprise running agentic AI in HR, healthcare, finance, critical infrastructure, or (like GSK) pharma supply chain now has a live legal obligation and almost no open-source tooling to meet it.
- The agentic AI GitHub landscape is saturated at the orchestration layer (LangChain, CrewAI, AutoGen, Dify, Langflow all have 50k–150k+ stars). Nobody has claimed the **governance/compliance layer** that sits *alongside* those frameworks.
- "Picks and shovels" repos that solve a boring, urgent, universally-needed problem (not a flashy demo) have a track record of steady, durable star growth rather than one viral spike that fades.
- This is also the most credible repo for your career narrative: Principal AI Architect at a regulated pharma enterprise, shipping the compliance tooling the whole industry now needs. It's a stronger signal to a VP/Head of AI hiring panel than a generic agent framework would be.

## 2. What it is (and isn't)

**Is:** A lightweight middleware/wrapper layer that any existing agent stack can adopt without ripping out its framework.

**Isn't:** Another agent orchestrator. You are not competing with LangChain/CrewAI — you're making them compliant.

## 3. Full module coverage (expanded scope)

Each module is scoped honestly: it logs, drafts, tests, or flags something concrete — none of them claim to *certify* compliance on their own, since that's a legal determination. That honesty is what makes a broad feature set credible instead of overreaching.

### Core (Phase 1)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 1 | **Risk classification engine** | Art. 6, Annex III | Tags each agent action/tool call against EU AI Act risk tiers (minimal / limited / high / unacceptable) using a configurable taxonomy across all eight Annex III high-risk categories (biometrics, critical infrastructure, education, employment, essential services, law enforcement, migration, justice/democracy) |
| 2 | **Immutable audit trail** | Art. 12 | Every decision, tool call, input/output, model version, and timestamp logged to an append-only store |
| 3 | **Human-in-the-loop approval gates** | Art. 14 | Configurable interrupt points that pause execution before a high-risk action fires, routing to a human approver, with escalation and override logging |
| 4 | **Explainability capture** | Art. 13 | Structures the agent's chain-of-thought/tool-selection rationale into an auditor-readable format |
| 5 | **Framework adapters** | — | LangChain, LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Claude Agent SDK |
| 6 | **Policy-as-code** | — | YAML rules defining what counts as high-risk for a given org and what triggers a human gate |

### Documentation & assessment tooling (Phase 2)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 7 | **Technical documentation generator** | Art. 11, Annex IV | Auto-drafts the Annex IV technical file (system description, design choices, data used, performance metrics) from audit logs + a guided questionnaire for the parts code can't infer |
| 8 | **Conformity readiness checklist** | Art. 43 | A gap-analysis tool that checks your logged evidence against each Annex IV/VI requirement and flags what's missing — a pre-assessment aid, not the assessment itself |
| 9 | **Fundamental Rights Impact Assessment (FRIA) template generator** | Art. 27 | Pre-fills an FRIA draft from your system's risk classification and deployment context — required for deployers in banking, insurance, and public-service high-risk use cases |
| 10 | **Post-market monitoring plan generator** | Art. 72 | Produces a monitoring plan template scaffolded from the system's risk tier and logged incident categories |
| 11 | **EU database registration data prep** | Art. 71 | Auto-compiles the information fields the Art. 71 registration form requires from your system's metadata — the actual filing stays manual, but the tedious data-gathering is automated |

### Robustness & incident tooling (Phase 3)

| # | Module | Article(s) | What it does |
|---|---|---|---|
| 12 | **Adversarial/red-team test harness** | Art. 15 | Runs a library of prompt-injection, jailbreak, and edge-case scenarios against your agent and reports pass/fail with logs |
| 13 | **Bias & fairness scan** | Art. 10 | Statistical checks on agent decisions across protected-characteristic proxies in the input data it processes at runtime (not training-data governance, which is out of scope) |
| 14 | **Serious incident report drafter** | Art. 73 | Turns a flagged incident (a gate override, an anomalous action, a user-reported harm) into a structured draft matching the incident-report format, for human review before filing |
| 15 | **GPAI transparency card generator** | Art. 53 | For teams building on top of general-purpose models, auto-generates a model transparency summary (capabilities, limitations, known risks) from config + your usage patterns |

### Multi-agent & multi-standard extensions (Phase 4 — differentiators)

| # | Module | What it does |
|---|---|---|
| 16 | **Composite-system risk aggregation** | A genuinely novel piece: flags when multiple individually low-risk agents, composed into a pipeline, cross into high-risk territory as a system — something no existing tool checks for, and a natural fit for your RL/systems background |
| 17 | **NIST AI RMF mapping layer** | Maps the same audit/risk data to NIST AI RMF's Govern/Map/Measure/Manage functions — widens the addressable market to US enterprises without EU exposure |
| 18 | **ISO/IEC 42001 mapping layer** | Same data, mapped to ISO 42001 AI management system clauses — relevant for any org pursuing certification |
| 19 | **Plugin architecture for community modules** | A defined interface so the community can contribute jurisdiction-specific or industry-specific modules (e.g., a pharma/GxP module, a financial services module) over time — this is also a strong organic-growth mechanism: contributors who add a module have a reason to promote the repo themselves |

### What stays explicitly out of scope (and why)

- **Prohibited-practice determination (Title II)** — legal judgment call, not a runtime check
- **Conformity assessment / CE marking itself** — requires formal procedures, sometimes a notified body; the toolkit preps evidence, it doesn't perform the assessment
- **Quality management system (Art. 17)** — an organizational process, not code
- **GPAI systemic-risk evaluation (Art. 55)** — applies to frontier model providers, not agent builders
- **Actual legal filing/registration submission** — data prep is automated, submission is not

This boundary list should live prominently in the README — it's what makes the broad feature set credible rather than overreaching.

## 4. Architecture (high level)

```
Your existing agent (LangChain / CrewAI / etc.)
            │
      @aiactguard.watch  ← decorator/callback, no framework replacement
            │
   ┌────────┴─────────┐
   │   AIActGuard Core  │
   │  - Risk classifier │
   │  - Policy engine    │
   │  - Audit logger     │
   └────────┬─────────┘
            │
   Audit store (SQLite default, Postgres for prod)
            │
   Report generator ──► compliance-report.md / .pdf
   Dashboard (optional, Streamlit) ──► live view of gated/logged actions
```

## 5. Realistic build roadmap (part-time, alongside a full-time role)

The full 19-module scope above is the destination, not the launch state — launching with real depth in Phase 1 and a visible, documented roadmap for Phases 2–4 is what actually drives sustained stars (people star ambitious, clearly-planned projects and come back for releases; they don't star a repo that ships everything half-finished on day one).

- **Weeks 1–2 — Phase 1 core:** Risk classifier + audit logger + LangChain adapter + policy-as-code
- **Weeks 3–4 — Phase 1 complete:** Human-approval gates + explainability capture + CrewAI and Claude Agent SDK adapters
- **Week 5 — Launch prep:** Docs site, quickstart per framework, README with the full module roadmap visible (this is your public commitment device and your changelog-driven visibility engine)
- **Week 6 — Launch**
- **Weeks 7–10 — Phase 2:** Technical documentation generator, conformity readiness checklist, FRIA generator
- **Weeks 11–14 — Phase 3:** Red-team harness, bias scan, incident report drafter, GPAI transparency card
- **Ongoing — Phase 4:** Composite-risk aggregation (your strongest technical differentiator — worth prioritizing earlier if you want a research-flavored angle sooner), NIST/ISO mapping layers, plugin architecture opened to contributors

Each phase completion is a natural release/announcement moment — this turns one launch into 4–5 visibility events instead of one.

## 6. Visibility / star-growth plan (this is where most repos fail, not the code)

- **Timed launch** explicitly anchored to the EU AI Act enforcement date — "the compliance gap every agent team now has."
- **Show HN**, r/MachineLearning, r/LocalLLaMA, and LinkedIn — post from your own account leveraging your GSK/pharma + PhD credibility, not an anonymous repo drop.
- **Submit to the existing "awesome-agentic-ai" curated lists** as a PR — free distribution into an audience that's already primed.
- **One technical blog post**: "Why agentic AI needs compliance-by-design under the EU AI Act" — this slots directly into the thought-leadership work you already have in motion (the pharma supply-chain resilience piece and the JEPA/bandit piece).
- **Framework-specific quickstarts** as separate short posts/gists ("Add EU AI Act compliance to your LangChain agent in 5 minutes") — lowers adoption friction and gives you multiple distinct pieces of shareable content from one project.
- **A "compliance-checked" badge** projects can add to their own README once integrated — this is a viral distribution loop, similar to how CI/coverage badges spread.
- Target compliance/legal-tech communities in addition to ML ones — this is a rare repo with two distinct audiences, which doubles your reach.

## 7. Name — confirmed: AIActGuard

Literal and high-intent for SEO ("EU AI Act" + "compliance"/"agent"), and it reads clearly as a governance layer rather than another orchestration framework.

## 8. License

**MIT.** Best fit here — max adoption, no copyleft friction for enterprises evaluating it (the exact audience you're targeting), and it's the norm across nearly all the comparable repos referenced earlier (LangChain, CrewAI, Guardrails AI).

## 9. Claude Code kickoff prompt

Since you'll build this in Claude Code, here's a ready-to-paste prompt to start the Phase 1 scaffold. Drop this plan file into the project directory first so Claude Code has the full spec as context.

```
I'm building AIActGuard, an MIT-licensed Python library that adds EU AI Act
technical-obligation tooling (audit logging, risk classification, human
approval gates) as middleware around existing agent frameworks — not a new
orchestrator. Full spec is in agentguard-project-plan.md in this directory.

Scaffold the Phase 1 MVP:
1. Package structure: aiactguard/ with core/, adapters/, policy/, storage/
2. core/risk_classifier.py — classifies actions against a configurable
   Annex III risk taxonomy (YAML-driven, ship a default taxonomy file)
3. core/audit_logger.py — append-only audit log, SQLite backend by default,
   schema covering timestamp, action, inputs/outputs, model version, risk tier
4. adapters/langchain_adapter.py — a callback/decorator that wraps a
   LangChain agent's tool calls and routes them through the risk classifier
   and audit logger with minimal integration code required
5. policy/schema.py + a default policy.yaml — defines what triggers a
   human-approval gate per org config
6. A working example in examples/langchain_quickstart.py showing a full
   wrapped agent in under 20 lines
7. pyproject.toml, MIT LICENSE file, and a README.md skeleton (I'll refine
   the README content separately, but scaffold the standard sections:
   badges, install, quickstart, module roadmap table, contributing, license)
8. Basic test coverage for risk_classifier and audit_logger

Keep it dependency-light — no framework lock-in beyond what's needed for
the LangChain adapter itself. Ask me before adding any new dependency
beyond langchain, pyyaml, and pytest.
```

## 10. Next steps

1. Register the GitHub repo under `AIActGuard`, MIT LICENSE
2. Open Claude Code in the repo directory with this plan file present, paste the kickoff prompt above
3. Come back here for the README launch copy, the LinkedIn/Show HN posts, and the framework-specific quickstart write-ups once Phase 1 is working code — that content lands better once there's a real repo to point at
