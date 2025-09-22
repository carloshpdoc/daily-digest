#!/usr/bin/env python3
"""Test enhanced huddle detection with simulated Slack data"""

import datetime as dt
import re
from zoneinfo import ZoneInfo


# Simulated Slack message data that would represent a huddle with Yago Castro on Sept 19th
def simulate_yago_huddle_messages():
    """Simulate the type of messages Slack would generate for a huddle session"""

    # Messages that Slack typically generates for huddles
    simulated_messages = [
        {
            "text": "Yago Castro joined the huddle",
            "ts": "1726761600.123456",  # Sept 19, 2025 14:00 (approximate)
            "subtype": "huddle_thread",
            "user": "U1234567890",  # Yago's user ID
        },
        {
            "text": "Carlos joined the huddle",
            "ts": "1726761610.123456",  # Sept 19, 2025 14:00:10
            "subtype": "huddle_thread",
            "user": "U0987654321",  # Carlos's user ID
        },
        {
            "text": "Huddle ended",
            "ts": "1726763400.123456",  # Sept 19, 2025 14:30 (30 min later)
            "subtype": "huddle_thread",
            "user": "U1234567890",
        },
    ]

    return simulated_messages


def test_huddle_detection():
    """Test our enhanced huddle detection patterns"""

    TZ = ZoneInfo("America/Sao_Paulo")

    # Enhanced huddle detection patterns (same as in main script)
    huddle_patterns = re.compile(
        "|".join(
            [
                r"\biniciou um huddle\b",
                r"\bhuddle iniciado\b",
                r"\bstarted a huddle\b",
                r"\bjoined the huddle\b",
                r"\bhuddle ended\b",
                r"\bentrou no huddle\b",
                r"\bsaiu do huddle\b",
                r"\bleft the huddle\b",
            ]
        ),
        re.IGNORECASE,
    )

    messages = simulate_yago_huddle_messages()
    huddle_events = []

    print("Testing huddle detection patterns...")
    print("=" * 50)

    for msg in messages:
        msg_text = msg.get("text", "")
        msg_subtype = msg.get("subtype", "")
        msg_ts = float(msg.get("ts", 0))

        # Check if this is a huddle-related message (same logic as main script)
        is_huddle = (
            "huddle" in msg_subtype.lower()
            or huddle_patterns.search(msg_text)
            or "huddle" in msg_text.lower()
        )

        if is_huddle:
            # Convert timestamp to readable format
            msg_time = dt.datetime.fromtimestamp(msg_ts, tz=TZ)

            print(f"✅ DETECTED: {msg_text}")
            print(f"   Time: {msg_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Subtype: {msg_subtype}")
            print()

            # Determine action
            action = (
                "joined"
                if any(
                    word in msg_text.lower()
                    for word in ["joined", "iniciou", "started", "entrou"]
                )
                else (
                    "ended"
                    if any(
                        word in msg_text.lower() for word in ["ended", "left", "saiu"]
                    )
                    else "activity"
                )
            )

            huddle_events.append(
                {
                    "time": msg_time,
                    "text": msg_text,
                    "participant": (
                        "teammate" if "Yago" in msg_text else "carlos.henrique"
                    ),
                    "action": action,
                    "timestamp": msg_ts,
                }
            )
        else:
            print(f"❌ IGNORED: {msg_text}")
            print()

    print("Summary of detected huddle events:")
    print("=" * 50)

    # Group by participant (same logic as main script)
    by_participant = {}
    for event in huddle_events:
        participant = event["participant"]
        if participant not in by_participant:
            by_participant[participant] = []
        by_participant[participant].append(event)

    for participant, events in by_participant.items():
        print(f"\n🗣️ **{participant}:**")
        for event in events:
            action_emoji = (
                "🔗"
                if event["action"] == "joined"
                else "🔚" if event["action"] == "ended" else "💬"
            )
            print(
                f"  - {event['time'].strftime('%H:%M')} - {action_emoji} {event['action']} huddle"
            )
            print(f'    💭 "{event["text"]}"')

    return huddle_events


if __name__ == "__main__":
    events = test_huddle_detection()
    print(f"\n🎯 Total huddle events detected: {len(events)}")

    # Check if we detected the specific Yago Castro huddle
    yago_events = [e for e in events if "yago" in e["participant"]]
    if yago_events:
        print("✅ Successfully detected huddle with Yago Castro!")
        print(f"   Events: {len(yago_events)}")
        for event in yago_events:
            print(
                f"   - {event['time'].strftime('%H:%M')} {event['action']}: {event['text']}"
            )
    else:
        print("❌ Did not detect Yago Castro huddle")
