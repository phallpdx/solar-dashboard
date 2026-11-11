# Solar dashboard

A home energy dashboard that combines APsystems (EMA) solar data, an Ambient
Weather station and PGE Green Button downloads.

- `solar/update.py` fetches everything and writes `dashboard.json`. It runs
  hourly from GitHub Actions and spends roughly 20 APsystems calls a day
  (about 620 a month), with a hard stop at 850 a month.
- `web/index.html` is the dashboard page. It reads `dashboard.json` and falls
  back to `sample.json` until real data exists.
- Cached API responses, call counts and PGE CSVs live on the `data` branch.
  Personal details (name, address, account number) are stripped from PGE
  files before they are saved.

## Settings

Repository secrets: `APSYSTEMS_APP_ID`, `APSYSTEMS_APP_SECRET`,
`APSYSTEMS_SID`, and optionally `AMBIENT_API_KEY` and `AMBIENT_APP_KEY`.
Optional `CALENDAR_ICS`: your Google Calendar's "Secret address in iCal format"
(one per line for several calendars). Event titles and places then appear on the dashboard.
Elections and representatives work without keys. Optional free keys add more:
`CONGRESS_KEY` (api.data.gov, bills your members of Congress sponsor), `OPENSTATES_KEY`
(openstates.org, your state legislators and their bills) and `GOOGLE_CIVIC_KEY` (a Google Cloud key
with the Civic Information API turned on, for what's on your ballot).
With an `AISSTREAM_KEY`, the river section shows the ship parked across from `river_view` in `config.json`
(a ship stopped within `parked_km`, default 1 km). The river itself needs no key: USGS gauges, the NWS river
forecast, marine warnings for the Columbia River bar and the coast surf-zone forecast.
`roof` in `config.json` (panel tilt and azimuth) feeds the irradiance-on-the-roof forecast (Open-Meteo) and the
long-term yield comparison (PVGIS); the system size comes from APsystems unless `kwp` is set there.
Also keyless: 7Timer's night-sky forecast, NOAA's half-hour aurora model, Tiangong and Hubble passes (CelesTrak),
asteroid close approaches (NASA JPL), NOAA's daily sunspot and flare counts with the SDO image, the Open-Meteo
smoke (PM2.5) outlook, Portland State and Portland Pilots basketball (ESPN), and one free archive item a day each
from the Art Institute of Chicago, the Library of Congress and the Internet Archive's Live Music Archive.
Optional `TMDB_API_KEY` (free for non-commercial use from themoviedb.org/settings/api; either the API key or the
API Read Access Token works) adds the best-rated new movies on your streaming services, movies coming to them in the next week, and a daily kids' movie pick
that fits the season and never repeats, and a daily classic movie (25+ years old, widely loved) that never repeats either. New shows and their TVmaze ratings work without a key.
Optional repository variable `PGE_CYCLE_START_DAY` (the day of the month your
PGE bill cycle starts).

## Run locally

```sh
export APSYSTEMS_APP_ID=... APSYSTEMS_APP_SECRET=... APSYSTEMS_SID=...
python -m solar.update          # writes data/dashboard.json
cp data/dashboard.json web/ && python -m http.server -d web 8000
```

## Kindle edition

Each site build also renders the full dashboard once in headless Chromium and
saves "The Morning Edition" in `kindle/`: a contents page (with "Today at a
glance") and one page per section, laid out for a black-and-white e-reader.
It is made by `solar/kindle_full.py`:

- The dashboard loads with `?kindle`, which shows whole lists instead of the
  top few (top items still first), and every "N more" / "Show all" is opened.
- An editorial pass drops controls and status text that only make sense on
  the live page, leads Today with the weather and calendar, gives Money its
  own section, gathers source lines at the foot of each section and tidies
  dates and times.
- The styling is one serif (Literata, saved alongside the pages), small-caps
  labels and hairline rules, with every colour turned into black, white or
  one of two greys, and no text reversed out of a dark block.
- Tap the right side of the Kindle screen to turn a screen forward (it stops
  at the last whole line), the left side to go back.

`kindle.html` redirects there, so bookmark `<your Pages URL>/kindle.html`.
If the step fails, `kindle.html` stays the simple text-only morning page.
