import re

from collections import defaultdict
from typing import Dict, List

def build_value_regex(players: set[str]) -> re.Pattern:
    players_re = "|".join(re.escape(p) for p in players)
    pattern = rf"""
        ^
        (?P<key>.+?\(({players_re})\))    # key up to and including (playername)
        (?:\s*:\s*(?P<value>.+))?         # optionally: colon + value (non-capturing group)
        $
    """
    return re.compile(pattern, re.VERBOSE)


def normalize_item_name(s: str) -> str:
    # Remove anything in parentheses
    s = re.sub(r"\([^)]*\)", "", s)

    # Replace underscores with spaces
    s = s.replace("_", " ")

    # Replace points with spaces
    s = s.replace(".", " ")

    # Lowercase
    s = s.lower()

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)

    return s.strip()

def format_fuzzy_search_results(
    search_results: Dict[str, List[Dict[str, object]]],
) -> List[str]:
    """
    Format fuzzy search results into human-readable output lines.

    Groups matches by matched item and aggregates spheres.

    Returns:
        List[str]: formatted output lines
    """

    output: List[str] = []

    for search_item, matches in search_results.items():
        grouped = defaultdict(lambda: {"spheres": set(), "confidence": 0})

        for match in matches:
            matched_item = match["matched_item"]
            grouped[matched_item]["spheres"].add(match["sphere"])
            grouped[matched_item]["confidence"] = max(
                grouped[matched_item]["confidence"],
                match["confidence"],
            )

        for matched_item, data in grouped.items():
            spheres = ", ".join(sorted(data["spheres"], key=int))
            confidence = data["confidence"]

            output.append(
                f"{search_item} → {matched_item} "
                f"Sphere{"(s)" if len(spheres) > 1 else ''} {spheres} "
                f"(confidence {confidence}%)"
            )

    return output
