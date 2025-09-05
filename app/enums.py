"""Module that contains enums"""

from enum import Enum, auto


class FilterType(Enum):
    """Filter type enum used in retrieving gps"""

    LOCATION_AND_OUTLINES = auto()
    OUTLINES_ONLY = auto()
