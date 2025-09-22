#!/usr/bin/env python3
"""Test the enhanced Jira functionality"""

import os
import datetime as dt
from dotenv import load_dotenv

load_dotenv()


def test_jira_enhanced():
    # Import the function from daily_digest
    from daily_digest import jira_enhanced_status

    target_date = dt.date(2025, 9, 19)
    print(f"🔍 Testing enhanced Jira for {target_date}")

    result = jira_enhanced_status(target_date)

    print(f"\n📊 Current Status ({len(result['current_status'])} issues):")
    if result["current_status"]:
        for issue in result["current_status"]:
            print(f"  - {issue['key']}: {issue['summary']}")
            print(f"    Status: {issue['status']}, Assignee: {issue['assignee']}")
    else:
        print("  No issues in progress or review")

    print(f"\n🔄 Movements ({len(result['movements'])} movements):")
    if result["movements"]:
        for movement in result["movements"]:
            print(f"  - {movement['key']}: {movement['summary']}")
            for change in movement["changes"]:
                print(f"    {change['time']}: {change['from']} → {change['to']}")
    else:
        print("  No card movements")


def test_jira_status_values():
    """Test to see what status values are available in your Jira"""
    import base64
    import requests

    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_TOKEN")

    if not all([base_url, email, token]):
        print("❌ Missing Jira credentials")
        return

    auth_string = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
    }

    try:
        # Get all statuses
        url = f"{base_url}/rest/api/3/status"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            statuses = response.json()
            print(f"\n📋 Available Jira statuses ({len(statuses)} total):")
            for status in statuses:
                category = status.get("statusCategory", {}).get("name", "Unknown")
                print(f"  - {status.get('name')} (Category: {category})")

            # Find statuses that might be "in progress" or "review"
            progress_statuses = []
            review_statuses = []

            for status in statuses:
                name = status.get("name", "").lower()
                category = status.get("statusCategory", {}).get("name", "").lower()

                if "progress" in name or "doing" in category:
                    progress_statuses.append(status.get("name"))
                elif "review" in name or "test" in name:
                    review_statuses.append(status.get("name"))

            print("\n🔧 Suggested status query:")
            all_suggested = progress_statuses + review_statuses
            if all_suggested:
                status_list = '", "'.join(all_suggested)
                print(f'  status IN ("{status_list}")')
            else:
                print("  Could not determine appropriate statuses automatically")

        else:
            print(f"❌ Failed to get statuses: {response.status_code}")

    except Exception as e:
        print(f"❌ Error getting statuses: {e}")


if __name__ == "__main__":
    print("🧪 Testing Enhanced Jira Functionality")
    print("=" * 50)

    test_jira_status_values()
    test_jira_enhanced()
