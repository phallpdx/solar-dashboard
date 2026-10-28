# Nightly list refresh with the local model

`refresh_lists.py` updates the dashboard's researched lists using the model in
LM Studio on Parker's desktop PC instead of Claude routines. It runs every night at
12:05 am, just after the site's own midnight rollover, and again at 2:05 and
4:05 am. The later runs reuse answers for unchanged pages, so they take a few
minutes and retry anything that failed earlier.

Lists it handles: jazz, concerts, events (big events), kids (family outings),
bluray, foodfinds, skioutlook, teams (fan pulse), coast, restaurants, localmusic and marketbrief (the morning
market analysis, North American Helium and Portland real estate, written from
news feeds and closing prices).

Every run also writes `web/localstatus.json`, saying which lists it changed
tonight. The Claude runs in the cloud read it each morning and skip whatever
this PC already refreshed, so they only do the full job when the PC was
off or a list failed. For planahead it only drops
past items: venue pages don't show on-sale dates, so finding new ones stays with
Claude.

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

If the model or a source fails, that list simply keeps yesterday's items.
Logs are in `local\logs\` (kept 30 days).

Concerts work a little differently: the model reads venue calendars and, when
an artist on the "missing" list gets a Portland date, moves them to "shows".
Finding newly acclaimed albums is still a job for Claude.

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
