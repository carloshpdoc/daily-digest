#!/usr/bin/env python3
"""Test for issues with current status values"""

import base64
import os

import requests
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("JIRA_BASE_URL")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_TOKEN")

if all([base_url, email, token]):
    auth_string = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
    }

    target_statuses = ["Em andamento", "Em análise", "Revisar"]

    print("🔍 Looking for issues with target statuses...")

    # Get a large sample of issues and check their statuses
    jql = "updated >= -7d ORDER BY updated DESC"
    url = f"{base_url}/rest/api/3/search"
    params = {"jql": jql, "fields": "summary,status,key,assignee", "maxResults": 100}

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        print(f"📊 Checking {len(data.get('issues', []))} of {total} recent issues")

        status_counts = {}
        matching_issues = []

        for issue in data.get("issues", []):
            status = issue.get("fields", {}).get("status", {}).get("name", "")

            # Count all statuses
            status_counts[status] = status_counts.get(status, 0) + 1

            # Check if it matches our target statuses
            if status in target_statuses:
                assignee = issue.get("fields", {}).get("assignee")
                assignee_name = "Unassigned"
                if assignee:
                    assignee_name = assignee.get(
                        "displayName", assignee.get("name", "Unknown")
                    )

                matching_issues.append(
                    {
                        "key": issue.get("key"),
                        "summary": issue.get("fields", {}).get("summary", "")[:60],
                        "status": status,
                        "assignee": assignee_name,
                    }
                )

        print("\n📈 Status distribution in last 7 days:")
        for status, count in sorted(
            status_counts.items(), key=lambda x: x[1], reverse=True
        ):
            marker = " ✅" if status in target_statuses else ""
            print(f"  - {status}: {count}{marker}")

        print(f"\n🎯 Found {len(matching_issues)} issues matching target statuses:")
        for issue in matching_issues:
            print(
                f"  - {issue['key']}: {issue['summary']} ({issue['status']}) - {issue['assignee']}"
            )

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:200])
else:
    print("❌ Missing Jira credentials")
