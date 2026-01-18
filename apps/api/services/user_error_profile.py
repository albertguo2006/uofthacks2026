"""
User Error Profile Service

Computes user's historical error profile by analyzing events.
Used for adaptive hint generation based on error patterns.
"""

from typing import Literal
from datetime import datetime, timedelta
from db.collections import Collections


ErrorCategory = Literal["syntax", "logic", "type", "runtime"]
HintStyle = Literal["example-based", "conceptual", "step-by-step", "socratic"]
Trend = Literal["improving", "stable", "struggling"]


async def compute_error_profile(user_id: str) -> dict:
    """
    Compute user's historical error profile by analyzing events.

    Returns:
    {
        "dominant_category": "syntax" | "logic" | "type" | "runtime",
        "category_distribution": {"syntax": 0.45, "logic": 0.30, ...},
        "total_errors": 127,
        "recent_trend": "improving" | "stable" | "struggling",
        "effective_hint_styles": ["example-based", "conceptual"]
    }
    """
    # Fetch error events from the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    error_events = await Collections.events().find({
        "user_id": user_id,
        "event_type": "error_emitted",
        "timestamp": {"$gte": thirty_days_ago}
    }).to_list(1000)

    # Fetch interventions to analyze effectiveness (use triggered_at field)
    interventions = await Collections.interventions().find({
        "user_id": user_id,
        "triggered_at": {"$gte": thirty_days_ago}
    }).to_list(500)

    if not error_events:
        return {
            "dominant_category": "logic",
            "category_distribution": {
                "syntax": 0.25,
                "logic": 0.25,
                "type": 0.25,
                "runtime": 0.25
            },
            "total_errors": 0,
            "recent_trend": "stable",
            "effective_hint_styles": ["conceptual", "example-based"],
            "has_data": False
        }

    # Categorize errors
    category_counts = {
        "syntax": 0,
        "logic": 0,
        "type": 0,
        "runtime": 0
    }

    for event in error_events:
        props = event.get("properties", {})
        error_msg = props.get("error_message", "").lower()
        error_type = props.get("error_type", "")

        category = categorize_error(error_msg, error_type)
        category_counts[category] += 1

    total_errors = sum(category_counts.values())

    # Calculate distribution
    category_distribution = {
        cat: round(count / total_errors, 2) if total_errors > 0 else 0.25
        for cat, count in category_counts.items()
    }

    # Find dominant category
    dominant_category = max(category_counts, key=category_counts.get)

    # Calculate recent trend (compare last 7 days vs previous 7 days)
    recent_trend = calculate_trend(error_events)

    # Determine effective hint styles based on intervention history
    effective_hint_styles = determine_effective_styles(interventions, dominant_category)

    return {
        "dominant_category": dominant_category,
        "category_distribution": category_distribution,
        "total_errors": total_errors,
        "recent_trend": recent_trend,
        "effective_hint_styles": effective_hint_styles,
        "has_data": True
    }


def categorize_error(error_msg: str, error_type: str = "") -> ErrorCategory:
    """Categorize an error based on message and type."""
    error_type_lower = error_type.lower()

    # Check error_type first
    if error_type_lower in ["syntax", "syntaxerror"]:
        return "syntax"
    if error_type_lower in ["typeerror", "type"]:
        return "type"
    if error_type_lower in ["runtime", "runtimeerror"]:
        return "runtime"

    # Syntax error patterns
    syntax_patterns = [
        "syntaxerror", "syntax error", "unexpected token", "missing",
        "expected", "invalid syntax", "unterminated", "parse error",
        "unexpected end", "unexpected identifier", "illegal",
        "missing )", "missing }", "missing ;", "indentation"
    ]
    if any(pattern in error_msg for pattern in syntax_patterns):
        return "syntax"

    # Type error patterns
    type_patterns = [
        "typeerror", "type error", "not a function", "undefined is not",
        "cannot read property", "null is not", "not iterable",
        "expected number", "expected string", "not callable",
        "'nonetype'", "attributeerror", "cannot convert"
    ]
    if any(pattern in error_msg for pattern in type_patterns):
        return "type"

    # Runtime error patterns
    runtime_patterns = [
        "runtime", "stack overflow", "recursion", "memory",
        "timeout", "killed", "segmentation", "out of memory",
        "maximum call stack", "infinite loop"
    ]
    if any(pattern in error_msg for pattern in runtime_patterns):
        return "runtime"

    # Default to logic (wrong output, failed assertions, etc.)
    return "logic"


