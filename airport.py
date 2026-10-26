# airport.py
# ----------
# Swedavia Flight Board — all 10 Swedavia airports in one menu app.
# A reverse-engineered recreation of the original Python CLI app.
#
# Evidence we worked backwards from:
#   - The original prints flight details like:
#       Status: Departed   Terminal: T1   Gate: 15
#       Sched: 17:55 UTC -> 18:55 CET   D/I: I
#   - It has a _is_valid_flight() helper that skips empty "ghost entries"
#     returned by the API, and _print_flight() that formats each flight.
#   - It works together with destinationer.py (country/city logic loaded
#     from city_country.json) and pages long boards with _print_flights_paged().
#
# Usage:
#   python airport.py            start the menu (works offline on sample data)
#   python airport.py --api      use the real Swedavia Flight Info API v2 (needs a key)

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from destinationer import (
    available_countries,
    filter_flights_by_country,
    _lookup_country,
    is_domestic,
)
import swedavia_client

# Make sure the arrow (→) and Swedish letters print on every terminal.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_FILE = Path(__file__).parent / "data" / "flights.json"
LOCAL_TIMEZONE = None
try:
    LOCAL_TIMEZONE = ZoneInfo("Europe/Stockholm")  # Sweden: CET winter, CEST summer
except Exception:
    # Windows does not ship the IANA timezone database that zoneinfo uses.
    # The fix is one command:  pip install tzdata   (already in requirements.txt)
    raise SystemExit(
        "Timezone database not found on this computer.\n"
        "Fix it by running:  pip install tzdata\n"
        "(It is already listed in requirements.txt.)"
    )

PAGE_SIZE = 50  # _print_flights_paged shows this many flights per page

AIRPORTS = [
    ("ARN", "Stockholm Arlanda"),
    ("BMA", "Stockholm Bromma"),
    ("GOT", "Göteborg Landvetter"),
    ("MMX", "Malmö"),
    ("UME", "Umeå"),
    ("LLA", "Luleå"),
    ("KRN", "Kiruna"),
    ("VBY", "Visby"),
    ("OER", "Örnsköldsvik"),
    ("RNB", "Ronneby"),
]

MENU = """
================ Swedavia Flight Board (recreation) ================
  1. Departures for an airport
  2. Arrivals for an airport
  3. All flights to a country
  4. Find one flight (any airport)
  5. List the 10 Swedavia airports
  6. Exit
=====================================================================
"""


def load_flights(use_api=False):
    """Load flights either from the bundled sample data or the live API."""
    if use_api:
        return swedavia_client.fetch_departures("ARN") + swedavia_client.fetch_departures("GOT")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return data["flights"]


def _is_valid_flight(flight):
    """Return True for real flights, False for empty 'ghost entries'.

    The real API sometimes returns broken records: no flight id, no
    destination or no schedule time. Those must not be printed.
    """
    if not isinstance(flight, dict):
        return False
    if not flight.get("flightId"):
        return False
    if not flight.get("toCity"):
        return False
    if not flight.get("scheduleTime"):
        return False
    return True


def _is_upcoming(flight):
    """True when the flight has not yet departed/landed and is not cancelled."""
    status = (flight.get("statusGeneric") or {}).get("english", "").lower()
    return status not in ("departed", "landed", "cancelled")


def _parse_utc(schedule_time):
    """Turn an API timestamp like '2026-10-26T17:55:00Z' into a UTC datetime."""
    return datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))


def _local_parts(schedule_time):
    """Return (utc_hhmm, local_hhmm, local_zone_name) for a schedule time."""
    utc_time = _parse_utc(schedule_time)
    local_time = utc_time.astimezone(LOCAL_TIMEZONE)
    return (
        utc_time.strftime("%H:%M"),
        local_time.strftime("%H:%M"),
        local_time.strftime("%Z"),
    )


def _sort_board(flights):
    """Upcoming flights first (by time), then the rest (by time)."""
    upcoming = sorted(
        (f for f in flights if _is_upcoming(f)),
        key=lambda f: f["scheduleTime"],
    )
    past = sorted(
        (f for f in flights if not _is_upcoming(f)),
        key=lambda f: f["scheduleTime"],
    )
    return upcoming + past


def _print_flight(flight, show_airport=False):
    """Print one flight in the same style as the original app."""
    airline = "{} ({})".format(
        flight.get("airlineName") or "Unknown airline",
        flight.get("airlineIata") or "??",
    )

    if flight.get("type") == "arrivals":
        route = "From: {} ({})  →  {}".format(
            flight.get("fromCity", "Unknown"), flight.get("fromId", "?"), flight.get("toId", "?")
        )
        other_city = flight.get("fromCity", "")
    else:
        route = "Departing {} ({})  →  {} ({})".format(
            flight.get("fromId", "?"), flight.get("fromCity", "Unknown"),
            flight.get("toCity", "Unknown"), flight.get("toId", "?"),
        )
        other_city = flight.get("toCity", "")

    di_flag = "D" if is_domestic(other_city) else "I"
    airport_tag = "   [{}]".format(flight.get("airport", "?")) if show_airport else ""

    print("=== {} — {}{} ===".format(flight["flightId"], airline, airport_tag))
    print("  {}   D/I: {}".format(route, di_flag))

    status = (flight.get("statusGeneric") or {}).get("english", "Unknown")
    print(
        "  Status: {}   Terminal: {}   Gate: {}".format(
            status, flight.get("terminalId") or "-", flight.get("gateId") or "-"
        )
    )

    utc_hhmm, local_hhmm, zone_name = _local_parts(flight["scheduleTime"])
    line = "  Sched: {} UTC → {} {}".format(utc_hhmm, local_hhmm, zone_name)

    late_time = flight.get("lateTime")
    if late_time:
        late_utc, late_local, late_zone = _local_parts(late_time)
        line += "   Expected: {} {} (delayed)".format(late_local, late_zone)

    print(line)
    print()


