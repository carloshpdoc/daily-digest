#!/usr/bin/env python3
"""Test Google Calendar integration directly"""

import datetime as dt
import os
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from icalendar import Calendar

load_dotenv()


def test_calendar():
    ics_url = os.getenv("GCAL_ICS_URL")
    print(f"Testing calendar URL: {ics_url}")

    # Fetch calendar data
    resp = requests.get(ics_url, timeout=30, allow_redirects=True)
    print(
        f"Response: {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}"
    )

    if not resp.ok:
        print(f"❌ Failed to fetch calendar: {resp.text[:200]}")
        return

    # Improved sanitization with line folding support
    def sanitize_ics(raw: bytes) -> bytes:
        txt = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        unfolded_lines = []
        current_line = b""

        for line in txt.split(b"\n"):
            if line.startswith(b" ") or line.startswith(b"\t"):
                current_line += line[1:]
            else:
                if current_line:
                    unfolded_lines.append(current_line)
                current_line = line

        if current_line:
            unfolded_lines.append(current_line)

        sanitized_lines = []
        for line in unfolded_lines:
            if not line.strip():
                continue
            if b":" in line:
                prop = line.split(b":", 1)[0].strip()
                if prop.isdigit():
                    continue
            sanitized_lines.append(line)

        return b"\n".join(sanitized_lines)

    try:
        sanitized = sanitize_ics(resp.content)
        cal = Calendar.from_ical(sanitized)
        print("✅ Calendar parsing successful!")

        # Test for multiple dates
        TZ = ZoneInfo(os.getenv("TIMEZONE", "America/Sao_Paulo"))

        # Test dates
        test_dates = [
            dt.date(2025, 9, 19),  # Target date
            dt.date(2025, 9, 21),  # Today
        ]

        all_events = []
        total_events = 0

        for comp in cal.walk("vevent"):
            total_events += 1
            title = str(comp.get("summary") or "(sem título)")
            ds = comp.get("dtstart")
            de = comp.get("dtend")

            if not ds:
                continue

            # Normalize datetime
            s1 = ds.dt
            if isinstance(s1, dt.date) and not isinstance(s1, dt.datetime):
                s1 = dt.datetime.combine(s1, dt.time.min).replace(tzinfo=TZ)
            elif isinstance(s1, dt.datetime):
                if s1.tzinfo is None:
                    s1 = s1.replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
                else:
                    s1 = s1.astimezone(TZ)

            e1 = None
            if de:
                e1 = de.dt
                if isinstance(e1, dt.date) and not isinstance(e1, dt.datetime):
                    e1 = dt.datetime.combine(e1, dt.time.min).replace(tzinfo=TZ)
                elif isinstance(e1, dt.datetime):
                    if e1.tzinfo is None:
                        e1 = e1.replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
                    else:
                        e1 = e1.astimezone(TZ)
            else:
                e1 = s1 + dt.timedelta(hours=1) if s1 else None

            all_events.append(
                {
                    "title": title,
                    "start": s1.isoformat() if s1 else None,
                    "end": e1.isoformat() if e1 else None,
                    "start_dt": s1,
                    "end_dt": e1,
                }
            )

        print(f"Total events in calendar: {total_events}")

        # Check each test date
        for test_date in test_dates:
            START = dt.datetime.combine(test_date, dt.time.min).replace(tzinfo=TZ)
            END = dt.datetime.combine(test_date, dt.time.max).replace(tzinfo=TZ)

            events_on_date = []
            for event in all_events:
                s1, e1 = event["start_dt"], event["end_dt"]
                if s1 and e1 and s1 <= END and e1 >= START:
                    events_on_date.append(event)

            print(f"\nEvents on {test_date}: {len(events_on_date)}")
            for event in events_on_date:
                print(f"  - {event['title']} ({event['start']} → {event['end']})")

        # Show some recent events for context
        recent_events = sorted(
            [e for e in all_events if e["start_dt"]],
            key=lambda x: x["start_dt"],
            reverse=True,
        )[:10]
        print("\nMost recent 10 events:")
        for event in recent_events:
            date_str = (
                event["start_dt"].strftime("%Y-%m-%d")
                if event["start_dt"]
                else "unknown"
            )
            print(f"  - {date_str}: {event['title']}")

        return all_events

    except Exception as e:
        print(f"❌ Calendar parsing failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    test_calendar()
