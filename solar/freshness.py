"""Save what each dashboard section shows today, so the page can sort its sections by what's new.

    python -m solar.freshness _site data/freshness.json

Opens the built site in headless Chromium, waits for every list to load, and asks the page for its section
"prints" (window.sectionSnapshot() in web/index.html: short hashes of each headline, link and list row, with numbers
taken out). Today's prints replace any saved earlier today; the last eight days are kept in the history file
(on the data branch) and copied to the site as freshness.json, which every device reads to sort alike.
"""
import functools
import http.server
import json
import os
import sys
import threading
from pathlib import Path

KEEP_DAYS = 8
TZ = "America/Los_Angeles"


def snapshot(site):
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(site))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            if os.environ.get("CHROME_PATH"):
                browser = p.chromium.launch(executable_path=os.environ["CHROME_PATH"])
            else:
                try:  # GitHub's runners already have Chrome; fall back to Playwright's own Chromium
                    browser = p.chromium.launch(channel="chrome")
                except Exception:  # noqa: BLE001
                    browser = p.chromium.launch()
            page = browser.new_context(timezone_id=TZ, viewport={"width": 1200, "height": 900}).new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}/index.html", wait_until="load", timeout=60000)
            page.wait_for_function("window.__printsReady === true", timeout=60000)
            got = page.evaluate("window.sectionSnapshot()")
            browser.close()
            return got
    finally:
        server.shutdown()


def merge(history, got):
    day, sections = got["day"], history.setdefault("sections", {})
    for sec, prints in got["prints"].items():
        sections.setdefault(sec, {})[day] = prints
    days = sorted({d for s in sections.values() for d in s})[-KEEP_DAYS:]
    for sec in list(sections):
        sections[sec] = {d: v for d, v in sections[sec].items() if d in days}
    history["updated"] = day
    return history


def main():
    site, hist_path = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        history = json.loads(hist_path.read_text())
    except (OSError, ValueError):
        history = {}
    history = merge(history, snapshot(site))
    text = json.dumps(history, separators=(",", ":"))
    hist_path.write_text(text)
    (site / "freshness.json").write_text(text)
    print(f"freshness: {len(history['sections'])} sections, days {sorted({d for s in history['sections'].values() for d in s})}")


if __name__ == "__main__":
    main()
