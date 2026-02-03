import json
import re

from collections import defaultdict
from typing import Dict, List, Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

archipelago_api_base_url = "https://archipelago.gg/api"

def _build_room_api_url(room_id: str) -> str:
    return archipelago_api_base_url + f"/room_status/{room_id}"

def _build_static_tracker_url(tracker_id: str) -> str:
    return archipelago_api_base_url + f"/static_tracker/{tracker_id}"

def _build_tracker_url(tracker_id: str) -> str:
    return archipelago_api_base_url + f"/tracker/{tracker_id}"

def get_players(room_json: Dict[str, Any]) -> List[str]:
    players = room_json.get("players", [])
    return players

def _build_datapackage_url(game_specific_hash: str) -> str:
    return archipelago_api_base_url + f"/datapackage/{game_specific_hash}"

def _get_room_json(room_id: str) -> Dict[str, Any]:
    return download_json(_build_room_api_url(room_id))

def _get_tracker_id(room_json: Dict[str, Any]) -> str:
    id = room_json.get("tracker",'')
    if id:
        return id
    else:
        raise Exception("Could not find tracker id")

def _get_static_tracker_json(tracker_id: str) -> Dict[str, Any]:
    return download_json(_build_static_tracker_url(tracker_id))

def _get_tracker_json(tracker_id: str) -> Dict[str, Any]:
    return download_json(_build_tracker_url(tracker_id))

def _get_datapackage_jsons(static_tracker_json: Dict[str, Any]) -> Dict[str, Any]:
    checksums = {}
    datapackage = static_tracker_json.get("datapackage", {})
    datapackages = {}
    if not datapackage:
        raise Exception("Could not find datapackage in static tracker JSON")
    for key, value in datapackage.items():
        if not key == "Archipelago":
            checksums[key] = value.get("checksum")
    for name, checksum in checksums.items():
        url = _build_datapackage_url(checksum)
        datapackages[name] = download_json(url)
    return datapackages

def collect_files(room_id: str):
    room_json = _get_room_json(room_id)
    tracker_id = _get_tracker_id(room_json)
    static_tracker_json = _get_static_tracker_json(tracker_id)
    tracker_json = _get_tracker_json(tracker_id)
    datapackage_jsons = _get_datapackage_jsons(static_tracker_json)
    return room_json, static_tracker_json, tracker_json, datapackage_jsons

def download_json(url: str) -> Dict:
    """
    Download a JSON file from a URL and return it as a JSON object.
    """
    try:
        with urlopen(url) as response:
            text = response.read().decode("utf-8", errors="replace")
            return json.loads(text)
    except HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code} while downloading {url}") from e
    except URLError as e:
        raise RuntimeError(f"Failed to reach {url}: {e.reason}") from e

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
                f"Desired: {search_item}, Matched: {matched_item} "
                f"(confidence {confidence}%) "
                f"→ Sphere{"(s)" if len(spheres) > 1 else ''} {spheres}"
            )

    return output


def download_input_file(url: str) -> list[str]:
    """
    Download a text file from a URL and return it as a list of lines,
    suitable for extract_playthrough_block().
    """
    try:
        with urlopen(url) as response:
            # Decode as UTF-8, replacing invalid bytes safely
            text = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code} while downloading {url}") from e
    except URLError as e:
        raise RuntimeError(f"Failed to reach {url}: {e.reason}") from e

    # Normalize line endings and split into lines
    return text.splitlines()

def build_location_dict(players_dict: Dict[str, Any], static_tracker_json, tracker_json, datapackage_jsons) -> Dict[str, Any]:
    locations_dict = {player: {} for player in players_dict.keys()}
    for player, info in players_dict.items():
        player_number = info["number"]
        game = ''
        for player_game_list_entry in static_tracker_json["player_game"]:
            if player_number == player_game_list_entry["player"]:
                game = player_game_list_entry["game"]
        if not game:
            raise Exception(f"Could not find game for {player}")
        checksum = static_tracker_json["datapackage"][game]["checksum"]
