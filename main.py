from app import extract_playthrough_block, parse_spheres, find_item_spheres_fuzzy, \
    find_earliest_check_for_each_player_in_each_players_game
from utils import build_value_regex, download_input_file, collect_files, get_players
from utils import format_fuzzy_search_results

"""
-------------- INPUT VARS HERE --------------
"""

# case doesn't matter, underscores don't matter, and it will match substrings
possible_unblocking_items = [
    "Grenade",
    "Bash",
    "Master Sword",
]

# the download link for the spoiler log
log_url = "https://archipelago.gg/dl_spoiler/foo_bar"
room_id = "fooOooOooOo0Oo-b4Ar"

# a threshold of % match that must be met for fuzzy matcher to return a match
fuzzy_threshold = 90

# set to true if debugging, it will enable some extra logging
DEBUG_MODE = False

"""
-------------- END OF INPUT --------------
"""
if __name__ == "__main__":
    room_json, static_tracker_json, tracker_json, datapackage_jsons = collect_files(room_id)
    players_dict = {}
    player_number = 0
    for player, game in get_players(room_json):
        player_number += 1
        players_dict[player] = {'name': player, 'game': game, "player number": player_number}
    players = set(players_dict.keys())

    value_re = build_value_regex(players)
    spoiler_lines = download_input_file(log_url)
    block = extract_playthrough_block(spoiler_lines)
    spheres = parse_spheres(block, value_re)
    search_results = find_item_spheres_fuzzy(spheres, possible_unblocking_items, fuzzy_threshold)

    for line in format_fuzzy_search_results(search_results):
        print(line)

    earliest_checks = find_earliest_check_for_each_player_in_each_players_game(players_dict, spheres, datapackage_jsons, tracker_json)
    for player, entry in earliest_checks.items():
        for thing in entry:
            if not thing:
                continue
            print(f"Potentially unblocking {player}: {thing.get("unlock")} at {thing.get('location')} (sphere {thing.get('sphere')})")