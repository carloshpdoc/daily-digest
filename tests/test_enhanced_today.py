#!/usr/bin/env python3
"""Test enhanced Jira functionality with current date"""

import datetime as dt

from daily_digest import jira_enhanced_status

# Test with current date
target_date = dt.date.today()
print(f"🔍 Testing enhanced Jira for {target_date}")

result = jira_enhanced_status(target_date)

print(f"\n📊 Current Status ({len(result['current_status'])} issues):")
if result["current_status"]:
    # Group by status
    by_status = {}
    for issue in result["current_status"]:
        status = issue["status"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(issue)

    for status, issues in by_status.items():
        print(f"\n**{status}:**")
        for issue in issues:
            assignee = (
                f" ({issue['assignee']})" if issue["assignee"] != "Unassigned" else ""
            )
            print(f"  - {issue['key']}: {issue['summary']}{assignee}")
else:
    print("  No issues in progress or review")

print(f"\n🔄 Movements ({len(result['movements'])} movements):")
if result["movements"]:
    for movement in result["movements"]:
        print(f"\n**{movement['key']}**: {movement['summary']}")
        for change in movement["changes"]:
            time_str = change["time"][11:16] if len(change["time"]) > 10 else ""
            print(f"  - {time_str} Moved: {change['from']} → {change['to']}")
else:
    print("  No card movements")

print("\n✅ Enhanced Jira integration is working!")
print(f"   - Found {len(result['current_status'])} current issues in progress/review")
print(f"   - Found {len(result['movements'])} card movements for {target_date}")
