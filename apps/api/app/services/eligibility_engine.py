from typing import List, Dict, Any
from app.services.llm_service import llm_service


class EligibilityEngine:
    def evaluate(self, profile_facts: List[Dict[str, Any]], scheme_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deterministic eligibility evaluation.
        Never guarantees - returns potentially_eligible/needs_more_info/likely_not_eligible
        """
        condition_results = []
        all_required_match = True
        missing_info = False
        explicit_no = False

        # Build fact map
        fact_map = {}
        for f in profile_facts:
            if f.get("verified") or f.get("source") in ["user_confirmed", "manually_entered"]:
                fact_map[f["field_name"]] = f["value"]

        for cond in scheme_conditions:
            ctype = cond.get("condition_type", "").lower()
            operator = cond.get("operator", "==")
            value = str(cond.get("value", "")).lower()
            is_required = cond.get("is_required", True)

            # Try to find matching fact
            fact_value = None
            for k, v in fact_map.items():
                if ctype in k.lower() or k.lower() in ctype:
                    fact_value = str(v).lower()
                    break

            if fact_value is None:
                if is_required:
                    missing_info = True
                    condition_results.append({
                        "condition": cond.get("description") or f"{ctype} {operator} {value}",
                        "status": "needs_more_info",
                        "reason": "Required fact not available/confirmed",
                        "evidence_url": cond.get("evidence_url"),
                    })
                else:
                    condition_results.append({
                        "condition": cond.get("description") or f"{ctype} {operator} {value}",
                        "status": "unknown",
                        "reason": "Optional condition - fact not provided",
                        "evidence_url": cond.get("evidence_url"),
                    })
                continue

            # Simple comparisons
            matched = False
            try:
                if operator == "==" or operator == "equals":
                    matched = fact_value == value or value in fact_value
                elif operator == "<=":
                    # Try numeric
                    try:
                        matched = float(fact_value) <= float(value)
                    except:
                        matched = value in fact_value
                elif operator == ">=":
                    try:
                        matched = float(fact_value) >= float(value)
                    except:
                        matched = value in fact_value
                elif operator == "in":
                    matched = fact_value in value or any(v.strip() in fact_value for v in value.split(","))
                else:
                    matched = value in fact_value or fact_value in value
            except:
                matched = value in fact_value

            if not matched and is_required:
                explicit_no = True
                all_required_match = False
            elif not matched:
                pass  # optional, don't fail

            condition_results.append({
                "condition": cond.get("description") or f"{ctype} {operator} {value}",
                "status": "matched" if matched else "not_matched",
                "your_value": fact_value,
                "required": value,
                "evidence_url": cond.get("evidence_url"),
                "evidence_excerpt": cond.get("evidence_excerpt"),
            })

        if explicit_no and all_required_match is False:
            outcome = "likely_not_eligible"
            match_score = 0.3
        elif missing_info:
            outcome = "needs_more_info"
            match_score = 0.5
        elif all_required_match and not missing_info:
            outcome = "potentially_eligible"
            match_score = 0.8
        else:
            outcome = "needs_more_info"
            match_score = 0.4

        return {
            "outcome": outcome,
            "match_score": match_score,
            "condition_results": condition_results,
            "disclaimer": "SchemeSathi is an information tool, not a government authority. This is not a guarantee of eligibility, approval, or benefit payment. Final decision rests with the relevant department.",
        }


eligibility_engine = EligibilityEngine()
