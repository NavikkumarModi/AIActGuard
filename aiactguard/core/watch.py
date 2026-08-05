from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from ..policy.schema import ApprovalRequired, PolicyConfig
from .audit_logger import AuditLogger
from .risk_classifier import RiskClassifier


def watch(
    *,
    category: str,
    classifier: Optional[RiskClassifier] = None,
    logger: Optional[AuditLogger] = None,
    policy: Optional[PolicyConfig] = None,
    approver: Optional[Callable[[dict], bool]] = None,
) -> Callable:
    """Decorator that classifies, gates, and audit-logs a single agent
    action or tool call — the no-framework-required integration path for
    functions that aren't wrapped via a framework-specific adapter.

    If the classified risk tier requires approval per the active policy and
    no `approver` is configured, raises ApprovalRequired instead of running
    the wrapped function.
    """
    classifier = classifier or RiskClassifier.default()
    logger = logger or AuditLogger.default()
    policy = policy or PolicyConfig.default()

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            risk_tier = classifier.classify(category)
            requires_approval = policy.requires_approval(category=category, risk_tier=risk_tier)

            approved = True
            if requires_approval:
                if approver is None:
                    logger.log(
                        action=fn.__name__,
                        category=category,
                        risk_tier=risk_tier,
                        inputs={"args": [repr(a) for a in args], "kwargs": {k: repr(v) for k, v in kwargs.items()}},
                        approved=False,
                        gated=True,
                        error="No approver configured for a gated action.",
                    )
                    raise ApprovalRequired(
                        f"Action '{fn.__name__}' (category={category}, risk_tier={risk_tier.value}) "
                        "requires human approval but no approver was configured."
                    )
                approved = approver(
                    {"action": fn.__name__, "category": category, "risk_tier": risk_tier.value,
                     "args": args, "kwargs": kwargs}
                )

            result = None
            error: Optional[BaseException] = None
            if approved:
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - re-raised below after logging
                    error = exc

            logger.log(
                action=fn.__name__,
                category=category,
                risk_tier=risk_tier,
                inputs={"args": [repr(a) for a in args], "kwargs": {k: repr(v) for k, v in kwargs.items()}},
                outputs=repr(result) if approved and error is None else None,
                approved=approved,
                gated=requires_approval,
                error=str(error) if error else None,
            )

            if error:
                raise error
            if not approved:
                raise ApprovalRequired(f"Action '{fn.__name__}' was not approved.")
            return result

        return wrapper

    return decorator
