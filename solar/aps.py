"""Minimal APsystems OpenAPI client (standard library only).

Signing follows the APsystems OpenAPI user manual v1.8: the string
Timestamp/Nonce/AppId/RequestPath/HTTPMethod/SignatureMethod is HMAC-SHA256'd
with the app secret, where RequestPath is the last segment of the URL path.
"""
import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
import uuid

BASE_URL = "https://api.apsystemsema.com:9282"
PREFIX = "/user/api/v2/systems"

RATE_LIMIT_CODES = {2005, 7001, 7002, 7003}
MESSAGES = {
    1000: "data exception", 1001: "no data",
    2001: "invalid App ID", 2002: "app not authorized", 2003: "app authorization expired",
    2004: "app has no permission for this data", 2005: "monthly call limit reached",
    4000: "bad request", 4001: "bad request (check the System ID)",
    5000: "APsystems server error", 7001: "server access limit", 7002: "too many requests",
    7003: "APsystems is busy",
}


class APSError(Exception):
    def __init__(self, code, path):
        self.code = code
        super().__init__(f"APsystems {path}: code {code} ({MESSAGES.get(code, 'unknown')})")


class Client:
    def __init__(self, app_id, app_secret, on_call=None):
        self.app_id = app_id.strip()
        self.secret = app_secret.strip()
        self.on_call = on_call  # counts calls against the monthly budget

    def _headers(self, path):
        ts = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        last = path.rstrip("/").rsplit("/", 1)[-1]
        to_sign = "/".join((ts, nonce, self.app_id, last, "GET", "HmacSHA256"))
        sig = hmac.new(self.secret.encode(), to_sign.encode(), hashlib.sha256).digest()
        return {
            "X-CA-AppId": self.app_id,
            "X-CA-Timestamp": ts,
            "X-CA-Nonce": nonce,
            "X-CA-Signature-Method": "HmacSHA256",
            "X-CA-Signature": base64.b64encode(sig).decode(),
        }

    def get(self, path, params=None):
        path = PREFIX + path
        url = BASE_URL + path + ("?" + urllib.parse.urlencode(params) if params else "")
        if self.on_call:
            self.on_call(path)
        req = urllib.request.Request(url, headers=self._headers(path))
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = json.load(resp)
        code = int(body.get("code", -1))
        if code != 0:
            raise APSError(code, path)
        return body.get("data")

    def details(self, sid):
        return self.get(f"/details/{sid}")

    def inverters(self, sid):
        return self.get(f"/inverters/{sid}")

    def summary(self, sid):
        return self.get(f"/summary/{sid}")

    def energy(self, sid, level, date_range=None):
        params = {"energy_level": level}
        if date_range:
            params["date_range"] = date_range
        return self.get(f"/energy/{sid}", params)

    def batch_power(self, sid, eid, date):
        """Every panel's power for one day: {time: [...], power: {"uid-ch": [...]}}."""
        return self.get(f"/{sid}/devices/inverter/batch/energy/{eid}",
                        {"energy_level": "power", "date_range": date})

    def meter_period(self, sid, eid, level, date_range=None):
        params = {"energy_level": level}
        if date_range:
            params["date_range"] = date_range
        return self.get(f"/{sid}/devices/meter/period/{eid}", params)
