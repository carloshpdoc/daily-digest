#!/usr/bin/env python3
"""
daily_digest.py (patched)
- Adiciona sanitização do ICS para corrigir "unsupported property: 02"
- Expansão de RRULE no iCal
- Fallback Google Calendar API
- Slack DMs com resolução por @handle, display_name, real_name, email e IDs diretos
- Flag opcional --slack-dump para listar usuários detectados
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

TZ = ZoneInfo(os.getenv("TIMEZONE", "America/Sao_Paulo"))


# ---------- Helpers ----------
def h2(t):
    return f"\n{t}\n" + "—" * len(t) + "\n"


def to_iso_z(d):
    return d.astimezone(ZoneInfo("UTC")).isoformat()


def env_required(name):
    v = os.getenv(name)
    if not v:
        print(f"[aviso] variável {name} não definida; pulando esta fonte.")
    return v


# ---------- Slack token store/refresh ----------
def _store_path():
    return os.getenv("SLACK_TOKEN_STORE", ".slack_token.json")


def _load_store():
    if os.path.exists(_store_path()):
        try:
            with open(_store_path(), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_store(data):
    try:
        with open(_store_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except:
        pass


def get_slack_access_token():
    # First try direct user token (no refresh needed)
    user_token = os.getenv("SLACK_USER_TOKEN")
    if user_token:
        return user_token, "env"

    # Try stored token
    store = _load_store()
    now = int(time.time())
    if store.get("access_token") and store.get("expires_at", 0) > now + 60:
        return store["access_token"], "store"

    # Try token refresh (optional - only if credentials available)
    cid = os.getenv("SLACK_CLIENT_ID")
    csec = os.getenv("SLACK_CLIENT_SECRET")
    rtok = store.get("refresh_token") or os.getenv("SLACK_REFRESH_TOKEN")

    if not (cid and csec and rtok):
        print(
            "[aviso] Slack: sem token direto nem credenciais para refresh; pulando Slack."
        )
        return None, "missing"

    url = "https://slack.com/api/oauth.v2.access"
    resp = requests.post(
        url,
        data={
            "client_id": cid,
            "client_secret": csec,
            "grant_type": "refresh_token",
            "refresh_token": rtok,
        },
        timeout=30,
    ).json()
    if not resp.get("ok"):
        return None, "refresh-failed"
    atok = resp.get("access_token") or resp.get("token")
    new_r = resp.get("refresh_token") or rtok
    exp_in = int(resp.get("expires_in", 12 * 60 * 60))
    _save_store(
        {
            "access_token": atok,
            "refresh_token": new_r,
            "expires_at": int(time.time()) + exp_in,
        }
    )
    return atok, "refreshed"


def _slack_user_map(headers):
    users = {}
    cursor = None
    while True:
        params = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        res = requests.get(
            "https://slack.com/api/users.list",
            headers=headers,
            params=params,
            timeout=30,
        ).json()
        if not res.get("ok"):
            break
        for m in res.get("members", []):
            uid = m.get("id")
            name = m.get("name") or ""
            prof = m.get("profile", {}) or {}
            disp = prof.get("display_name_normalized") or ""
            real = prof.get("real_name_normalized") or ""
            email = prof.get("email")
            if name:
                users["@" + name.lower()] = uid
            if disp:
                users["@" + disp.lower()] = uid
            if real:
                users["@" + real.lower()] = uid
            if email:
                users[email.lower()] = uid
        cursor = res.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return users


def slack_dump():
    atok, _ = get_slack_access_token()
    if not atok:
        return 1
    headers = {"Authorization": f"Bearer {atok}"}
    m = _slack_user_map(headers)
    print(json.dumps(m, indent=2, ensure_ascii=False))
    return 0


def slack_dm_huddles(START, END):
    """Enhanced Slack huddle detection with participant and timing information"""
    atok, _ = get_slack_access_token()
    if not atok:
        return []
    headers = {"Authorization": f"Bearer {atok}"}

    usernames = [
        u.strip() for u in os.getenv("SLACK_DM_USERNAMES", "").split(",") if u.strip()
    ]
    emails = [
        e.strip().lower()
        for e in os.getenv("SLACK_DM_EMAILS", "").split(",")
        if e.strip()
    ]
    ids = [
        i.strip() for i in os.getenv("SLACK_DM_USER_IDS", "").split(",") if i.strip()
    ]

    users = _slack_user_map(headers)
    user_names = {v: k for k, v in users.items()}  # Reverse mapping for names

    # email lookup extra
    for em in emails:
        if em in users:
            continue
        lr = requests.get(
            "https://slack.com/api/users.lookupByEmail",
            headers=headers,
            params={"email": em},
            timeout=15,
        ).json()
        if lr.get("ok"):
            uid = lr.get("user", {}).get("id")
            if uid:
                users[em] = uid

    target_ids = []
    dm_participants = {}  # Map DM ID to participant info

    for uname in usernames:
        uid = users.get(uname.lower())
        if uid:
            target_ids.append(uid)
        else:
            print(f"[aviso] Slack: não achei {uname}")
    for em in emails:
        uid = users.get(em)
        if uid:
            target_ids.append(uid)
        else:
            print(f"[aviso] Slack: não achei {em}")
    target_ids += ids

    # abrir DMs and get participant info
    dm_ids = []
    for uid in target_ids:
        opened = requests.post(
            "https://slack.com/api/conversations.open",
            headers=headers,
            data={"users": uid},
            timeout=15,
        ).json()
        if opened.get("ok") and opened.get("channel", {}).get("id"):
            dm_id = opened["channel"]["id"]
            dm_ids.append(dm_id)

            # Get participant name
            participant_name = user_names.get(uid, uid)
            if participant_name.startswith("@"):
                participant_name = participant_name[1:]  # Remove @ prefix
            dm_participants[dm_id] = participant_name

    # Enhanced huddle detection patterns
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

    huddle_sessions = []

    for dm_id in dm_ids:
        participant = dm_participants.get(dm_id, "Unknown")

        hist = requests.get(
            "https://slack.com/api/conversations.history",
            headers=headers,
            params={
                "channel": dm_id,
                "oldest": int(START.timestamp()),
                "latest": int(END.timestamp()),
                "inclusive": "true",
            },
            timeout=30,
        ).json()

        if not hist.get("ok"):
            continue

        huddle_events = []

        for msg in hist.get("messages", []):
            msg_text = msg.get("text", "")
            msg_subtype = msg.get("subtype", "")
            msg_ts = float(msg.get("ts", 0))

            # Check if this is a huddle-related message
            if (
                "huddle" in msg_subtype.lower()
                or huddle_patterns.search(msg_text)
                or "huddle" in msg_text.lower()
            ):
                # Convert timestamp to readable format
                import datetime

                msg_time = datetime.datetime.fromtimestamp(msg_ts, tz=TZ)

                huddle_events.append(
                    {
                        "time": msg_time,
                        "text": msg_text,
                        "subtype": msg_subtype,
                        "participant": participant,
                        "timestamp": msg_ts,
                    }
                )

        # Group huddle events into sessions
        if huddle_events:
            # Sort by timestamp
            huddle_events.sort(key=lambda x: x["timestamp"])

            for event in huddle_events:
                session_info = {
                    "participant": event["participant"],
                    "time": event["time"].strftime("%H:%M"),
                    "date": event["time"].strftime("%Y-%m-%d"),
                    "text": event["text"],
                    "action": (
                        "joined"
                        if any(
                            word in event["text"].lower()
                            for word in ["joined", "iniciou", "started", "entrou"]
                        )
                        else (
                            "ended"
                            if any(
                                word in event["text"].lower()
                                for word in ["ended", "left", "saiu"]
                            )
                            else "activity"
                        )
                    ),
                }
                huddle_sessions.append(session_info)

    return huddle_sessions


# ---------- ICS sanitizer ----------
def _sanitize_ics(raw: bytes) -> bytes:
    # Normalize line endings
    txt = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    # Handle iCal line folding (RFC 5545): lines beginning with SPACE or TAB are continuations
    unfolded_lines = []
    current_line = b""

    for line in txt.split(b"\n"):
        if line.startswith(b" ") or line.startswith(b"\t"):
            # Continuation line - remove leading whitespace and append to current line
            current_line += line[1:]
        else:
            # New property line
            if current_line:
                unfolded_lines.append(current_line)
            current_line = line

    # Don't forget the last line
    if current_line:
        unfolded_lines.append(current_line)

    # Now filter out problematic lines
    sanitized_lines = []
    for line in unfolded_lines:
        if not line.strip():
            continue
        # Skip lines where the property name is just digits
        if b":" in line:
            prop = line.split(b":", 1)[0].strip()
            if prop.isdigit():
                continue
        sanitized_lines.append(line)

    return b"\n".join(sanitized_lines)


# ---------- Google Calendar ----------
# ---------- GitHub PRs ----------
def github_prs(start_date, end_date):
    token = env_required("GITHUB_TOKEN")
    repos = os.getenv("GITHUB_REPOS", "").split(",")

    if not token:
        return []

    headers = {"Authorization": f"token {token}"}
    prs = []

    for repo in repos:
        repo = repo.strip()
        if not repo:
            continue

        try:
            # First try to get repository info to check access
            repo_info_url = f"https://api.github.com/repos/{repo}"
            repo_check = requests.get(repo_info_url, headers=headers, timeout=30)

            if repo_check.status_code == 404:
                print(f"[aviso] Repositório {repo} não encontrado")
                continue
            elif repo_check.status_code != 200:
                print(f"[aviso] Erro ao acessar {repo}: {repo_check.status_code}")
                continue

            # Search for PRs in the repository (simplified search)
            search_query = (
                f"repo:{repo} type:pr updated:>={start_date.strftime('%Y-%m-%d')}"
            )

            url = f"https://api.github.com/search/issues?q={quote(search_query)}"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    prs.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("html_url", ""),
                            "state": item.get("state", ""),
                            "repo": repo,
                        }
                    )
            else:
                print(
                    f"[aviso] GitHub API erro {response.status_code} para {repo}: {response.text[:200]}"
                )

        except Exception as e:
            print(f"[aviso] GitHub falhou para {repo}: {e}")

    return prs


# ---------- Jira Issues ----------
def jira_enhanced_status(target_date):
    """
    Enhanced Jira function that returns:
    1. Current issues in 'In Progress' and 'Review' columns
    2. Issue movements that happened on the target date
    """
    base_url = env_required("JIRA_BASE_URL")
    email = env_required("JIRA_EMAIL")
    token = env_required("JIRA_TOKEN")

    if not all([base_url, email, token]):
        return {"current_status": [], "movements": []}

    import base64

    auth_string = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
    }

    result = {"current_status": [], "movements": []}

    try:
        # 1. Get current issues in "In Progress" and "Review" columns assigned to current user
        # Get recent issues assigned to current user and filter by status in code
        status_jql = f"assignee = '{email}' AND updated >= -30d ORDER BY status ASC, updated DESC"

        url = f"{base_url}/rest/api/3/search"
        params = {
            "jql": status_jql,
            "fields": "summary,status,key,updated,assignee",
            "maxResults": 100,
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            matched_issues = 0

            for issue in data.get("issues", []):
                # Filter by status in code since JQL doesn't work with specific status names
                status_name = issue.get("fields", {}).get("status", {}).get("name", "")

                # Only include issues that are in progress or review states
                if status_name in ["Em andamento", "Em análise", "Revisar"]:
                    matched_issues += 1

                    result["current_status"].append(
                        {
                            "key": issue.get("key", ""),
                            "summary": issue.get("fields", {}).get("summary", ""),
                            "status": status_name,
                            "updated": issue.get("fields", {}).get("updated", ""),
                        }
                    )

            # Optional: print debug info if needed
            # print(f"[debug] Jira query returned {total_issues} issues, {matched_issues} matched target statuses")
        else:
            print(
                f"[aviso] Jira current status erro {response.status_code}: {response.text[:200]}"
            )

        # 2. Get issue movements on the target date for current user
        movements_jql = f"assignee = '{email}' AND updated >= '{target_date.strftime('%Y-%m-%d')}' AND updated <= '{target_date.strftime('%Y-%m-%d')}' ORDER BY updated DESC"

        params = {
            "jql": movements_jql,
            "fields": "summary,status,key,updated",
            "maxResults": 50,
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            for issue in data.get("issues", []):
                # Get issue history to see what changed
                issue_key = issue.get("key", "")
                history_url = f"{base_url}/rest/api/3/issue/{issue_key}/changelog"

                history_response = requests.get(
                    history_url, headers=headers, timeout=30
                )

                status_changes = []
                if history_response.status_code == 200:
                    history_data = history_response.json()

                    for history in history_data.get("values", []):
                        # Check if this change happened on target date
                        change_date = history.get("created", "")[
                            :10
                        ]  # Extract YYYY-MM-DD
                        if change_date == target_date.strftime("%Y-%m-%d"):
                            for item in history.get("items", []):
                                if item.get("field") == "status":
                                    status_changes.append(
                                        {
                                            "from": item.get("fromString", ""),
                                            "to": item.get("toString", ""),
                                            "time": history.get("created", ""),
                                        }
                                    )

                if status_changes:
                    result["movements"].append(
                        {
                            "key": issue.get("key", ""),
                            "summary": issue.get("fields", {}).get("summary", ""),
                            "changes": status_changes,
                        }
                    )

        else:
            print(
                f"[aviso] Jira movements erro {response.status_code}: {response.text[:200]}"
            )

    except Exception as e:
        print(f"[aviso] Jira enhanced status falhou: {e}")

    return result


def jira_issues(start_date, end_date):
    """Legacy function - kept for backward compatibility"""
    base_url = env_required("JIRA_BASE_URL")
    email = env_required("JIRA_EMAIL")
    token = env_required("JIRA_TOKEN")

    if not all([base_url, email, token]):
        return []

    import base64

    auth_string = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
    }

    # JQL query for issues updated in the date range (remove updatedBy filter as it's not available)
    jql = f"updated >= '{start_date.strftime('%Y-%m-%d')}' AND updated <= '{end_date.strftime('%Y-%m-%d')}' ORDER BY updated DESC"

    try:
        url = f"{base_url}/rest/api/3/search"
        params = {"jql": jql, "fields": "summary,status,key,updated", "maxResults": 50}

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            issues = []
            for issue in data.get("issues", []):
                issues.append(
                    {
                        "key": issue.get("key", ""),
                        "summary": issue.get("fields", {}).get("summary", ""),
                        "status": issue.get("fields", {})
                        .get("status", {})
                        .get("name", ""),
                        "updated": issue.get("fields", {}).get("updated", ""),
                    }
                )
            return issues
        else:
            print(
                f"[aviso] Jira API erro {response.status_code}: {response.text[:200]}"
            )

    except Exception as e:
        print(f"[aviso] Jira falhou: {e}")

    return []


def gcal_events(START, END):
    import datetime as _dt
    import os
    from zoneinfo import ZoneInfo as _ZI

    import requests
    from dateutil.rrule import rrulestr
    from icalendar import Calendar

    tz = TZ
    ics_src = os.getenv("GCAL_ICS_URL")
    token = os.getenv("GOOGLE_CALENDAR_TOKEN")

    # Use the global _sanitize_ics function defined above

    def _norm(dtv):
        if isinstance(dtv, _dt.date) and not isinstance(dtv, _dt.datetime):
            return _dt.datetime.combine(dtv, _dt.time.min).replace(tzinfo=tz)
        if isinstance(dtv, _dt.datetime):
            if dtv.tzinfo is None:
                return dtv.replace(tzinfo=_ZI("UTC")).astimezone(tz)
            return dtv.astimezone(tz)
        return None

    def _parse_ics(raw: bytes):
        # Use the exact same sanitization as test_calendar.py
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

        sanitized = sanitize_ics(raw)
        cal = Calendar.from_ical(sanitized)
        events = []
        for comp in cal.walk("vevent"):
            title = str(comp.get("summary") or "(sem título)")
            ds, de, rr = comp.get("dtstart"), comp.get("dtend"), comp.get("rrule")
            if not ds:
                continue
            s1 = _norm(ds.dt)
            e1 = _norm(de.dt) if de else (s1 + _dt.timedelta(hours=1) if s1 else None)
            if not (s1 and e1):
                continue

            if not rr:  # non-recurring
                if s1 <= END and e1 >= START:
                    events.append(
                        {"title": title, "start": s1.isoformat(), "end": e1.isoformat()}
                    )
                continue

            # recurring
            # Valid RRULE properties according to RFC 5545
            valid_rrule_props = {
                "FREQ",
                "UNTIL",
                "COUNT",
                "INTERVAL",
                "BYSECOND",
                "BYMINUTE",
                "BYHOUR",
                "BYDAY",
                "BYMONTHDAY",
                "BYYEARDAY",
                "BYWEEKNO",
                "BYMONTH",
                "BYSETPOS",
                "WKST",
            }

            parts = []
            for k, v in rr.items():
                # Filter out invalid RRULE properties
                if str(k).upper() not in valid_rrule_props:
                    continue

                vals = []
                for it in v:
                    if isinstance(it, bytes):
                        it = it.decode("utf-8", "ignore")
                    vals.append(str(it))
                parts.append(f"{k}=" + ",".join(vals))

            if not parts:  # Skip if no valid RRULE parts
                continue

            rrule_str = ";".join(parts)
            dtstart_utc = s1.astimezone(_ZI("UTC")).strftime("%Y%m%dT%H%M%SZ")

            try:
                rule = rrulestr(
                    f"DTSTART:{dtstart_utc}\nRRULE:{rrule_str}", forceset=True
                )
            except ValueError:
                # Skip this recurring event if RRULE parsing fails
                continue

            w0 = START.astimezone(_ZI("UTC"))
            w1 = END.astimezone(_ZI("UTC"))
            for occ in rule.between(w0, w1, inc=True):
                occ_local = (
                    occ.astimezone(tz)
                    if occ.tzinfo
                    else occ.replace(tzinfo=_ZI("UTC")).astimezone(tz)
                )
                dur = e1 - s1
                oe = occ_local + dur
                if occ_local <= END and oe >= START:
                    events.append(
                        {
                            "title": title,
                            "start": occ_local.isoformat(),
                            "end": oe.isoformat(),
                        }
                    )
        events.sort(key=lambda x: x["start"])
        return events

    # 1) ICS (URL or file)
    if ics_src:
        try:
            if ics_src.startswith(("http://", "https://")):
                resp = requests.get(ics_src, timeout=30, allow_redirects=True)
                ct = resp.headers.get("Content-Type", "")
                if not resp.ok:
                    print(f"[aviso] iCal HTTP {resp.status_code}: {resp.text[:200]}")
                elif "text/calendar" not in ct.lower():
                    print(
                        f"[aviso] iCal content-type inesperado: {ct}. Trecho: {resp.text[:160]!r}"
                    )
                else:
                    return _parse_ics(resp.content)
            else:
                with open(ics_src, "rb") as f:
                    raw = f.read()
                return _parse_ics(raw)
        except Exception as e:
            print(
                f"[aviso] iCal falhou ({type(e).__name__}: {e}); tentando API se houver token..."
            )

    # 2) Fallback: Calendar API
    if not token:
        print(
            "[aviso] Sem GCAL_ICS_URL válido e sem GOOGLE_CALENDAR_TOKEN; pulando Google Calendar."
        )
        return []
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "timeMin": to_iso_z(START),
        "timeMax": to_iso_z(END),
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    r = requests.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        params=params,
        timeout=30,
    )
    if not r.ok:
        print(f"[aviso] Google Calendar API erro {r.status_code}: {r.text[:200]}")
        return []
    out = []
    for ev in r.json().get("items", []):
        title = ev.get("summary") or "(sem título)"
        start_dt = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get(
            "date"
        )
        end_dt = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
        out.append({"title": title, "start": start_dt, "end": end_dt})
    return out


# ---------- Main ----------
if __name__ == "__main__":
    import sys  # ensure this is imported at top if not already

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD")
    ap.add_argument(
        "--slack-dump",
        dest="slack_dump",
        action="store_true",
        help="Print Slack user map and exit",
    )
    # ap.add_argument(
    #     "--search-huddles",
    #     dest="search_huddles",
    #     action="store_true",
    #     help="Test automated Slack huddle search (requires search:read scope)",
    # )
    args = ap.parse_args()

    # use underscore, not hyphen:
    if args.slack_dump:
        sys.exit(slack_dump())

    # if args.search_huddles:
    #     # Test automated huddle search functionality
    #     try:
    #         from slack_search_automation import (
    #             search_huddle_activity,
    #             format_huddle_results,
    #         )
    #
    #         if args.date:
    #             report_day = dt.date.fromisoformat(args.date)
    #         else:
    #             report_day = dt.datetime.now(TZ).date() - dt.timedelta(
    #                 days=1
    #             )  # Default to yesterday
    #
    #         print(f"🔍 Testing automated Slack huddle search for {report_day}")
    #         print("=" * 60)
    #
    #         # Get target users from environment
    #         target_usernames = os.getenv("SLACK_DM_USERNAMES", "").split(",")
    #         target_usernames = [u.strip() for u in target_usernames if u.strip()]
    #
    #         if not target_usernames:
    #             print("❌ No target usernames found in SLACK_DM_USERNAMES")
    #             print(
    #                 "💡 Add usernames like: SLACK_DM_USERNAMES=@yago.castro,@barbara.ramos"
    #             )
    #             sys.exit(1)
    #
    #         date_str = report_day.strftime("%Y-%m-%d")
    #         all_events = []
    #
    #         for username in target_usernames:
    #             if username:
    #                 print(f"\n🔍 Searching huddles with {username} on {date_str}")
    #                 events = search_huddle_activity(username, date_str)
    #                 all_events.extend(events)
    #
    #         if all_events:
    #             result = format_huddle_results(all_events)
    #             print(f"\n{result}")
    #         else:
    #             print(f"\nℹ️  No huddle activity found for {date_str}")
    #             print("💡 Try a different date or check if huddles occurred in DMs")
    #
    #     except ImportError:
    #         print("❌ Slack search automation not available")
    #         print("💡 Make sure slack_search_automation.py is in the same directory")
    #     except Exception as e:
    #         print(f"❌ Error in automated search: {str(e)}")
    #
    #     sys.exit(0)

    # date handling
    if args.date:
        report_day = dt.date.fromisoformat(args.date)
    else:
        report_day = dt.datetime.now(TZ).date()

    START = dt.datetime.combine(report_day, dt.time.min).replace(tzinfo=TZ)
    END = dt.datetime.combine(report_day, dt.time.max).replace(tzinfo=TZ)

    lines = [f"📌 Resumo do dia — {report_day}\n"]

    # GitHub PRs
    prs = github_prs(report_day, report_day)
    lines.append(h2("GitHub PRs"))
    if prs:
        for pr in prs:
            lines.append(
                f"- [{pr['repo']}] {pr['title']} ({pr['state']}) - {pr['url']}"
            )
    else:
        lines.append("- (nenhum PR)")

    # Enhanced Jira Status
    jira_data = jira_enhanced_status(report_day)
    lines.append(h2("Jira Status"))

    # Current Status section
    lines.append("### My Issues in Progress & Review:")
    if jira_data["current_status"]:
        # Group by status
        by_status = {}
        for issue in jira_data["current_status"]:
            status = issue["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(issue)

        for status, issues in by_status.items():
            lines.append(f"\n**{status}:**")
            for issue in issues:
                lines.append(f"  - {issue['key']}: {issue['summary']}")
    else:
        lines.append("- (sem issues em progresso ou review)")

    # Movements section
    lines.append(f"\n### My Card Movements on {report_day}:")
    if jira_data["movements"]:
        for movement in jira_data["movements"]:
            lines.append(f"\n**{movement['key']}**: {movement['summary']}")
            for change in movement["changes"]:
                time_str = (
                    change["time"][11:16] if len(change["time"]) > 10 else ""
                )  # Extract HH:MM
                lines.append(f"  - {time_str} Moved: {change['from']} → {change['to']}")
    else:
        lines.append("- (sem movimentações de cards)")

    # Calendar
    evs = gcal_events(START, END)
    lines.append(h2("Google Calendar"))
    if evs:
        for e in evs:
            lines.append(f"- {e['title']} ({e['start']} → {e['end']})")
    else:
        lines.append("- (nenhum evento)")

    # Slack Huddles (COMMENTED OUT - Focus on Calendar, GitHub, Jira only)
    # huddle_sessions = slack_dm_huddles(START, END)
    # lines.append(h2("Slack Huddles"))
    # if huddle_sessions:
    #     # Group by participant for better organization
    #     by_participant = {}
    #     for session in huddle_sessions:
    #         participant = session["participant"]
    #         if participant not in by_participant:
    #             by_participant[participant] = []
    #         by_participant[participant].append(session)
    #
    #     for participant, sessions in by_participant.items():
    #         lines.append(f"\n🗣️ **{participant}:**")
    #         for session in sessions:
    #             action_emoji = (
    #                 "🔗"
    #                 if session["action"] == "joined"
    #                 else "🔚"
    #                 if session["action"] == "ended"
    #                 else "💬"
    #             )
    #             lines.append(
    #                 f"  - {session['time']} - {action_emoji} {session['action']} huddle"
    #             )
    #             if session.get("text") and session["text"].strip():
    #                 # Add original message if it contains useful info
    #                 clean_text = session["text"].replace("\n", " ").strip()
    #                 if len(clean_text) > 80:
    #                     clean_text = clean_text[:77] + "..."
    #                 lines.append(f'    💭 "{clean_text}"')
    # else:
    #     lines.append("- (nenhum huddle)")

    # Write to file
    output_file = os.getenv("OUTPUT_FILE", f"daily_report_{report_day}.txt")

    output_content = "\n".join(lines)
    print(output_content)

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"\n✅ Relatório salvo em: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Erro ao salvar arquivo: {e}")
