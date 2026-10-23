"""Ambient Weather REST API (https://ambientweather.docs.apiary.io)."""
import json
import time
import urllib.parse
import urllib.request

BASE_URL = "https://rt.ambientweather.net/v1"


class Client:
    def __init__(self, api_key, app_key):
        self.keys = {"apiKey": api_key.strip(), "applicationKey": app_key.strip()}

    def _get(self, path, **params):
        url = f"{BASE_URL}{path}?" + urllib.parse.urlencode({**self.keys, **params})
        req = urllib.request.Request(url, headers={"User-Agent": "solar-dashboard"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    def devices(self):
        return self._get("/devices")

    def history(self, mac, limit=288):
        """Newest-first readings (5-minute steps), each with dateutc in ms."""
        time.sleep(1.1)  # the API allows one request per second per key
        return self._get(f"/devices/{urllib.parse.quote(mac)}", limit=limit)
