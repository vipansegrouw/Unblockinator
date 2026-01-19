import re

def build_value_regex(players: set[str]) -> re.Pattern:
    players_re = "|".join(re.escape(p) for p in players)
    pattern = rf"""
        ^
        (?P<key>.+?\(({players_re})\))    # key up to and including (playername)
        \s*                               # optional whitespace after key
        (?P<value>.*)                     # value is everything else after
        $
    """
    return re.compile(pattern, re.VERBOSE)

def normalize_item_name(s: str) -> str:
    # Remove anything in parentheses
    s = re.sub(r"\([^)]*\)", "", s)

    # Replace underscores with spaces
    s = s.replace("_", " ")

    # Lowercase
    s = s.lower()

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)

    return s.strip()
