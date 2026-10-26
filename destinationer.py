# destinationer.py
# ----------------
# Country and city logic for the flight board.
# Reverse-engineering evidence (from the original app): it uses a
# case-insensitive lookup (_lookup_country) and a country_to_cities index
# so flights can be filtered by country (e.g. Spain).
#
# The index itself lives in city_country.json (country -> list of cities),
# built from an official airport/city list — exactly like the original app,
# which loads its mapping from a JSON file instead of hard-coding it.

import json
from pathlib import Path

CITY_COUNTRY_FILE = Path(__file__).parent / "city_country.json"

# Index: country -> all cities in our data that belong to it.
# Loaded once at import; {country: [cities]}
with CITY_COUNTRY_FILE.open(encoding="utf-8") as _f:
    COUNTRY_TO_CITIES = json.load(_f)

# Reverse index: "frankfurt" -> "Germany", built once, used by _lookup_country.
_CITY_TO_COUNTRY = {
    city.lower(): country
    for country, cities in COUNTRY_TO_CITIES.items()
    for city in cities
}


def _lookup_country(name):
    """Find the canonical country for a country name OR a city name.

    Case-insensitive on purpose: 'SPAIN', 'spain' and ' Spain ' must all
    find 'Spain', and a city like 'Barcelona' must find 'Spain' too.
    Returns the country name (string) or None if not found.
    """
    if not isinstance(name, str):
        return None
    wanted = name.strip().lower()

    # 1. Direct match on the country name
    for country in COUNTRY_TO_CITIES:
        if country.lower() == wanted:
            return country

    # 2. City -> country via the reverse index
    return _CITY_TO_COUNTRY.get(wanted)


def country_for_city(city_name):
    """Return the country a destination city belongs to, or None."""
    if not isinstance(city_name, str):
        return None
    return _CITY_TO_COUNTRY.get(city_name.strip().lower())


def is_domestic(city_name):
    """True when the city belongs to Sweden — used for the D/I flag."""
    return country_for_city(city_name) == "Sweden"


def filter_flights_by_country(flights, country_name):
    """Return only the flights whose destination city is in the given country.

    Accepts a country ('Spain') or even a city ('barcelona') — both work,
    because _lookup_country maps both to the canonical country.
    """
    country = _lookup_country(country_name)
    if country is None:
        return []

    cities = {city.lower() for city in COUNTRY_TO_CITIES[country]}
    return [
        flight
        for flight in flights
        if isinstance(flight.get("toCity"), str)
        and flight["toCity"].lower() in cities
    ]


def available_countries():
    """Sorted list of all countries in the index (for friendly error messages)."""
    return sorted(COUNTRY_TO_CITIES.keys())
