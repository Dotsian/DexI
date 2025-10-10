from datetime import date

import holidays

from .dexi_types import SpecialMessage

CURRENT_YEAR = date.today().year

HOLIDAYS = holidays.country_holidays("US")
HOLIDAYS.update({date(CURRENT_YEAR, 10, 31): "Halloween"})


SPECIAL_MESSAGES: dict[str, SpecialMessage] = {
    "New Year's Day": {
        "emoji": "🎆",
        "messages": ["New year, new me!", "Happy New Years!"],
    },
    "Thanksgiving Day": {
        "emoji": "🦃",
        "messages": ["Gobble gobble!", "Happy Thanksgiving!"],
    },
    "Halloween": {
        "emoji": "👻",
        "messages": ["Boo!", "Spooky!", "Happy Halloween!", "Trick-or-treat!"],
    },
    "Christmas Day": {
        "emoji": "🎁",
        "messages": ["Ho ho ho!", "Jolly!", "Merry Christmas!"],
    },
}


def get_special() -> SpecialMessage | None:
    active_holiday = HOLIDAYS.get(date.today())

    if active_holiday is None:
        return None

    return SPECIAL_MESSAGES[active_holiday]
