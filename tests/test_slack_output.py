#!/usr/bin/env python3
"""Test enhanced Slack huddle output format"""


def h2(t):
    return f"\n{t}\n" + "—" * len(t) + "\n"


# Simulated enhanced huddle data
huddle_sessions = [
    {
        "participant": "barbara.ramos",
        "time": "10:30",
        "action": "joined",
        "text": "Barbara joined the huddle",
    },
    {
        "participant": "barbara.ramos",
        "time": "11:15",
        "action": "ended",
        "text": "Barbara left the huddle",
    },
    {
        "participant": "john.doe",
        "time": "14:20",
        "action": "joined",
        "text": "John started a huddle to discuss the sprint planning",
    },
    {
        "participant": "john.doe",
        "time": "14:45",
        "action": "ended",
        "text": "Huddle ended",
    },
]

lines = []
lines.append(h2("Slack Huddles"))

if huddle_sessions:
    # Group by participant for better organization
    by_participant = {}
    for session in huddle_sessions:
        participant = session["participant"]
        if participant not in by_participant:
            by_participant[participant] = []
        by_participant[participant].append(session)

    for participant, sessions in by_participant.items():
        lines.append(f"\n🗣️ **{participant}:**")
        for session in sessions:
            action_emoji = (
                "🔗"
                if session["action"] == "joined"
                else "🔚"
                if session["action"] == "ended"
                else "💬"
            )
            lines.append(
                f"  - {session['time']} - {action_emoji} {session['action']} huddle"
            )
            if session.get("text") and session["text"].strip():
                # Add original message if it contains useful info
                clean_text = session["text"].replace("\n", " ").strip()
                if len(clean_text) > 80:
                    clean_text = clean_text[:77] + "..."
                lines.append(f'    💭 "{clean_text}"')
else:
    lines.append("- (nenhum huddle)")

print("\n".join(lines))
