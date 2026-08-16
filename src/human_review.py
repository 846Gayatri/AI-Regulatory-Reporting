import json
import sys

def review_packets(packets, non_interactive=False):
    """Interactively review evidence packets.

    Args:
        packets (dict): Mapping of section name to evidence packet dict.
        non_interactive (bool): If True, automatically approve all packets.

    Returns:
        dict: Mapping of section name to decision string ("approved" or "flagged: <note>").
    """
    decisions = {}
    if non_interactive:
        for name in packets:
            decisions[name] = "approved"
        return decisions

    for name, packet in packets.items():
        print(f"\n=== Review {name} ===")
        print(json.dumps(packet, indent=2, ensure_ascii=False))
        resp = input("Approve? (y=approve, f=flag) [y]: ").strip().lower()
        if resp == "f":
            note = input("Enter flag note: ").strip()
            decisions[name] = f"flagged: {note}" if note else "flagged"
        else:
            decisions[name] = "approved"
    return decisions
