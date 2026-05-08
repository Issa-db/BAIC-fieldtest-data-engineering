# transform/country_mapper.py

from typing import Optional, Tuple, Dict

# Extend this lookup as new test routes appear
CITY_TO_COUNTRY: Dict[str, str] = {
    # Germany
    "stuttgart":      "Germany",
    "münchen":        "Germany",
    "munich":         "Germany",
    "frankfurt":      "Germany",
    "berlin":         "Germany",
    "hamburg":        "Germany",
    "köln":           "Germany",
    "cologne":        "Germany",
    "nürnberg":       "Germany",
    "nuremberg":      "Germany",
    "德国":           "Germany",

    # France
    "paris":          "France",
    "lyon":           "France",
    "marseille":      "France",
    "bordeaux":       "France",
    "法国":           "France",

    # Italy
    "milan":          "Italy",
    "milano":         "Italy",
    "rome":           "Italy",
    "roma":           "Italy",
    "florence":       "Italy",
    "firenze":        "Italy",
    "意大利":         "Italy",

    # Switzerland
    "zurich":         "Switzerland",
    "zürich":         "Switzerland",
    "geneva":         "Switzerland",
    "genève":         "Switzerland",
    "bern":           "Switzerland",
    "瑞士":           "Switzerland",

    # Austria
    "vienna":         "Austria",
    "wien":           "Austria",
    "salzburg":       "Austria",
    "奥地利":         "Austria",

    # Netherlands
    "amsterdam":      "Netherlands",
    "rotterdam":      "Netherlands",
    "荷兰":           "Netherlands",

    # Belgium
    "brussels":       "Belgium",
    "bruxelles":      "Belgium",
    "比利时":         "Belgium",
}


def map_location_to_country(location_raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Map a raw location string to a standardised country name.
    Returns (country, warning). warning is set if the location is unrecognised.
    """
    if not location_raw:
        return None, "empty location"

    text = str(location_raw).lower().strip()

    # Direct lookup
    for key, country in CITY_TO_COUNTRY.items():
        if key in text:
            return country, None

    return None, f"unrecognised location: '{location_raw}' — add to CITY_TO_COUNTRY"