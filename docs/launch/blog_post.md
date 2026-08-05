# Why agentic AI needs compliance-by-design under the EU AI Act — draft

*Publish as a standalone post (personal blog / Medium / dev.to / LinkedIn article). Fill in bracketed sections before publishing.*

---

## The gap

On August 2, 2026, the EU AI Act's obligations for high-risk AI systems became fully enforceable. If you're running agentic AI — an LLM with tool access making or influencing decisions — in HR, healthcare, finance, critical infrastructure, or [your domain], you now have a live legal obligation.

Here's the problem: the agentic AI ecosystem has almost no tooling for this. LangChain, CrewAI, AutoGen, Dify — all excellent at orchestration, none of them built with Article 12 (audit trails), Article 13 (explainability), or Article 14 (human oversight) in mind, because that's not what they're for. The compliance layer that should sit *alongside* the orchestration layer basically doesn't exist as open source.

## What "compliance-by-design" actually means for an agent

It's tempting to treat this as a paperwork problem you solve after the fact — ship the agent, write the documentation later. That doesn't work for three concrete reasons:

1. **You can't reconstruct an audit trail retroactively.** If Article 12 requires logging every decision, tool call, and model version, that has to be instrumented at the point the agent actually runs — not approximated from logs that weren't designed for this.
2. **Human oversight (Article 14) has to be a real interrupt point, not a policy document.** A gate that "should" pause before a high-risk action needs to actually block execution, with an approval or escalation path, not just be a line in a runbook.
3. **Explainability (Article 13) has to capture what the agent actually reasoned**, not a summary written after the fact by someone guessing at its logic.

All three of these are runtime concerns. They have to be built into the agent's execution path, not bolted on afterward — which is the whole argument for compliance-by-design.

## What I built

AIActGuard is middleware for exactly this — a decorator/callback that wraps an existing agent (LangChain, CrewAI, Claude Agent SDK) rather than replacing its framework:

```python
from aiactguard.adapters.langchain_adapter import AIActGuardCallbackHandler
from aiactguard.core.approval import ApprovalContext, ApprovalDecision

def compliance_officer(ctx: ApprovalContext) -> ApprovalDecision:
    approved = input(f"Approve {ctx.action} ({ctx.risk_tier.value})? [y/N] ").lower() == "y"
    return ApprovalDecision(approved=approved, approver_id="compliance_officer")

guard = AIActGuardCallbackHandler(category="essential_services", approvers=[compliance_officer])
agent_executor.invoke({"input": "..."}, config={"callbacks": [guard]})
```

Under the hood: a configurable risk taxonomy classifies each action against the EU AI Act's Annex III categories, an append-only audit trail logs every decision, and a policy-as-code layer defines what triggers a human-approval gate — with an escalation chain (try approver A, fall back to approver B) and mandatory reasoned logging when someone overrides a denial.

One finding worth sharing: when I validated the LangChain adapter against LangChain's *real* callback dispatch (not just unit-test stubs), I found that LangChain's callback manager silently swallows exceptions raised inside a callback by default — meaning a naively-written "raise to block execution" gate would log a warning and let the tool call through anyway. [Framework]'s callback handlers need to opt into `raise_error = True` for that to actually work. It's the kind of gap that only shows up when you test against the real framework, which is exactly why I don't trust a compliance tool that's only been unit-tested against its own assumptions about the framework it wraps.

## What it doesn't do

Deliberately: it doesn't determine whether a practice is prohibited under Title II (legal judgment, not a runtime check), it doesn't perform conformity assessment or CE marking (that needs formal procedures, sometimes a notified body), and none of its report generators — technical documentation, FRIA, incident reports — claim to be the final filing. Everything it produces is a draft with a human review step before it's used for anything.

That's a deliberate design choice: a tool that overclaims what it certifies is worse than no tool, because it creates false confidence exactly where the stakes are highest.

## Try it

```bash
pip install aiactguard[langchain]
```

MIT-licensed, [github.com/NavikkumarModi/AIActGuard](https://github.com/NavikkumarModi/AIActGuard). Framework-specific quickstarts for LangChain, CrewAI, and the Claude Agent SDK are in the repo's `examples/` directory. If you're building agentic AI in a regulated industry, I'd genuinely like to hear what's missing.

---
**Fill in before publishing:** your domain/background in the intro, the `[Framework]` reference (this is LangChain-specific — reword if generalizing), and consider swapping the code sample for whichever framework your audience uses most.