def calculate_trend(error_events: list) -> Trend:
    """Calculate if user is improving, stable, or struggling."""
    if len(error_events) < 5:
        return "stable"

    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    recent_errors = [
        e for e in error_events
        if e.get("timestamp") and e["timestamp"] >= seven_days_ago
    ]

    previous_errors = [
        e for e in error_events
        if e.get("timestamp") and fourteen_days_ago <= e["timestamp"] < seven_days_ago
    ]

    recent_count = len(recent_errors)
    previous_count = len(previous_errors)

    if previous_count == 0:
        return "stable"

    # Calculate change ratio
    change_ratio = (recent_count - previous_count) / previous_count

    if change_ratio <= -0.3:
        return "improving"
    elif change_ratio >= 0.3:
        return "struggling"
    return "stable"


def determine_effective_styles(interventions: list, dominant_category: ErrorCategory) -> list[HintStyle]:
    """
    Determine which hint styles are most effective for the user.
    Based on intervention history and resolved issues.
    """
    # Analyze which interventions led to resolved issues
    style_effectiveness: dict[str, dict] = {}

    for intervention in interventions:
        hint_category = intervention.get("hint_category", "approach")
        resolved = intervention.get("resolved_issue", False)

        if hint_category not in style_effectiveness:
            style_effectiveness[hint_category] = {"resolved": 0, "total": 0}

        style_effectiveness[hint_category]["total"] += 1
        if resolved:
            style_effectiveness[hint_category]["resolved"] += 1

    # Calculate effectiveness rates
    effective_styles = []
    for style, stats in style_effectiveness.items():
        if stats["total"] >= 3:  # Need minimum data
            rate = stats["resolved"] / stats["total"]
            if rate >= 0.4:  # 40% resolution rate considered effective
                effective_styles.append(map_category_to_style(style))

    # If no data, use defaults based on dominant error category
    if not effective_styles:
        effective_styles = get_default_styles(dominant_category)

    return effective_styles[:2]  # Return top 2 styles


def map_category_to_style(hint_category: str) -> HintStyle:
    """Map hint category to hint style."""
    mapping = {
        "syntax": "example-based",
        "logic": "socratic",
        "approach": "conceptual",
        "encouragement": "step-by-step"
    }
    return mapping.get(hint_category, "conceptual")


def get_default_styles(dominant_category: ErrorCategory) -> list[HintStyle]:
    """Get default hint styles based on dominant error category."""
    defaults = {
        "syntax": ["example-based", "step-by-step"],
        "logic": ["socratic", "conceptual"],
        "type": ["example-based", "conceptual"],
        "runtime": ["step-by-step", "conceptual"]
    }
    return defaults.get(dominant_category, ["conceptual", "example-based"])


async def get_error_profile_summary(user_id: str) -> str:
    """Generate a human-readable summary of user's error profile."""
    profile = await compute_error_profile(user_id)

    if not profile.get("has_data"):
        return "No error history available yet."

    dominant = profile["dominant_category"]
    total = profile["total_errors"]
    trend = profile["recent_trend"]

    trend_text = {
        "improving": "making good progress",
        "stable": "maintaining steady practice",
        "struggling": "facing some challenges"
    }.get(trend, "practicing")

    category_text = {
        "syntax": "syntax-related issues (brackets, semicolons, indentation)",
        "logic": "logical errors (off-by-one, wrong conditions)",
        "type": "type-related mistakes (undefined, null, type mismatches)",
        "runtime": "runtime issues (recursion, memory)"
    }.get(dominant, "various coding challenges")

    return f"Based on {total} errors analyzed, you tend to encounter {category_text}. You're currently {trend_text}."