def _print_flights_paged(flights, show_airport=False):
    """Print flights in pages of PAGE_SIZE, pausing between pages."""
    for index, flight in enumerate(flights, start=1):
        _print_flight(flight, show_airport=show_airport)
        if index % PAGE_SIZE == 0 and index < len(flights):
            print("-- page {} of {} -- press Enter for more, Ctrl+C to stop".format(
                index // PAGE_SIZE + 1, (len(flights) + PAGE_SIZE - 1) // PAGE_SIZE
            ))
            try:
                input()
            except EOFError:
                break


def _choose_airport():
    """Ask the user to pick one of the 10 airports. Returns (code, name)."""
    print("\nAirports:")
    for index, (code, name) in enumerate(AIRPORTS, start=1):
        print("  {:2}. {}  {}".format(index, code, name))
    while True:
        choice = input("Pick an airport (number or code, Enter = ARN): ").strip()
        if not choice:
            return AIRPORTS[0]
        if choice.isdigit() and 1 <= int(choice) <= len(AIRPORTS):
            return AIRPORTS[int(choice) - 1]
        for code, name in AIRPORTS:
            if choice.upper() == code:
                return (code, name)
        print("Not an airport on the list — try again.")


def _ask(text):
    """input() that survives Ctrl+D / piped input."""
    try:
        return input(text).strip()
    except EOFError:
        return ""


def show_board(flights, board_type):
    """Menu options 1 and 2: pick an airport, print its board."""
    code, name = _choose_airport()
    board = [f for f in flights if f.get("airport") == code and f.get("type") == board_type]

    valid = [f for f in board if _is_valid_flight(f)]
    ghosts = len(board) - len(valid)
    if ghosts:
        print("\n(Filtered out {} ghost entr{})".format(ghosts, "y" if ghosts == 1 else "ies"))

    board_sorted = _sort_board(valid)
    title = "Departures" if board_type == "departures" else "Arrivals"
    print("\n{} — {} ({}) — {} flight(s)\n".format(title, name, code, len(board_sorted)))
    if not board_sorted:
        print("No flights on this board.")
        return
    _print_flights_paged(board_sorted)


def show_country(flights):
    """Menu option 3: all departures to one country (across all airports)."""
    country_in = _ask("\nCountry or city (e.g. spain or barcelona): ")
    if not country_in:
        print("No input given.")
        return
    if _lookup_country(country_in) is None:
        print("Unknown country: {!r}".format(country_in))
        print("Available countries: {}".format(", ".join(available_countries())))
        return
    dep = [f for f in flights if f.get("type") == "departures" and _is_valid_flight(f)]
    found = _sort_board(filter_flights_by_country(dep, country_in))
    print("\nDepartures to {} — {} flight(s)\n".format(_lookup_country(country_in), len(found)))
    if not found:
        print("No flights to that country right now.")
        return
    _print_flights_paged(found, show_airport=True)


def show_flight(flights):
    """Menu option 4: find one flight by id (case-insensitive)."""
    wanted = _ask("\nFlight number (e.g. LH819): ").strip().lower()
    if not wanted:
        print("No input given.")
        return
    found = [
        f for f in flights
        if _is_valid_flight(f) and f["flightId"].lower() == wanted
    ]
    if not found:
        print("No flight with id {!r}. Try option 5 to browse, or 'LH819'.".format(wanted))
        return
    for flight in found:
        _print_flight(flight, show_airport=True)


def show_airports():
    """Menu option 5: list the airports."""
    print("\nThe 10 Swedavia airports:")
    for code, name in AIRPORTS:
        print("  {}  {}".format(code, name))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Swedavia Flight Board — 10 airports, recreated with GenAI."
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Fetch live data from the real Swedavia API (needs SWEDAVIA_API_KEY).",
    )
    args = parser.parse_args()

    flights = load_flights(use_api=args.api)

    while True:
        print(MENU)
        choice = _ask("Choose 1-6: ")
        if choice == "1":
            show_board(flights, "departures")
        elif choice == "2":
            show_board(flights, "arrivals")
        elif choice == "3":
            show_country(flights)
        elif choice == "4":
            show_flight(flights)
        elif choice == "5":
            show_airports()
        elif choice in ("6", "q", "Q"):
            print("Safe travels!")
            return
        else:
            print("Please choose a number 1-6.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSafe travels!")
