#!/usr/bin/env python3
"""Automated Slack Search for Huddle Detection"""

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()


def get_slack_token():
    """Get Slack token from environment or .env file"""
    token = os.getenv("SLACK_USER_TOKEN")

    if not token:
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("SLACK_USER_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")

    return token.strip() if token else None


def automated_slack_search(query, count=20):
    """
    Perform automated Slack search using the Search API

    Args:
        query (str): Search query (e.g., "huddle from:@yago.castro on:2025-09-19")
        count (int): Number of results to return (max 100)

    Returns:
        dict: Search results or error information
    """
    token = get_slack_token()
    if not token:
        return {"error": "No valid Slack token found"}

    headers = {"Authorization": f"Bearer {token}"}

    url = "https://slack.com/api/search.messages"
    params = {
        "query": query,
        "count": min(count, 100),  # API limit is 100
        "highlight": True,
        "sort": "timestamp",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        result = resp.json()

        if result.get("ok"):
            return result
        else:
            return {"error": result.get("error", "unknown")}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def search_huddle_activity(target_user, date_str=None, days_back=7):
    """
    Search for huddle activity with a specific user

    Args:
        target_user (str): Username to search for (e.g., "@yago.castro")
        date_str (str): Specific date in YYYY-MM-DD format (optional)
        days_back (int): Number of days to search back if no specific date

    Returns:
        list: Processed huddle events
    """
    if not target_user.startswith("@"):
        target_user = f"@{target_user}"

    search_queries = []

    if date_str:
        # Search for specific date
        search_queries = [
            f"huddle from:{target_user} on:{date_str}",
            f"huddle to:{target_user} on:{date_str}",
            f"joined the huddle from:{target_user} on:{date_str}",
            f"started a huddle in:{target_user} on:{date_str}",
        ]
    else:
        # Search recent days
        for i in range(days_back):
            search_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            search_queries.extend(
                [
                    f"huddle from:{target_user} on:{search_date}",
                    f"huddle to:{target_user} on:{search_date}",
                ]
            )

    all_events = []

    for query in search_queries:
        print(f"🔍 Searching: {query}")
        result = automated_slack_search(query, count=10)

        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
            continue

        messages = result.get("messages", {})
        matches = messages.get("matches", [])

        print(f"   ✅ Found {len(matches)} results")

        for match in matches:
            event = process_huddle_message(match, target_user)
            if event:
                all_events.append(event)

    # Remove duplicates and sort by timestamp
    unique_events = {}
    for event in all_events:
        key = f"{event['timestamp']}_{event['text'][:50]}"
        unique_events[key] = event

    return sorted(unique_events.values(), key=lambda x: x["timestamp"])


def process_huddle_message(message, target_user):
    """
    Process a Slack message to extract huddle information

    Args:
        message (dict): Slack message from search results
        target_user (str): Target user for context

    Returns:
        dict: Processed huddle event or None
    """
    text = message.get("text", "").lower()
    timestamp = float(message.get("ts", 0))
    user = message.get("user", "unknown")

    # Skip if not huddle-related
    huddle_keywords = ["huddle", "joined the call", "started a call"]
    if not any(keyword in text for keyword in huddle_keywords):
        return None

    # Determine action type
    action = "unknown"
    if any(word in text for word in ["joined", "iniciou", "started", "entrou"]):
        action = "joined"
    elif any(word in text for word in ["ended", "left", "saiu", "finished"]):
        action = "ended"
    elif "huddle" in text:
        action = "activity"

    return {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp),
        "user": user,
        "target_user": target_user.replace("@", ""),
        "action": action,
        "text": message.get("text", ""),
        "channel": message.get("channel", {}).get("name", ""),
        "permalink": message.get("permalink", ""),
    }


def format_huddle_results(events):
    """
    Format huddle events for display

    Args:
        events (list): List of huddle events

    Returns:
        str: Formatted output
    """
    if not events:
        return "No huddle activity found."

    output = []
    output.append(f"🎯 Found {len(events)} huddle events:")
    output.append("=" * 50)

    for event in events:
        dt = event["datetime"]
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")

        output.append(f"📅 {date_str} {time_str}")
        output.append(f"   👤 User: {event['user']}")
        output.append(f"   🎬 Action: {event['action']}")
        output.append(f"   💬 Text: {event['text'][:100]}...")
        if event.get("permalink"):
            output.append(f"   🔗 Link: {event['permalink']}")
        output.append("")

    return "\n".join(output)


def test_huddle_search():
    """Test the huddle search functionality"""
    print("🧪 Testing automated Slack huddle search...")
    print("=" * 60)

    # Test specific date search (the example from conversation)
    target_user = "@yago.castro"
    test_date = "2025-09-19"

    print(f"🔍 Searching for huddles with {target_user} on {test_date}")
    events = search_huddle_activity(target_user, test_date)

    result = format_huddle_results(events)
    print(result)

    # Test recent activity
    print("\n" + "=" * 60)
    print(f"🔍 Searching recent huddle activity with {target_user}")
    recent_events = search_huddle_activity(target_user, days_back=3)

    recent_result = format_huddle_results(recent_events)
    print(recent_result)


if __name__ == "__main__":
    # Check if search scope is available
    token = get_slack_token()
    if not token:
        print("❌ No Slack token found")
        exit(1)

    # Quick scope test
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://slack.com/api/search.messages",
        headers=headers,
        params={"query": "test", "count": 1},
    )
    result = resp.json()

    if result.get("error") == "missing_scope":
        print("❌ Missing 'search:read' scope!")
        print("📝 To enable automation:")
        print("   1. Go to https://api.slack.com/apps")
        print("   2. Select your app")
        print("   3. Go to 'OAuth & Permissions'")
        print("   4. Add 'search:read' scope")
        print("   5. Reinstall the app")
        print("\n💡 Current scopes: users:read, im:history")
        print("💡 Needed scopes: users:read, im:history, search:read")
    else:
        print("✅ Search API available! Running tests...")
        test_huddle_search()
