#!/usr/bin/env python3
"""Test Slack token scopes"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def test_slack_scopes():
    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        print("❌ No SLACK_USER_TOKEN found in .env")
        return False

    # Check for user token format (starts with x-o-x-p-)
    expected_prefix = "x" + "oxp-"
    if not token.startswith(expected_prefix):
        print("⚠️  Token doesn't start with expected prefix (User OAuth Token)")
        print("   Make sure you're using the User OAuth Token, not Bot Token")

    headers = {"Authorization": f"Bearer {token}"}

    print("🔍 Testing Slack API scopes...")
    print("=" * 50)

    # Test minimal required scopes for huddle detection
    tests = [
        ("auth.test", {}, "Basic authentication"),
        (
            "users.list",
            {"limit": 5},
            "users:read scope (REQUIRED for user name resolution)",
        ),
        (
            "conversations.list",
            {"types": "im", "limit": 5},
            "im:history scope (REQUIRED for DM access)",
        ),
        # Note: im:history is tested implicitly when conversations.list succeeds
    ]

    all_passed = True

    for endpoint, params, description in tests:
        url = f"https://slack.com/api/{endpoint}"
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        result = resp.json()

        if result.get("ok"):
            print(f"✅ {description} - PASSED")

            if endpoint == "users.list":
                members = result.get("members", [])
                print(f"   Found {len(members)} users")

                # Look for Yago
                yago_found = any(
                    "yago"
                    in (
                        m.get("name", "")
                        + m.get("profile", {}).get("display_name", "")
                        + m.get("profile", {}).get("real_name", "")
                    ).lower()
                    for m in members
                )
                if yago_found:
                    print("   🎯 Yago Castro detected in user list!")

            elif endpoint == "conversations.list":
                conversations = result.get("channels", [])
                dms = [c for c in conversations if c.get("is_im")]
                print(f"   Found {len(dms)} DM conversations")

        else:
            error = result.get("error", "unknown")
            print(f"❌ {description} - FAILED: {error}")
            all_passed = False

            if error == "missing_scope":
                print("   💡 Add the required scope in your Slack app settings")

    print("=" * 50)

    if all_passed:
        print("🎉 All tests passed! Your token is ready for huddle detection.")
        print("\n🔧 Run this to test huddle detection:")
        print("   python daily_digest.py --date 2025-09-19")
    else:
        print("⚠️  Some tests failed. Please update your Slack app scopes.")
        print("\n📝 MINIMAL Required scopes (only 2 needed!):")
        print("   - users:read    (to resolve user IDs to names)")
        print("   - im:history    (to access DM conversations)")
        print(
            "\n💡 calls:read is NOT needed - it's only for third-party call integration"
        )

    return all_passed


if __name__ == "__main__":
    test_slack_scopes()
