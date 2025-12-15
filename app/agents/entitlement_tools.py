from __future__ import annotations

from typing import Dict, List, Literal, Optional, Tuple

from .entitlements import PLAN_ENTITLEMENTS

Plan = Literal["BRONZE", "SILVER", "GOLD"]


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _index_entitlements() -> Tuple[Dict[str, Plan], List[str]]:
    """Create a reverse index: report -> lowest plan that includes it, and paid-only list.

    - For included/optional under plans, we consider "included" as coverage.
    - Items under optional are available but not automatically included; we still map
      them to their plan for upsell guidance.
    - Items only under PAID belong to the paid-only list.
    """
    reverse: Dict[str, Plan] = {}
    # Order matters from lowest to highest to compute lowest plan providing it
    order: List[Plan] = ["BRONZE", "SILVER", "GOLD"]
    for plan in order:
        plan_data = PLAN_ENTITLEMENTS.get(plan, {})
        for bucket in ("included", "optional"):
            for item in plan_data.get(bucket, []):
                key = _normalize(item)
                reverse.setdefault(key, plan)
    paid = PLAN_ENTITLEMENTS.get("PAID", {}).get("reports", []) or []
    return reverse, [_normalize(r) for r in paid]


_REVERSE_INDEX, _PAID = _index_entitlements()


def check_entitlement(*, report: str, plan: Plan) -> Dict[str, object]:
    """Tool: Check access for a report under a plan.

    Returns a dict with fields:
      - status: one of {included, optional, paid, not_found}
      - current_plan: provided plan
      - lowest_plan: if not included in current plan, the lowest plan that covers it (may equal current_plan)
      - paid_only: bool
      - canonical_report: normalized key used for comparison
    """
    key = _normalize(report)
    paid_only = key in _PAID
    lowest_plan: Optional[Plan] = _REVERSE_INDEX.get(key)

    if paid_only:
        return {
            "status": "paid",
            "current_plan": plan,
            "lowest_plan": None,
            "paid_only": True,
            "canonical_report": key,
        }

    if not lowest_plan:
        return {
            "status": "not_found",
            "current_plan": plan,
            "lowest_plan": None,
            "paid_only": False,
            "canonical_report": key,
        }

    order: List[Plan] = ["BRONZE", "SILVER", "GOLD"]
    if order.index(plan) >= order.index(lowest_plan):
        return {
            "status": "included",
            "current_plan": plan,
            "lowest_plan": lowest_plan,
            "paid_only": False,
            "canonical_report": key,
        }
    else:
        return {
            "status": "optional",
            "current_plan": plan,
            "lowest_plan": lowest_plan,
            "paid_only": False,
            "canonical_report": key,
        }
