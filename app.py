import re

from collections import defaultdict
from typing import Dict, List
from thefuzz import fuzz

from utils import normalize_item_name


def extract_playthrough_block(lines: list[str]) -> list[str]:
    BLOCK_START_RE = re.compile(r"^\s*(\d+)\s*:\s*\{\s*$")
    in_section = False
    brace_depth = 0
    body: list[str] = []

    for line in lines:
        raw = line.rstrip()
        stripped = raw.strip()

        # Wait for the marker
        if not in_section:
            if stripped == "Playthrough:":
                in_section = True
            continue

        # Ignore empty lines completely
        if not stripped:
            continue

        # New block header
        if BLOCK_START_RE.match(raw):
            body.append(raw)
            brace_depth = 1
            continue

        # Inside a block
        if brace_depth > 0:
            body.append(raw)
            brace_depth += raw.count("{")
            brace_depth -= raw.count("}")
            continue

        # Non-empty, not a block start, and not inside a block → stop
        break

    return body

def parse_spheres(block_lines: list[str], value_re) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    current_id = None
    current_data = None

    for line in block_lines:
        line = line.strip()

        if not line:
            continue

        # Match: number: {
        m = re.match(r"(\d+)\s*:\s*\{", line)
        if m:
            current_id = m.group(1)  # always digits now
            current_data = {}
            result[current_id] = current_data
            continue

        if line == "}":
            current_id = None
            current_data = None
            continue

        # Match: key: value
        if current_data is not None:
            m = value_re.match(line)

            if not m:
                raise ValueError(f"Unparseable line: {line}")

            key = m.group("key").strip()
            value = m.group("value") or ""
            value = value.strip()

            current_data[key] = value

    return result

def find_item_spheres_fuzzy(
    spheres: Dict[str, Dict[str, str]],
    items: List[str],
    fuzzy_threshold: int,
) -> Dict[str, List[Dict[str, object]]]:
    """
    Fuzzy-match items against playthrough values.

    Returns:
        item -> list of {
            matched_item: str,
            sphere: str,
            confidence: int
        }
    """

    ratio_funcs = (
        fuzz.ratio,
        fuzz.partial_ratio,
        fuzz.token_set_ratio,
        fuzz.token_sort_ratio,
    )

    normalized_items = {
        item: normalize_item_name(item)
        for item in items
    }

    results: Dict[str, List[Dict[str, object]]] = defaultdict(list)

    for sphere, locations in spheres.items():
        for raw_value in locations.values():
            normalized_value = normalize_item_name(raw_value)

            for original_item, norm_item in normalized_items.items():
                best_ratio = 0

                for func in ratio_funcs:
                    ratio = func(norm_item, normalized_value)
                    if ratio == 100:
                        best_ratio = 100
                        break
                    if ratio > best_ratio:
                        best_ratio = ratio

                if best_ratio >= fuzzy_threshold:
                    results[original_item].append({
                        "matched_item": raw_value,
                        "sphere": sphere,
                        "confidence": best_ratio,
                    })

    return dict(results)
