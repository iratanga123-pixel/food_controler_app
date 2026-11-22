"""SMS alerts to storage managers.

By default messages are written to data/sms_outbox.log (simulated SMS).
To send through the free Africa's Talking sandbox instead, set two environment variables:
    $env:AT_USERNAME = "sandbox"
    $env:AT_API_KEY  = "<your sandbox API key>"
Messages then appear in the sandbox phone simulator on the Africa's Talking website.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime

from config import CROPS, DATA_DIR, SMS_OUTBOX

STATE_FILE = DATA_DIR / "alert_state.json"   # last level we alerted for each store


def compose(p: dict) -> str:
    s, f, c = p["store"], p["features"], CROPS[p["store"]["crop"]]
    d = p["drivers"]
    if d["moisture"] >= max(d["humidity"], d["temperature"]):
        cause, action = f"grain moisture {f['grain_moisture']:.1f}% (safe <= {c['m_safe']}%)", f"Dry the grain below {c['m_safe']}%."
    elif d["humidity"] >= d["temperature"]:
        cause, action = f"air humidity {f['humidity']:.0f}% (keep < 70%)", "Ventilate on dry hours, keep bags on pallets."
    else:
        cause, action = f"grain temperature {f['grain_temp']:.1f}C", "Shade the store, ventilate at night, check for insects."
    tag = "URGENT" if p["level"] == 2 else "WARNING"
    en = f"SFLP {tag}: {s['name']}, {cause}. Spoilage risk in next 3 days. {action} Reply 1 when checked."
    rw = (f"IBURIRA: Ububiko bwa {s['district']}, ubuhehere bw'{c['rw']} ni {f['grain_moisture']:.1f}%. "
          f"Mwanike neza kugeza munsi ya {c['m_safe']}%.")
    return en + "\n" + rw


def send_sms(phone: str, text: str) -> str:
    user, key = os.getenv("AT_USERNAME"), os.getenv("AT_API_KEY")
    if user and key:
        host = "api.sandbox.africastalking.com" if user == "sandbox" else "api.africastalking.com"
        data = urllib.parse.urlencode({"username": user, "to": phone, "message": text}).encode()
        req = urllib.request.Request(f"https://{host}/version1/messaging", data=data,
                                     headers={"apiKey": key, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return "Africa's Talking: " + r.read().decode()[:120]
    with open(SMS_OUTBOX, "a", encoding="utf-8") as fh:
        fh.write(f"--- {datetime.now():%Y-%m-%d %H:%M:%S}  to {phone}\n{text}\n")
    return f"saved to {SMS_OUTBOX.name}"


def check_and_send(preds: list[dict]) -> list[str]:
    """Send an alert when a store's risk level goes up; send an all-clear when it returns to Good."""
    return [a["line"] for a in check_and_alert(preds)]


def check_and_alert(preds: list[dict]) -> list[dict]:
    """Like check_and_send, but returns the details of each alert (used for desktop notifications)."""
    try:
        state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    except (ValueError, OSError):
        state = {}
    sent = []
    for p in preds:
        sid, prev = p["store"]["id"], state.get(p["store"]["id"], 0)
        if p["level"] > prev:
            text = compose(p)
        elif p["level"] == 0 and prev > 0:
            text = f"SFLP: {p['store']['name']} is back to safe conditions. Keep weekly checks."
        else:
            state[sid] = p["level"]
            continue
        result = send_sms(p["store"]["phone"], text)
        sent.append({"id": f"{sid}-{datetime.now():%Y%m%d%H%M%S%f}", "store": p["store"]["name"],
                     "level": p["level"], "level_name": p["level_name"], "text": text,
                     "line": f"{p['store']['name']} ({p['level_name']}): {result}"})
        state[sid] = p["level"]
    STATE_FILE.write_text(json.dumps(state))
    return sent
