from app import download_input_file, extract_playthrough_block, parse_spheres, find_item_spheres_fuzzy
from utils import build_value_regex
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

# list every player's "slot" name as it appears in archipelago
players = {
    "player1",
    "player 2",
}

# the download link for the spoiler log
log_url = "https://archipelago.gg/dl_spoiler/foo_bar"

# a threshold of % match that must be met for fuzzy matcher to return a match
fuzzy_threshold = 90

"""
-------------- END OF INPUT --------------
"""

value_re = build_value_regex(players)
spoiler_lines = download_input_file(log_url)
block = extract_playthrough_block(spoiler_lines)
spheres = parse_spheres(block, value_re)
search_results = find_item_spheres_fuzzy(spheres, possible_unblocking_items, fuzzy_threshold)

for line in format_fuzzy_search_results(search_results):
    print(line)