import argparse
import json
import os
from pathlib import Path

from analysis import load_data, compute_basic_stats, deduplicate_cases
from evidence import build_evidence_packets
from human_review import review_packets
from llm_interface import generate_section_text
from report_generator import render_report


def main():
    parser = argparse.ArgumentParser(description="GenAR PADER pipeline")
    parser.add_argument("--data", required=True, help="Path to the ICSR CSV or Excel file")
    parser.add_argument("--out", default="output", help="Output directory")
    parser.add_argument("--non-interactive", action="store_true", help="Auto‑approve all review steps")
    args = parser.parse_args()

    data_path = Path(args.data)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load raw data (CSV or Excel) and compute basic statistics
    df = load_data(data_path)
    stats = compute_basic_stats(df)

    # Build evidence packets for each PADER section
    packets = build_evidence_packets(stats)

    # Human review gate (auto‑approve in non‑interactive mode)
    review_log = review_packets(packets, non_interactive=args.non_interactive)

    # Generate prose for each section (or placeholder if flagged)
    rendered_sections = {}
    for name, packet in packets.items():
        decision = review_log.get(name, "approved")
        if decision == "approved":
            rendered_sections[name] = generate_section_text(packet)
        else:
            rendered_sections[name] = f"[FLAGGED SECTION – review needed]\n\nNote: {decision}"

    # Render final markdown report
    report_md = render_report(rendered_sections)
    report_path = out_dir / "pader_report.md"
    report_path.write_text(report_md, encoding="utf-8")

    # Write case listing CSV (deduplicated cases)
    cases_df = deduplicate_cases(df)
    cases_df.to_csv(out_dir / "case_listing.csv", index=False)

    # Write a simple run‑log JSON containing validation stats and review decisions
    run_log = {
        "validation": stats,
        "review_log": review_log,
    }
    (out_dir / "run_log.json").write_text(json.dumps(run_log, indent=2, default=str), encoding="utf-8")

if __name__ == "__main__":
    main()
