# LinkedIn post — draft

Post from your own account, not a company/project page — the credibility here is "[your title] who builds this stuff for a living," and that only works coming from you directly.

---

The EU AI Act's obligations for high-risk AI systems became enforceable on August 2, 2026.

Most agentic AI in production right now — in HR, finance, healthcare, [pharma/supply-chain — adjust to your actual domain] — has no tooling for Article 12 (audit trails), Article 13 (explainability), or Article 14 (human oversight). The orchestration layer (LangChain, CrewAI, AutoGen) is extremely well built out. The compliance layer sitting next to it basically doesn't exist as open source.

So I built AIActGuard: MIT-licensed middleware you drop onto an existing agent — not a new framework to migrate to — that adds:

→ Risk classification against Annex III categories
→ An immutable audit trail
→ Human-approval gates with an escalation chain (and it logs *why* someone overrode a denial)
→ Explainability capture from the agent's actual reasoning
→ Drafting tools for the paperwork: technical documentation, a conformity checklist, an FRIA, incident reports, NIST/ISO mappings

It's explicit about what it doesn't do — none of this replaces a legal conformity assessment. It's the "here's your evidence, here's your gaps" layer.

[Optional: 1-2 sentences on why this matters to you personally / your background — e.g. building this after seeing the compliance gap firsthand in a regulated industry]

Repo's open, feedback and contributions welcome — especially from anyone who's had to actually build this for a real deployment:
https://github.com/NavikkumarModi/AIActGuard

#AIAct #ComplianceByDesign #AgenticAI #OpenSource

---
**Fill in before posting:** the bracketed personal-context line, and swap "pharma/supply-chain" for whatever's actually true for you.
