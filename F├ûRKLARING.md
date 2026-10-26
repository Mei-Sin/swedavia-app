# FÖRKLARING — How the Code Works (Explanation)

This file explains every file in the project and why each part exists. The names follow the original app's structure wherever the evidence revealed it (functions starting with `_` are internal helpers, the Swedish module name `destinationer` means "destinations").

## The big picture

```
                   you (the menu in airport.py)
                            │ chooses 1-6
                            ▼
        data/flights.json  ──►  _is_valid_flight()   ghost entries removed
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
        one airport    country filter   flight lookup
              │             │              │
              └──────► destinationer.py ◄──┘
                       city_country.json decides
                       country, and D or I flag
                            │
                            ▼
                 _print_flight() per flight
                 UTC time → Europe/Stockholm (CET/CEST)
```

## File by file

### `airport.py` — the app itself

| Part | What it does |
|------|--------------|
| `MENU` / `main()` | Prints the 6-option menu, reads your choice in a loop, and calls the right function for options 1-5. Option 6 exits. |
| `load_flights()` | Reads `data/flights.json`. With `--api` it calls `swedavia_client.py` instead — the rest of the app never notices the difference. |
| `_is_valid_flight(flight)` | The "ghost guard". Returns `False` when a record has no flight id, no destination city or no schedule time. This mirrors the original app: public APIs sometimes return empty records that must not be printed. |
| `_is_upcoming(flight)` | `True` while a flight is still Scheduled / Check-in open / Boarding / Delayed. Used to sort the board: upcoming flights first, departed and landed last. |
| `_parse_utc()` / `_local_parts()` | Converts the API's UTC timestamp (`2026-10-26T17:55:00Z`) to Swedish local time with `zoneinfo` (`Europe/Stockholm`). Sweden has two time zones across the year — CET and CEST — and `zoneinfo` picks the right one automatically. |
| `_print_flight(flight)` | Prints one flight block in the original style: `Status: … Terminal: … Gate: …` and `Sched: 17:55 UTC → 18:55 CET`, plus the `D/I` flag. Delayed flights also show their expected time. |
| `_print_flights_paged(flights)` | Prints the board in pages of `PAGE_SIZE = 50` and pauses between pages, so very long boards stay readable. |
| `_choose_airport()` | Shows the 10 airports and lets you pick by number or code (e.g. `3` or `GOT`). Empty input defaults to ARN. |

### `destinationer.py` — the country logic

| Part | What it does |
|------|--------------|
| `COUNTRY_TO_CITIES` | Loaded once from `city_country.json`: `{country: [cities]}`. Keeping it in JSON (not code) is what the original does — data belongs in data files. |
| `_lookup_country(name)` | Case-insensitive lookup of a **country** (`SPAIN`, `spain`) or even a **city** (`barcelona` → `Spain`). Returns the canonical country or `None`. This exact behaviour was one of the clues about the original. |
| `country_for_city(city)` / `is_domestic(city)` | Powers the `D/I` flag: if the destination city belongs to Sweden the flight is domestic (`D`), otherwise international (`I`). |
| `filter_flights_by_country(flights, country)` | Returns only flights whose destination city belongs to the country. |
| `available_countries()` | Sorted list of all 62 countries, used when you type an unknown name — the app answers with a helpful list instead of crashing. |

### `city_country.json` — the data behind country filtering and D/I

62 countries and 193 cities, built from an official city list (the same approach the original app used when it built its mapping from an Excel file). It is loaded at runtime, so adding a city never requires touching the code.

### `data/flights.json` — the sample flight database

124 flights (62 departures + 62 arrivals) across all 10 Swedavia airports, written in the Swedavia API's field style (`flightId`, `scheduleTime`, `statusGeneric`, `terminalId`, `gateId` …). It also contains **2 ghost entries on purpose**, so you can see `_is_valid_flight()` filter them and print the counter.

### `swedavia_client.py` — the optional live connection

Calls the real Swedavia Flight Info API v2 (endpoints `…/{airport}/departures` and `…/{airport}/arrivals`) with your subscription key, then **normalizes** the API's field names into the exact shapes the board prints. Both data sources — file or API — therefore flow through the same code path.

## Design decisions worth mentioning in the video

1. **Data first, then logic, then interface** — the JSON was built before the modules, because every other decision depends on the data's shape.
2. **The evidence dictated the structure** — the helper names (`_is_valid_flight`, `_print_flight`) came straight from the screenshot; recreating an app includes recreating its structure, not just its output.
3. **Offline by default** — the app works without any key or internet, and goes live later with one flag. This keeps the demo safe to record.
4. **Windows safety** — Windows lacks the IANA timezone database, so `requirements.txt` ships `tzdata` and the program prints the exact fix command if it is missing.
