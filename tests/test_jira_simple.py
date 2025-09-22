#!/usr/bin/env python3
"""Simple test of Jira without date filtering"""

import os
import base64
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

    # Simple query for recent issues
    jql = "updated >= -30d ORDER BY updated DESC"
    url = f"{base_url}/rest/api/3/search"
    params = {"jql": jql, "fields": "summary,status,key,updated", "maxResults": 10}

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        print(f"📊 Found {total} recent issues")

        for issue in data.get("issues", []):
            key = issue.get("key")
            summary = issue.get("fields", {}).get("summary", "")[:50]
            status = issue.get("fields", {}).get("status", {}).get("name", "")
            updated = issue.get("fields", {}).get("updated", "")[:10]

            print(f"  - {key}: {summary}... ({status}) - {updated}")

            # Check if this would be included in our filter
            if status in ["Em andamento", "Em análise", "Revisar"]:
                print("    ✅ Would be included in current status")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:200])
else:
    print("❌ Missing Jira credentials")
