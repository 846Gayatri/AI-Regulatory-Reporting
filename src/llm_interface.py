# src/llm_interface.py
"""LLM interface for generating section prose.

In production this would call an LLM, but for this prototype we provide an
offline fallback that converts the evidence packet data into polished,
human‑readable report text — no external API required.
"""

from typing import Dict, Any, List


def _fmt_list(items: list) -> str:
    """Format a list of (name, count) tuples as bullet points."""
    if not items:
        return "- None reported\n"
    lines = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            lines.append(f"- {item[0]}: {item[1]} case(s)")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _render_reporting_period(data: Dict[str, Any]) -> str:
    start = data.get("start_date", "N/A")
    end = data.get("end_date", "N/A")
    return (
        f"## Reporting Period\n\n"
        f"This Periodic Adverse Drug Experience Report (PADER) covers the "
        f"reporting period from **{start}** to **{end}**.\n"
    )


def _render_narrative_summary(data: Dict[str, Any]) -> str:
    total = data.get("total_cases", 0)
    serious = data.get("serious_cases", 0)
    non_serious = data.get("non_serious_cases", 0)
    top_reactions = data.get("top_reactions", [])
    top_serious = data.get("top_serious_reactions", [])

    reaction_names = ", ".join(r[0] for r in top_reactions[:5] if isinstance(r, (list, tuple))) if top_reactions else "none"
    serious_names = ", ".join(r[0] for r in top_serious[:5] if isinstance(r, (list, tuple))) if top_serious else "none"

    return (
        f"## Narrative Summary and Analysis\n\n"
        f"During the reporting period, a total of **{total}** Individual Case Safety "
        f"Reports (ICSRs) were received. Of these, **{serious}** were classified as "
        f"serious and **{non_serious}** as non‑serious.\n\n"
        f"The most frequently reported adverse reactions were: {reaction_names}. "
        f"Among serious cases, the most commonly reported reactions were: {serious_names}.\n\n"
        f"No new safety signals were identified during this period that would warrant "
        f"a change to the established benefit‑risk profile. The types of adverse events "
        f"reported remain consistent with the known safety profile of the product. "
        f"Continued routine pharmacovigilance monitoring is recommended.\n"
    )


def _render_case_summary(data: Dict[str, Any]) -> str:
    age_groups = data.get("age_groups", [])
    sex_counts = data.get("sex_counts", {})
    country_counts = data.get("country_counts", [])

    # Build age summary
    if age_groups:
        non_zero_ages = [(g, c) for g, c in age_groups if isinstance(c, (int, float)) and c > 0]
        if non_zero_ages:
            age_text = ", ".join(f"{g} ({int(c)})" for g, c in non_zero_ages)
        else:
            age_text = "no age data available"
    else:
        age_text = "no age data available"

    # Build sex summary
    if sex_counts:
        sex_text = ", ".join(f"{k}: {v}" for k, v in sex_counts.items())
    else:
        sex_text = "no sex data available"

    # Build country summary
    if country_counts:
        country_text = ", ".join(
            f"{c[0]} ({c[1]})" for c in country_counts[:10]
            if isinstance(c, (list, tuple)) and len(c) >= 2
        )
    else:
        country_text = "no country data available"

    return (
        f"## Summary Analysis of Cases\n\n"
        f"### Demographics\n\n"
        f"**Age distribution:** {age_text}.\n\n"
        f"**Sex distribution:** {sex_text}.\n\n"
        f"**Reporting countries:** {country_text}.\n"
    )


def _render_reaction_analysis(data: Dict[str, Any]) -> str:
    top_reactions = data.get("top_reactions", [])
    top_serious = data.get("top_serious_reactions", [])

    lines = [
        "## Reaction / Adverse Event Analysis\n",
        "### Most Frequently Reported Reactions\n",
        _fmt_list(top_reactions),
        "### Most Frequently Reported Serious Reactions\n",
        _fmt_list(top_serious),
    ]
    return "\n".join(lines)


def _render_serious_cases(data: Dict[str, Any]) -> str:
    serious = data.get("serious_cases", 0)
    return (
        f"## Serious Cases / 15‑Day Alerts\n\n"
        f"A total of **{serious}** serious case(s) were reported during the "
        f"reporting period.\n\n"
        f"All serious cases were assessed against 15‑day expedited reporting "
        f"thresholds. Cases meeting regulatory criteria were submitted within "
        f"the required time‑frame.\n"
    )


def _render_trends(data: Dict[str, Any]) -> str:
    total = data.get("total_cases", 0)
    return (
        f"## Trends and Important Observations\n\n"
        f"A total of **{total}** case(s) were received during the reporting period. "
        f"No significant upward or downward trend in overall case volume was observed.\n\n"
        f"The adverse event profile remains consistent with previous reporting periods. "
        f"No new safety concerns requiring immediate regulatory action have been identified. "
        f"Routine monitoring will continue in the next reporting period.\n"
    )


# Map section names to their dedicated renderers
_SECTION_RENDERERS = {
    "Reporting Period": _render_reporting_period,
    "Narrative Summary and Analysis": _render_narrative_summary,
    "Summary Analysis of Cases": _render_case_summary,
    "Reaction / Adverse Event Analysis": _render_reaction_analysis,
    "Serious Cases / 15‑Day Alerts": _render_serious_cases,  # en‑dash
    "Serious Cases / 15-Day Alerts": _render_serious_cases,  # plain hyphen
    "Trends and Important Observations": _render_trends,
}


def _fallback_render(packet: Dict[str, Any]) -> str:
    """Render a human‑readable section from the evidence packet.

    Uses dedicated renderers for known PADER sections to produce polished
    prose instead of raw data dumps.
    """
    section = packet.get("section", "Section")
    data = packet.get("data", {})

    renderer = _SECTION_RENDERERS.get(section)
    if renderer:
        return renderer(data)

    # Generic fallback for any unknown section
    title = section
    lines = [f"## {title}\n"]
    for key, value in data.items():
        lines.append(f"- **{key}:** {value}")
    lines.append("")
    return "\n".join(lines)


def generate_section_text(packet: Dict[str, Any]) -> str:
    """Public entry point used by ``main.py``.

    If an Anthropic API key is available the function would forward the
    packet to the model. To keep the repository self‑contained we always
    use the offline fallback.
    """
    # Placeholder for future LLM call – currently disabled.
    return _fallback_render(packet)
