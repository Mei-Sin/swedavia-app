# Swedavia Flight Board — All 10 Swedish Airports

**APL Project 2026 — "Recreate an app with GenAI" (Swedavia)**

A Python command-line app that recreates the original Swedavia flight board: a menu-driven terminal program with departures and arrivals for all 10 Swedavia airports, country filtering, a D/I (domestic/international) flag, real UTC → Swedish local time conversion and ghost-entry filtering.

**The evidence we started from (the original's output):**

```
LH819 — Lufthansa (LH)
  Departing GOT to Frankfurt
  Status:   Departed
  Terminal: T1   Gate: 15
  Scheduled: 17:55 UTC  ->  18:55 CET
```

Our recreation produces **exactly this record** — and keeps the original's structure: `_is_valid_flight` (filters the API's empty "ghost entries"), `_print_flight` (formats each flight), `_is_upcoming` (orders the board), `_print_flights_paged` (pages long lists) and `destinationer.py` (case-insensitive country/city lookup loaded from `city_country.json`).

## Features

- **Menu with 6 options** — departures, arrivals, country filter, flight lookup, airport list, exit
- **All 10 Swedavia airports** — ARN, BMA, GOT, MMX, UME, LLA, KRN, VBY, OER, RNB
- **124 flights of sample data** (62 departures + 62 arrivals) that mirror the Swedavia API field names — including 2 ghost entries on purpose, so the filtering is visible
- **`city_country.json`** — 62 countries / 193 cities, built the same way the original built it: from an official city list, loaded at runtime (never hard-coded)
- **D/I flag** — a flight is marked `D` (domestic) or `I` (international) by looking up the destination city's country
- **Real time-zone conversion** — `Sched: 16:25 UTC → 17:25 CET` via `zoneinfo` (handles CET and CEST)
- **Ghost-entry filtering** — broken API records are skipped and counted
- **Paging** — boards longer than `PAGE_SIZE = 50` flights are printed page by page
- **Country filter** — `spain` works in any case; even a city name (`barcelona`) resolves to its country
- **Optional live mode** — `--api` uses the real Swedavia Flight Info API v2 when you add a free subscription key

## Getting started

Requires Python 3.9+ (for `zoneinfo`).

### Windows (Git Bash) — the full setup used for this project

Open the `swedavia-app` folder in File Explorer, right-click empty space inside it and choose **Git Bash Here**, then run:

```bash
python --version                       # check Python 3.9+ (if not found, use `py` instead of `python`)
python -m venv venv                    # one-time: create a virtual environment
source venv/Scripts/activate           # activate it — the line now starts with (venv)
pip install -r requirements.txt        # one-time: install the Windows timezone data
python airport.py                      # start the menu app
```

Next time you open the project, you only need `source venv/Scripts/activate` before running the app.

### macOS / Linux / Ubuntu (WSL)

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

### Example session

```
================ Swedavia Flight Board (recreation) ================
  1. Departures for an airport
  2. Arrivals for an airport
  3. All flights to a country
  4. Find one flight (any airport)
  5. List the 10 Swedavia airports
  6. Exit
=====================================================================
Choose 1-6: 4
Flight number (e.g. LH819): lh819

=== LH819 — Lufthansa (LH)   [GOT] ===
  Departing GOT (Gothenburg)  →  Frankfurt (FRA)   D/I: I
  Status: Departed   Terminal: T1   Gate: 15
  Sched: 17:55 UTC → 18:55 CET
```

## Connecting the real Swedavia API

The original app reads its data from the [Swedavia Flight Info API v2](https://www.swedavia.se/flyginfo-api/), which needs a free subscription key:

1. Request a key from Swedavia's developer portal
2. Create a `.env` file (or set an environment variable):
   ```
   SWEDAVIA_API_KEY=your-key-here
   ```
3. Run `python airport.py --api`

The live client (`swedavia_client.py`) normalizes the API's field names onto the shapes the board prints, so both data sources work through the same code.

## Project structure

```
swedavia-app/
├── airport.py            # main menu app: _is_valid_flight, _is_upcoming,
│                         # _print_flight, _print_flights_paged, argparse
├── destinationer.py      # country logic: _lookup_country, country_for_city,
│                         # is_domestic (D/I), filter_flights_by_country
├── swedavia_client.py    # optional live Swedavia API v2 client (needs a key)
├── city_country.json     # 62 countries -> 193 cities (D/I + country filter)
├── data/
│   └── flights.json      # 124 flights, 10 airports + 2 ghost entries
├── requirements.txt      # tzdata (Windows timezone data) — the only dependency
├── DOCUMENTATION.md      # full project documentation (4 phases + conclusion, per the guide)
├── FÖRKLARING.md         # how the code works, file by file
└── README.md
```

## Documentation

See [DOCUMENTATION.md](./DOCUMENTATION.md) for the full reverse-engineering story following the four phases of the assignment guide — research, implementation, completion, problems & solutions, conclusion, plus the video plan and the GenAI prompt log. [FÖRKLARING.md](./FÖRKLARING.md) explains the code file by file.
