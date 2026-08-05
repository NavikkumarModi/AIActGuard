# Show HN post — draft

Timing note: post this on/around August 2nd (the EU AI Act's high-risk-system obligations enforcement date) or as close after as the actual PyPI release allows — the doc's whole angle is "the compliance gap every agent team now has," which is time-sensitive to that date. Don't post before there's a real `pip install aiactguard` to point people at.

## Title

```
Show HN: AIActGuard – EU AI Act compliance middleware for LangChain/CrewAI/Claude agents
```

(HN strips "Show HN:" length into the 80-char limit — trim the rest if needed, e.g. drop "for LangChain/CrewAI/Claude agents" and let the comment explain.)

## Post body (submit as the first comment, HN convention for Show HN)

I built AIActGuard because [YOUR REASON — e.g. "as a Principal AI Architect in pharma, I watched teams ship agentic AI in HR/finance/supply-chain contexts with zero tooling for the EU AI Act's Article 12/13/14 obligations that became enforceable this month"]. There's a lot of open-source agent orchestration (LangChain, CrewAI, AutoGen) but nothing sitting alongside it as a compliance layer.

It's a decorator/callback you drop onto an existing agent — not a new orchestrator:

- Risk classification against the EU AI Act's Annex III categories
- An immutable audit trail (every tool call, decision, model version, timestamp)
- Human-approval gates with an escalation chain and reasoned-override logging
- Explainability capture (the agent's actual chain-of-thought, not a fabricated summary)
- Drafts (not certifies) the paperwork: technical documentation, a conformity gap-analysis checklist, an FRIA, a post-market monitoring plan, EU registration data prep, incident reports, NIST/ISO mappings

Every module is explicit about what it can't do — it doesn't claim to determine legal conformity, that's a human/legal call. README has the full scope boundary.

MIT-licensed, dependency-light (the CrewAI/Claude Agent SDK adapters are duck-typed, no hard dependency on those packages). Would love feedback, especially from anyone who's actually had to build EU AI Act compliance tooling for a real deployment — I'm sure there are gaps I haven't hit yet.

GitHub: https://github.com/NavikkumarModi/AIActGuard
PyPI: `pip install aiactguard`

---
**Fill in before posting:** the bracketed reason above, and double-check the PyPI install line is live before this goes out.
