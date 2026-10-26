# swedavia_client.py
# ------------------
# OPTIONAL live connection to the real Swedavia Flight Info API (v2).
#
# The original app fetches its data from api.swedavia.se, which requires a
# free subscription key (sent as the Ocp-Apim-Subscription-Key header).
# The API exposes two endpoints per airport:
#     GET https://api.swedavia.se/flightinfo/v2/{airport}/departures
#     GET https://api.swedavia.se/flightinfo/v2/{airport}/arrivals
# Without a key the app runs on data/flights.json instead, which mirrors
# the same fields — so the recreation works offline out of the box.
#
# To go live later:
#   1. Request a key at Swedavia's developer portal
#   2. Put it in a .env file or environment variable: SWEDAVIA_API_KEY=...
#   3. Run: python airport.py --api

import json
import os
import urllib.request

API_BASE = "https://api.swedavia.se/flightinfo/v2/{airport}/{board}"


def _fetch(airport, board):
    """Call one API endpoint and return the raw flights list."""
    key = os.environ.get("SWEDAVIA_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "No SWEDAVIA_API_KEY found.\n"
            "Run without --api to use the bundled sample data, or add your key "
            "to a .env file first (see README.md)."
        )
    request = urllib.request.Request(
        API_BASE.format(airport=airport, board=board),
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    # The real response wraps the list in a "flights" key.
    return payload.get("flights", [])


def _normalize_flight(raw, airport, board):
    """Map the API's field names onto the shapes airport.py prints.

    The API gives airport ids, not city names, so toCity/fromCity fall back
    to the IATA code for destinations the city_country.json does not know.
    """
    dest_id = raw.get("flightDestinationId") or raw.get("flightDestinationAirportId") or "?"
    return {
        "flightId": raw.get("flightId") or "",
        "airlineName": raw.get("airlineName") or raw.get("airlineIata") or "Unknown airline",
        "airlineIata": raw.get("airlineIata") or "",
        "type": board,
        "airport": airport,
        "fromId": airport if board == "departures" else dest_id,
        "fromCity": airport if board == "departures" else dest_id,
        "toId": dest_id if board == "departures" else airport,
        "toCity": dest_id if board == "departures" else airport,
        "scheduleTime": raw.get("scheduleTime") or "",
        "statusGeneric": raw.get("statusGeneric") or {},
        "terminalId": raw.get("terminalId"),
        "gateId": raw.get("gateId"),
        "lateTime": raw.get("lateTime"),
    }


def fetch_departures(airport="GOT"):
    """Live departures for one airport, normalized for the board."""
    return [_normalize_flight(f, airport, "departures") for f in _fetch(airport, "departures")]


def fetch_arrivals(airport="GOT"):
    """Live arrivals for one airport, normalized for the board."""
    return [_normalize_flight(f, airport, "arrivals") for f in _fetch(airport, "arrivals")]
