# Swedavia Flight Board — Project Documentation

**Project:** Recreate an app with GenAI — Swedavia (APL Project 2026)
**All documentation and the video are in English, as the assignment guide requires.**

**Goal:** We were shown a finished application — a Python command-line flight app for the Swedish airports run by Swedavia — and had to figure out what code made it, then recreate it ourselves using generative AI, working backwards like a detective.

**The evidence we started from** (screenshot of the original app):

```
LH819 — Lufthansa (LH)
  Departing GOT to Frankfurt
  Status:   Departed
  Terminal: T1   Gate: 15
  Scheduled: 17:55 UTC  ->  18:55 CET
```

plus clues about the code: a helper called `_is_valid_flight` that skips empty "**ghost entries**", a helper called `_print_flight` that formats each flight, a module called `destinationer.py` with a case-insensitive `_lookup_country` and a `country_to_cities` index for filtering flights by country, an `_is_upcoming` helper, paging with `PAGE_SIZE = 50`, a `city_country.json` file built from an official city list, and a menu-driven program covering the Swedavia airports with a `D/I` (domestic/international) flag on every flight.

---

## Phase 1: Research Phase (Pre-study)

### Information gathering

We began by studying the screenshot of the original application and listing everything it revealed. The output format told us which data fields must exist: every printed line — flight id, airline with IATA code, route, status, terminal, gate, and the double time display — maps directly to one field in the app's data. The dual time display (`17:55 UTC -> 18:55 CET`) showed that the app stores one UTC timestamp and converts it to Swedish local time, which led us to research how Sweden's time zones work: Sweden uses CET in winter and CEST in summer, and Python's built-in `zoneinfo` with the `Europe/Stockholm` zone handles both automatically. We also researched the official Swedavia Flight Info API (version 2): a public REST API that returns departures and arrivals per airport as JSON, protected by a free subscription key sent as the `Ocp-Apim-Subscription-Key` header. Finally, we studied the "ghost entry" problem — public APIs sometimes return empty or half-empty records that must be filtered before display — because the original app had a whole helper function dedicated to it.

### Choice of tools and techniques

| Choice | Reason |
|--------|--------|
| Python 3 (standard library only) | The original is a Python CLI app — matching the tool makes the recreation faithful and easy to explain in the video |
| `json` + bundled sample data | So the app works offline and during the demo; the data file mirrors the API's field names exactly |
| `urllib.request` (optional API client) | The standard-library way to call the real API when a key is available — no extra packages |
| `zoneinfo` (Europe/Stockholm) | Converts UTC schedule times to Swedish local time (CET/CEST), exactly like the original output shows |
| `argparse` + an interactive menu | Gives the app the demoed flags (`--api`) and the six-option menu visible in the original |
| `city_country.json` as a data file | The original loads its city-to-country mapping from a JSON file built from an official list — data belongs in data files, not in code |

### Planning

