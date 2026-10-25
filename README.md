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
Optional repository variable `PGE_CYCLE_START_DAY` (the day of the month your
PGE bill cycle starts).

## Run locally

```sh
export APSYSTEMS_APP_ID=... APSYSTEMS_APP_SECRET=... APSYSTEMS_SID=...
python -m solar.update          # writes data/dashboard.json
cp data/dashboard.json web/ && python -m http.server -d web 8000
```
