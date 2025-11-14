"""
Test for the Email Microservice.

Usage:
  python test_email.py --mode instant   --to you@example.com
  python test_email.py --mode scheduled --to you@example.com --minutes 2

This script pings the service, sends an instant or scheduled email,
and displays the response.
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
import requests

# Update this if your service runs on a different port
BASE_URL = "http://127.0.0.1:5002"

def pretty(obj):
    """Return JSON format string"""
    return json.dumps(obj, indent=2, ensure_ascii=True)

def send_instant(to_email: str):
    """Send an instant email request via POST /send-email."""
    payload = {
        "recipients": [to_email],
        "subject_line": "Email Microservice - Instant Test",
        "body": (
            "<!doctype html><html><body>"
            "<h2 style='margin:0'> Instant Email Test</h2>"
            "<p>This email was sent immediately by the Email Microservice.</p>"
            "</body></html>"
        ),
        "is_html": True
    }
    r = requests.post(f"{BASE_URL}/send-email", json=payload, timeout=10)
    print(f"[instant] HTTP {r.status_code}")
    try:
        print(pretty(r.json()))
    except Exception:
        print(r.text)

def send_scheduled(to_email: str, minutes_from_now: int):
    """Schedule an email using POST /send-timed-email and check its status."""
    
    # Calculate future time in UTC
    now_utc = datetime.now(timezone.utc)
    
    # Check scheduled time is at the start of a minute
    if now_utc.second > 0 or now_utc.microsecond > 0:
        now_utc = now_utc.replace(second=0, microsecond=0) + timedelta(minutes=1)
    
    future_utc = now_utc + timedelta(minutes=max(minutes_from_now, 3))

    payload = {
        "recipients": [to_email],
        "subject_line": "Email Microservice - Scheduled Test",
        "body": (
            "<!doctype html><html><body>"
            "<h2 style='margin:0'> Scheduled Email Test</h2>"
            f"<p>Scheduled for: <b>{future_utc.strftime('%Y-%m-%d %H:%M')} UTC</b></p>"
            "</body></html>"
        ),
        "is_html": True,
        "date_to_send": future_utc.strftime("%Y-%m-%d"),
        "time_to_send": future_utc.strftime("%H:%M")
    }
    
    r = requests.post(f"{BASE_URL}/send-timed-email", json=payload, timeout=10)
    print(f"[scheduled] HTTP {r.status_code}")
    print(pretty(r.json() if r.headers.get("Content-Type","").startswith("application/json") else r.text))

    # Check schedule status using the returned ID
    try:
        resp = r.json()
        print(pretty(resp))
        schedule_id = resp.get("details", {}).get("schedule_id")
        if schedule_id:
            check = requests.get(f"{BASE_URL}/check-scheduled-email/{schedule_id}", timeout=10)
            print("\n[status check]")
            print(pretty(check.json()))
    except Exception:
        print(r.text)

def ping() -> bool:
    """Check if the microservice is running via GET /ping."""
    try:
        r = requests.get(f"{BASE_URL}/ping", timeout=5)
        ok = (r.status_code == 200)
        print(f"[ping] {r.status_code} {r.text}")
        return ok
    except Exception as e:
        print(f"[ping] failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["instant", "scheduled"], required=True)
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--minutes", type=int, default=2, help="Delay time for scheduled send")
    args = parser.parse_args()

    if not ping():
        print("Connection error. Please start the server at (http://127.0.0.1:5002/ping).")
        raise SystemExit(1)

    if args.mode == "instant":
        send_instant(args.to)
    else:
        send_scheduled(args.to, args.minutes)