We planned to rebuild the app in the order its evidence suggested: first the data layer (`city_country.json` and the flight data, because every other decision depends on the data's shape), then `destinationer.py` (the country logic), then `airport.py` (validation, formatting, paging and the menu), and finally testing of every menu path before writing the documentation and recording the video.

### Problems and solutions during research

- **Problem:** The real Swedavia API requires a subscription key that we do not have.
  **Solution:** We built the app on a bundled data file that mirrors the API's fields — including ghost entries on purpose — and wrote a small optional client (`swedavia_client.py`) that is ready for a real key. Documented as a deliberate design decision.
- **Problem:** It was hard to know how faithful the recreation had to be — the screenshot only shows a few lines.
  **Solution:** We treated every visible detail (function names, output format, paging constant, the JSON file name) as a requirement, and filled the invisible parts (menu structure, airport list) with reasonable choices that we documented openly.

---

## Phase 2: Starting the Work (Implementation)

### How the work started

We started from the strongest clue: the flight `LH819` from Gothenburg to Frankfurt, departed, terminal T1, gate 15, scheduled 17:55 UTC which equals 18:55 CET. Working backwards, that single record told us the app must store at least: flight id, airline name and IATA code, origin and destination, a status, terminal, gate, and one UTC timestamp that gets converted to Swedish local time for display. The helper names visible in the screenshot — `_is_valid_flight` (the underscore means "internal function") and `_print_flight` — were reused verbatim, because recreating an app includes recreating its structure, not just its output.

### How the project was built

The work was done in a GenAI-assisted loop: one prompt produced one part of the project, each result was tested immediately, and any error was fed back to the AI together with the exact error text (the full prompt log is in the Appendix).

1. **Data first.** A generator produced `city_country.json` (62 countries, 193 cities, from an official city list — the same approach the original used) and `data/flights.json`: 124 flights (62 departures + 62 arrivals) across all 10 Swedavia airports in the API's field style, with 2 ghost entries on purpose so the filtering is visible. The route list starts with the exact evidence flight: `LH819`, Lufthansa, GOT → Frankfurt, T1, gate 15, 17:55 UTC, Departed.
2. **`destinationer.py`.** Loads `city_country.json` and builds a reverse index (city → country). `_lookup_country` resolves any spelling of a country or even a city name to the canonical country; `country_for_city` and `is_domestic` power the `D/I` flag; `filter_flights_by_country` filters a flight list; `available_countries` supports friendly errors.
3. **`airport.py`.** The menu app: `_is_valid_flight()` skips ghost entries, `_is_upcoming()` orders the board (upcoming first), `_print_flight()` prints each flight in the original format — including `Status: … Terminal: … Gate: …`, the `D/I` flag and `Sched: 17:55 UTC → 18:55 CET` with real `zoneinfo` conversion — and `_print_flights_paged()` pages boards longer than `PAGE_SIZE = 50`. The six menu options cover departures, arrivals, country filter, single-flight lookup, the airport list and exit.
4. **The optional live client.** `swedavia_client.py` calls the API v2 endpoints and normalizes the API's field names onto the shapes the board prints, so both data sources flow through the same code.

### Problems and solutions during implementation

- **Problem:** `TypeError: unhashable type: 'list'` when filtering by country — our first `_lookup_country` returned the *cities list* while the filter expected the *country name*.
  **Solution:** We redefined the function's contract: it now returns the canonical country name and even accepts a city name. A real example of how reverse-engineered guesses must be tested, not trusted.
- **Problem:** Windows does not ship the IANA timezone database, so `zoneinfo` raised `ZoneInfoNotFoundError` on a Windows computer.
  **Solution:** Added `requirements.txt` with the `tzdata` package and wrapped the timezone setup so the program prints the exact fix command instead of a stack trace.
- **Problem:** The output uses characters like `→` and Swedish letters (`å`, `ä`, `ö`) that can crash older Windows consoles.
  **Solution:** The program reconfigures its own standard output to UTF-8 with replacement at startup, so it never crashes on the character set.
- **Problem:** The API response wraps flights in a `"flights"` key and uses airport ids rather than city names.
  **Solution:** The client unpacks `payload.get("flights", [])` and normalizes each record; unknown destinations fall back to the airport id, documented as a known limitation of live mode.

---

## Phase 3: Completion of the Work (Finishing & Improvement)

### Finishing and testing the whole solution

Every mode was tested end to end: the default menu loop; departures and arrivals for each of the 10 airports (the GOT board shows 12 flights and filters its ghost entries with a counter); the country filter with lowercase `spain` (proving case-insensitivity) and with the city name `barcelona` (resolving to Spain); a single flight lookup (`lh819` returns precisely the record from the original screenshot, including T1, gate 15 and the 17:55 UTC → 18:55 CET conversion); an unknown country (friendly error listing all 62 countries); the `D/I` flag (Stockholm → Malmö correctly shows `D`, GOT → Frankfurt shows `I`); an invalid menu choice (polite re-ask instead of a crash); and `--api` without a key (clear instruction instead of a stack trace). The time conversion was verified against the original evidence: 17:55 UTC on 26 October 2026 becomes 18:55 CET — identical to the screenshot.

### Improvements and optimisation

- Ghost filtering prints how many entries were removed, so the behaviour is visible in the demo instead of silent.
- The country lookup accepts both countries and cities, which makes the filter more forgiving than a strict match.
- Boards are sorted so upcoming flights come first, with departed and landed flights grouped at the end.
- UTF-8 output reconfiguration and the `tzdata` dependency make the app run safely on Windows, macOS and Linux alike.
- The live-API path is isolated in its own module, so the app works offline out of the box and goes live later with one flag and one key.

### Publishing

The project is published on GitHub as the final deliverable, together with this documentation, the README, the code-explanation file (`FÖRKLARING.md`) and the video recording plan. The exact Git commands used are collected in the Appendix.

### Problems and solutions during completion

- **Problem:** We had to be sure the recreation matches the original, not just resembles it.
  **Solution:** We compared field by field against the screenshot evidence — flight id, airline formatting, status, terminal, gate and the two time zones all match exactly.
- **Problem:** Small formatting details (the arrow, the spacing, the `D/I` position) had to look right in every terminal.
  **Solution:** Tested the output side by side with the original and fixed the format strings one by one.

---

## Phase 4: Problems & Solutions (Summary)

| Problem | Solution |
|---------|----------|
| Real Swedavia API needs a subscription key | Bundled sample data mirroring the API fields + optional `swedavia_client.py` ready for a key |
| `TypeError: unhashable type: 'list'` in the country filter | Fixed the contract of `_lookup_country` to return the canonical country name; now also accepts city names |
| Windows lacks the IANA timezone database (`ZoneInfoNotFoundError`) | `requirements.txt` ships `tzdata`; the program prints the exact fix command if the database is missing |
| Sweden has two time zones across the year (CET/CEST) | `zoneinfo` with `Europe/Stockholm` converts correctly in both seasons |
| The API returns empty "ghost entries" | `_is_valid_flight` validates flight id, destination and schedule time before printing; the removal is counted |
| Special characters (`→`, `å`, `ä`, `ö`) can crash older Windows consoles | Standard output reconfigured to UTF-8 with replacement at startup |
| Case sensitivity in user input (`SPAIN` vs `spain`) | All lookups normalise with `.strip().lower()`, matching the original's behaviour |
| Unknown country would crash the filter | Friendly error message listing all available countries |

---

## Conclusion

**What we achieved:** a working Python command-line application that recreates the Swedavia flight board we were shown — a six-option menu, departures and arrivals for all 10 Swedavia airports, the exact evidence record for LH819, ghost-entry filtering, real UTC-to-Swedish-time conversion, a data-driven D/I flag, country filtering powered by `city_country.json`, paging for long boards, and an optional path to the live API. Working backwards from the output and the function names, we reconstructed not only what the app does but how it is structured.

**What we learned:** to treat every guess as a hypothesis to test (the country lookup failed on the first run and was fixed); to separate data from code (the city mapping lives in JSON, exactly like the original); to isolate external dependencies behind a small client; and that a reverse-engineered recreation must match the original's behaviour *and* its structure. We also learned how to drive generative AI productively: give it the evidence, demand one piece at a time, test everything immediately, and feed errors back with their exact text.

**What could be improved:** fetch live data once a key is available and cache responses so repeated runs are faster; add automatic tests for the conversion and filter functions; let the user page backwards; and extend `city_country.json` with more cities so live mode shows fewer IATA-code fallbacks.

---

## Video Recording Plan (minimum 4 minutes, in English)

| Time | What to show and say |
|------|----------------------|
| 0:00–0:30 | Present the mission: "I was shown a finished Python flight app for the Swedavia airports and had to recreate it using generative AI." Show the original screenshot next to your recreated output. |
| 0:30–1:30 | **Phase 1 — Research:** walk through the deductions — output format → data fields; function names → code structure; dual times → UTC-to-CET conversion; ghost entries → API filtering; the menu and D/I flag visible in the original. |
| 1:30–2:45 | **Phase 2 — Implementation:** open the project in the editor. Show `city_country.json` and `data/flights.json` (point out the ghost entries), `destinationer.py` (the case-insensitive lookup) and `airport.py` (`_is_valid_flight`, `_is_upcoming`, `_print_flight`, paging). Show a prompt-and-answer screenshot from the GenAI conversation. |
| 2:45–3:45 | **Demonstration:** run the menu in the terminal: departures for GOT (ghosts filtered, LH819 matches the original exactly), arrivals for ARN, option 3 with `spain` and `barcelona`, option 4 with `lh819`, option 5 for the airport list. |
| 3:45–4:30 | **Phases 3–4 — Problems & solutions:** the `TypeError` bug and the fix, the Windows timezone issue and `tzdata`, the API-key barrier and the sample-data decision. |
| 4:30–5:00 | **Conclusion:** what was achieved, what was learned, what could be improved. Show the GitHub repository with the pushed files. |

Recording tips: use OBS Studio, Loom or Windows Game Bar (Win + G), speak clearly and calmly, show concrete examples instead of only talking, and plan what to say before recording.

---

## Appendix A: GenAI Prompt Log — the recreation workflow

The assignment required recreating the app **using generative AI**. This log documents the prompt sequence in the correct order — each prompt produced one part, and each result was tested before moving on.

| # | Step | Prompt given to the AI | Result / action taken |
|---|------|------------------------|----------------------|
| 1 | Analyse the evidence | "I'm recreating a Python CLI flight app for the Swedavia airports by reverse engineering it. The original prints this: [LH819 block]. It has `_is_valid_flight`, `_print_flight`, `_is_upcoming`, paging, `destinationer.py` with `_lookup_country` and `city_country.json`. Do NOT write code yet — analyse what data fields and functions the app must have." | A field list and a function plan — saved as the blueprint. Screenshot taken for the video. |
| 2 | Data layer | "Generate `city_country.json` (country → cities from an official list) and `data/flights.json`: departures and arrivals for the 10 Swedavia airports in Swedavia API field style, including LH819 → Frankfurt (T1, gate 15, 17:55 UTC), plus ghost entries on purpose." | The data files were created and inspected — the ghost entries and the evidence record verified first. |
| 3 | Country module | "Generate `destinationer.py` with `_lookup_country` (case-insensitive, accepts country OR city), `country_for_city`, `is_domestic`, `filter_flights_by_country`, `available_countries`, loading `city_country.json`." | Tested with `spain`, `barcelona` and an unknown name before continuing. |
| 4 | Main program | "Generate `airport.py`: a 6-option menu, `_is_valid_flight`, `_is_upcoming`, `_print_flight` in the original format with the D/I flag and `Sched: HH:MM UTC → HH:MM CET`, `_print_flights_paged` with `PAGE_SIZE = 50`, `--api` flag, friendly errors." | Every menu option was run and compared with the original evidence. |
| 5 | Debug with the AI | Whenever a run failed, the exact error text was pasted back: "I get this error when running: [error]. Explain why and give the fixed code." | Examples: the `TypeError` in the country filter; the Windows `ZoneInfoNotFoundError` fixed by `pip install tzdata`. |
| 6 | Docs & review | "Write the README and the documentation following the four-phase assignment guide; review for anything unclear or exaggerated." | README.md, FÖRKLARING.md and this document were produced and corrected. |

**What this shows:** the GenAI never ran untested — every generated piece was run, compared with the original evidence, and (when wrong) fed back as an error report. The human provided the evidence, the verification and the decisions; the GenAI provided the code, explanations and structure. That combination is what "recreate an app with GenAI" means in practice.

## Appendix B: GitHub publishing (commands used)

```bash
git init
git add .
git commit -m "Recreate Swedavia flight board app (Python CLI) with GenAI"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

Later updates: `git add .` → `git commit -m "Describe the change"` → `git push`.
If "Permission denied": check that you are logged in with the right account (or that the access token in the URL is valid). If the branch is wrong: `git branch -M main`. If changes are not visible on GitHub: do not forget `git push`.
