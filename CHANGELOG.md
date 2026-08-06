# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.2] — 2026-08-06

### Changed
- Removed `agentguard-project-plan.md` and `docs/launch/` (internal planning/launch drafts, not meant for the public repo) — kept privately outside the repo.
- Extracted the repeated Markdown-building code duplicated across every report/mapping/testing module into a shared `aiactguard.core.markdown.MarkdownReport` builder. Output is unchanged; this is a pure internal refactor.

## [0.1.1] — 2026-08-05

### Fixed
- README links to `LICENSE`, `pyproject.toml`, and everything under `examples/` were repo-relative, which resolves fine on GitHub but breaks on PyPI's standalone-rendered project page. Rewritten to absolute GitHub URLs.

## [0.1.0] — 2026-08-05

Initial build: all 19 modules from the original project plan.

### Phase 1 — Core
- Risk classification engine against a configurable EU AI Act Annex III taxonomy
- Immutable, append-only audit trail (SQLite-backed by default)
- Human-in-the-loop approval gates with a multi-approver escalation chain and reasoned-override logging
- Explainability capture (chain-of-thought/rationale attached to audit records)
- Policy-as-code (YAML gate rules)
- Framework adapters: LangChain, CrewAI, Claude Agent SDK
- `@watch` decorator for framework-agnostic integration

### Phase 2 — Documentation & assessment tooling
- Technical documentation generator (Art. 11 / Annex IV)
- Conformity readiness checklist (Art. 43)
- FRIA template generator (Art. 27)
- Post-market monitoring plan generator (Art. 72)
- EU database registration data prep (Art. 71)

### Phase 3 — Robustness & incident tooling
- Adversarial/red-team test harness (Art. 15)
- Bias & fairness scan (Art. 10)
- Serious incident report drafter (Art. 73)
- GPAI transparency card generator (Art. 53)

### Phase 4 — Multi-agent & multi-standard extensions
- Composite-system risk aggregation across multi-step pipelines
- NIST AI RMF mapping layer
- ISO/IEC 42001 mapping layer
- Plugin architecture (`aiactguard.plugins`) with entry-point discovery for community modules
