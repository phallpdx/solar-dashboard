# Nightly list refresh with the local model

`refresh_lists.py` updates the dashboard's researched lists using the model in
LM Studio on Parker's desktop PC instead of Claude routines. It runs every night at
12:05 am, just after the site's own midnight rollover, and again at 2:05 and
4:05 am. The later runs reuse answers for unchanged pages, so they take a few
minutes and retry anything that failed earlier.

Lists it handles: jazz, concerts, events (big events), kids (family outings),
bluray, foodfinds, planahead, skioutlook, teams (fan pulse), coast, restaurants, localmusic, liquor and marketbrief (the morning
market analysis, North American Helium and Portland real estate, written from
news feeds and closing prices).

Every run also writes `web/localstatus.json`, saying which lists it changed
tonight. The Claude runs in the cloud read it each morning and skip whatever
this PC already refreshed, so they only do the full job when the PC was
off or a list failed. Planahead reads on-sale news (the Portland Mercury's weekly
Ticket Alert and on-sale headlines), but the cloud run still researches it every
morning, since venue pages don't show on-sale dates.

Liquor works without reading pages: OLCC posts this month's and next month's
price lists as CSV files, and any item code in next month's list that isn't in
this month's is new in Oregon. The model only names the category and writes a
plain description. It never rates bottles, so rating stays empty; the cloud
roundup can add critic scores. OLCC doesn't publish per-store stock, so these are
new in Oregon, not confirmed on the St. Johns shelf.

## What a run does

1. Pulls the latest script from GitHub, then starts LM Studio's server and loads
   the model, unless they are already running.
2. For each list, fetches the pages and feeds in `sources.json`, asks the model
   to pull out items as JSON, and checks them: dates must be real and upcoming,
   links must appear on the page and still load, and duplicates are dropped.
3. Merges the new items into the current list from `main`, drops past items and
   pushes the changed files to the `claude/local-lists` branch. The "Publish
   researched lists" workflow then copies them onto `main`. Your working folder
   is never touched.
4. Unloads the model and stops the server if it started them.

Every answer gets a second look: the model checks its draft against the same
page, drops what the page doesn't support and fixes wrong names, dates and
links (turn it off with `"review": false` under `lmstudio` in `sources.json`).
Only changed pages are asked, so this roughly doubles model time for those.

If the model or a source fails, that list simply keeps yesterday's items.
Logs are in `local\logs\` (kept 30 days).

## Flips

`flips` looks for anything on Portland Craigslist (the categories under
`lists.flips` in `sources.json`) that Parker could resell for $150+ after
about 15% in fees, paying $50+ an hour counting the pickup drive and selling
time. Gemma screens each new listing once for a known brand and model priced
well under resale. Its guesses only choose what to check: they wait in a queue
in `flips.json`, and the best few a run (`flips.verify_per_run`, 10) are priced
from a web search of used and sold prices. A price only counts if the result
it cites shows that dollar figure. Guesses not checked tonight stay queued for
the next run (up to 10 days, while the listing is up), so a busy night's finds
aren't lost.

## Web search through Open WebUI

A source in `sources.json` can be a web search instead of a page:
`{"name": "Web search: Portland presales", "search": "Portland Oregon concert presale ..."}`.
The script sends it to Open WebUI on this PC (`http://localhost:3000`, the
`open-webui` Docker container), which runs it on its configured search engine
(Tavily) and returns the top results. The model then reads the result titles
and snippets like a feed, and items must link one of the results. Plan ahead,
big events, and the market brief's helium and real estate sections each have one.
A source with `"days": ["Mon", "Thu"]` only runs on those weekdays; that's how
the weekly deep passes the cloud runs used to do (jazz Monday, food finds
Tuesday, family outings and Blu-ray Thursday, the roundup lists Saturday) are
spread over the week. Concerts searches for Metacritic-scored albums on Monday
and Thursday (a score is kept only if it appears in the result it links), and
the real estate section now fills its own "stats" figures the same way.
`web/localstatus.json` says whether tonight's searches worked (`web_search`).

Searches cost search credits, so each query runs once a day (the 2:05 and
4:05 runs reuse the 12:05 results from `local\cache\searches.json`) and a day
stops at `openwebui.max_searches_per_day` (12). The nightly job starts Docker
and the container if they aren't running and stops them again afterwards.

It needs an Open WebUI API key, saved once with
`powershell -ExecutionPolicy Bypass -File local\set_openwebui_key.ps1`
(encrypted for your Windows account in `local\openwebui_key.dat`, never
committed). Without it, search sources are skipped and everything else runs
as before. To try a query by hand: `py local\refresh_lists.py --search "query"`.

Concerts work a little differently: the model reads venue calendars and, when
an artist on the "missing" list gets a Portland date, moves them to "shows".
It also reads Pitchfork's Best New Albums feed and adds those artists to
"missing" with no score (the feed has none) and score_source "Pitchfork Best New Music".
The cloud run still adds Metacritic-scored albums twice a week.

## One-time setup (Windows)

1. Install Git and Python, and get the code (PowerShell):

   ```powershell
   winget install --id Git.Git -e
   winget install --id Python.Python.3.12 -e
   ```

   Close and reopen PowerShell, then:

   ```powershell
   git clone https://github.com/phallpdx/solar-dashboard $HOME\solar-dashboard
   cd $HOME\solar-dashboard
   ```

2. In LM Studio, turn Gemma's thinking off: open the model's settings
   (My Models, then the gear next to Gemma 4) and switch off thinking or
   reasoning if it is listed. The script also asks for thinking off on every
   request, but the setting makes sure.
3. Run the setup script. It checks everything, signs in to GitHub once and
   registers the nightly task:

   ```powershell
   powershell -ExecutionPolicy Bypass -File local\setup.ps1 -RunNow
   ```

   `-RunNow` also starts a first run so you can check `local\logs\` right away.
4. Keep the PC on and signed in (locking it is fine). The task can
   wake the PC from sleep if wake timers are allowed in your power plan.

## Handy commands

```powershell
py local\refresh_lists.py --check-sources       # which sources still load and have text
py local\refresh_lists.py --only jazz --dry-run # try one list, write to local\out\
powershell -ExecutionPolicy Bypass -File local\setup.ps1 -At 01:00,03:00   # change the times
powershell -ExecutionPolicy Bypass -File local\setup.ps1 -Uninstall  # remove the task
```

To change where a list looks, edit `sources.json`. Pages that build their
calendar with JavaScript show up as "almost no text" in `--check-sources`;
swap those for an RSS feed or a plainer page.
