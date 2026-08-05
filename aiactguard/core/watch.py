from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from ..policy.schema import ApprovalRequired, PolicyConfig
from .approval import Approver
from .audit_logger import AuditLogger
from .guard import GuardCore
from .risk_classifier import RiskClassifier


def watch(
    *,
    category: str,
    classifier: Optional[RiskClassifier] = None,
    logger: Optional[AuditLogger] = None,
    policy: Optional[PolicyConfig] = None,
    approvers: Optional[list[Approver]] = None,
    rationale_fn: Optional[Callable[[tuple, dict, Any], list[dict]]] = None,
) -> Callable:
    """Decorator that classifies, gates, and audit-logs a single agent
    action or tool call — the no-framework-required integration path for
    functions that aren't wrapped via a framework-specific adapter.

    `approvers` is an escalation chain (see `ApprovalGate`): each is tried
    in order until one returns a decision. If the action requires approval
    and nobody in the chain responds (or approves), `ApprovalRequired` is
    raised instead of running the wrapped function.

    `rationale_fn`, if given, is called with `(args, kwargs, result)` after
    a successful run and should return a list of `{"source": ..., "text": ...}`
    steps to attach to the audit record for explainability capture (Art. 13).
    """
    guard = GuardCore(
        category=category,
        classifier=classifier,
        logger=logger,
        policy=policy,
        approvers=approvers,
    )

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            inputs = {"args": [repr(a) for a in args], "kwargs": {k: repr(v) for k, v in kwargs.items()}}
            evaluation = guard.evaluate(action=fn.__name__, inputs=inputs)

            if evaluation.gated and not evaluation.approved:
                guard.log(evaluation, action=fn.__name__, inputs=inputs)
                raise ApprovalRequired(
                    f"Action '{fn.__name__}' (category={category}, risk_tier={evaluation.risk_tier.value}) "
                    f"was denied: {evaluation.denial_reason}"
                )

            result = None
            error: Optional[BaseException] = None
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - re-raised below after a single log call
                error = exc

            rationale = rationale_fn(args, kwargs, result) if (rationale_fn and error is None) else None

            decision = evaluation.decision
            guard.logger.log(
                action=fn.__name__,
                category=category,
                risk_tier=evaluation.risk_tier,
                inputs=inputs,
                outputs=repr(result) if error is None else None,
                model_version=guard.model_version,
                approved=error is None,
                gated=evaluation.gated,
                error=str(error) if error else None,
                approver_id=decision.approver_id if decision else None,
                override=decision.override if decision else False,
                reason=decision.reason if decision else None,
                rationale=rationale,
            )

            if error is not None:
                raise error
            return result

        return wrapper

    return decorator
