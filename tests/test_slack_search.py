#!/usr/bin/env python3
"""Test Slack Search API functionality"""

import os
import requests
from dotenv import load_dotenv

# Debug .env loading
env_result = load_dotenv()
print(f"🔧 .env loaded: {env_result}")

# Check all SLACK environment variables
print("🔍 Slack environment variables:")
for key, value in os.environ.items():
    if "SLACK" in key:
        print(f"  {key}: {value[:30]}...")
print()


def test_slack_search():
    # Try alternative approaches to get the token
    token = os.getenv("SLACK_USER_TOKEN")

    if not token:
        # Try reading from .env file directly
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("SLACK_USER_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        print("🔧 Found token in .env file directly")
                        break
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")

    if not token:
        print("❌ No valid SLACK_USER_TOKEN found")
        return False

    token = token.strip()
    print(f"🔑 Token loaded: {token[:20]}...")

    print(f"🔑 Token loaded: {token[:20]}...")
    if not token.startswith(("xoxp-", "xoxe.")):
        print("⚠️  Token format unexpected")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    print("🔍 Testing Slack Search API...")
    print("=" * 50)

    # Test search.messages endpoint with huddle query
    search_query = "huddle from:@teammate on:2025-09-19"
    url = "https://slack.com/api/search.messages"

    params = {"query": search_query, "count": 10, "highlight": True}

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    result = resp.json()

    print(f"🔎 Testing search query: '{search_query}'")

    if result.get("ok"):
        print("✅ Search API access - PASSED")

        messages = result.get("messages", {})
        total = messages.get("total", 0)
        matches = messages.get("matches", [])

        print(f"   Found {total} total results")
        print(f"   Retrieved {len(matches)} matches")

        if matches:
            print("\n📝 Sample results:")
            for i, match in enumerate(matches[:3]):  # Show first 3
                user = match.get("user", "unknown")
                text = (
                    match.get("text", "")[:100] + "..."
                    if len(match.get("text", "")) > 100
                    else match.get("text", "")
                )
                ts = match.get("ts", "")
                print(f"   {i + 1}. User: {user}")
                print(f"      Text: {text}")
                print(f"      Timestamp: {ts}")
                print()
        else:
            print("   ℹ️  No messages found for this query")
            print("   💡 Try a broader search term or different date")

        return True

    else:
        error = result.get("error", "unknown")
        print(f"❌ Search API access - FAILED: {error}")

        if error == "missing_scope":
            print("   💡 Need 'search:read' scope for search functionality")
            print("   📝 Current minimal scopes: users:read, im:history")
            print("   🔧 Add 'search:read' scope in your Slack app settings")
        elif error == "invalid_auth":
            print("   🔄 Token may need refresh")

        return False


def test_alternative_searches():
    """Test different search query patterns"""
    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # Test queries that might find huddle activity
    test_queries = [
        "huddle",
        "joined the huddle",
        "started a huddle",
        "from:@teammate",
        "in:@your.username",  # DM with you
        "after:2025-09-19 before:2025-09-20",
    ]

    print("\n🧪 Testing alternative search patterns...")
    print("=" * 50)

    for query in test_queries:
        print(f"Testing: '{query}'")

        params = {"query": query, "count": 3}
        resp = requests.get(
            "https://slack.com/api/search.messages",
            headers=headers,
            params=params,
            timeout=30,
        )
        result = resp.json()

        if result.get("ok"):
            total = result.get("messages", {}).get("total", 0)
            print(f"   ✅ {total} results")
        else:
            error = result.get("error", "unknown")
            print(f"   ❌ {error}")
        print()


if __name__ == "__main__":
    success = test_slack_search()
    if success:
        test_alternative_searches()
