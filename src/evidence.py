# src/evidence.py
"""Create section‑specific evidence packets for the PADER report.

Each packet is a JSON‑serialisable dict containing:
- `section`: human‑readable name matching the six PADER sections.
- `reporting_period`: start and end dates from the stats.
- `data`: a subset of the global stats required for that section.
- `instructions`: short prompt text (used by llm_interface) describing the desired prose.
"""

from typing import Dict, Any


def _base_packet(stats: Dict[str, Any], section: str) -> Dict[str, Any]:
    return {
        "section": section,
        "reporting_period": f"{stats.get('start_date', '')} to {stats.get('end_date', '')}",
        "data": {},
        "instructions": "",
    }


def build_evidence_packets(stats: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return a dict mapping section names to evidence packets.

    Sections follow the naming used in the challenge:
    1. Reporting Period
    2. Narrative Summary and Analysis
    3. Summary Analysis of Cases
    4. Reaction / Adverse Event Analysis
    5. Serious Cases / 15‑Day Alerts
    6. Trends and Important Observations
    """
    packets: Dict[str, Dict[str, Any]] = {}

    # 1. Reporting Period – just the dates
    rp = _base_packet(stats, "Reporting Period")
    rp["data"] = {
        "start_date": stats.get("start_date"),
        "end_date": stats.get("end_date"),
    }
    rp["instructions"] = "Provide the reporting period dates in ISO format."
    packets["Reporting Period"] = rp

    # 2. Narrative Summary and Analysis
    ns = _base_packet(stats, "Narrative Summary and Analysis")
    ns["data"] = {
        "total_cases": stats.get("total_cases"),
        "serious_cases": stats.get("serious_cases"),
        "non_serious_cases": stats.get("non_serious_cases"),
        "top_reactions": stats.get("top_reactions", []),
        "top_serious_reactions": stats.get("top_serious_reactions", []),
    }
    ns["instructions"] = "Write a short neutral narrative (150‑220 words) summarising the overall safety profile, using the numbers provided. Do not draw safety conclusions."
    packets["Narrative Summary and Analysis"] = ns

    # 3. Summary Analysis of Cases
    sc = _base_packet(stats, "Summary Analysis of Cases")
    sc["data"] = {
        "age_groups": stats.get("age_groups", []),
        "sex_counts": stats.get("sex_counts", {}),
        "country_counts": stats.get("country_counts", []),
    }
    sc["instructions"] = "Summarise the case demographics (age, sex, country) in a concise paragraph (120‑180 words)."
    packets["Summary Analysis of Cases"] = sc

    # 4. Reaction / Adverse Event Analysis
    ra = _base_packet(stats, "Reaction / Adverse Event Analysis")
    ra["data"] = {
        "top_reactions": stats.get("top_reactions", []),
        "top_serious_reactions": stats.get("top_serious_reactions", []),
    }
    ra["instructions"] = "List the most frequent reactions and serious reactions, each as a short bullet point."
    packets["Reaction / Adverse Event Analysis"] = ra

    # 5. Serious Cases / 15‑Day Alerts
    sa = _base_packet(stats, "Serious Cases / 15‑Day Alerts")
    sa["data"] = {
        "serious_cases": stats.get("serious_cases"),
    }
    sa["instructions"] = "State the count of serious cases and note any 15‑day alert thresholds (if applicable)."
    packets["Serious Cases / 15‑Day Alerts"] = sa

    # 6. Trends and Important Observations
    tr = _base_packet(stats, "Trends and Important Observations")
    tr["data"] = {
        "total_cases": stats.get("total_cases"),
        # In a real system we would compute month‑wise trends; here we just pass the total.
    }
    tr["instructions"] = "Mention any noteworthy trends such as increasing case counts over time, if observable. Keep it brief."
    packets["Trends and Important Observations"] = tr

    return packets
