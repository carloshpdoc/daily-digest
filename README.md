# Daily Digest Generator

A comprehensive daily report generator that aggregates your development activity from GitHub, Jira, and Google Calendar into a single, clean markdown report.

## 📊 What it does

The Daily Digest tool automatically generates reports containing:

- **GitHub PRs**: Pull requests you created or were involved in
- **Jira Status**: Your current issues in progress and review, plus card movements
- **Google Calendar**: Your meetings and events for the day

## 🚀 Installation

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see Configuration section below).

### 3. Run Daily Digest

```bash
# Generate report for today
python daily_digest.py

# Generate report for specific date
python daily_digest.py --date 2025-09-19

# Generate report for yesterday
python daily_digest.py --date yesterday
```

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

#### GitHub Configuration
```env
GITHUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_USER=your_github_username
GITHUB_REPOS=owner/repository-name
```

**How to get GitHub token:**
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token with `repo` scope
3. Copy the token to your `.env` file

#### Jira Configuration
```env
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_TOKEN=your_jira_api_token
```

**How to get Jira token:**
1. Go to Jira Account Settings > Security > API tokens
2. Create API token
3. Copy the token to your `.env` file

#### Google Calendar Configuration
```env
GCAL_ICS_URL="https://calendar.google.com/calendar/ical/your-email%40company.com/private-your-private-key/basic.ics"
TIMEZONE=America/Sao_Paulo
```

**How to get Calendar ICS URL:**
1. Open Google Calendar
2. Go to Settings > Settings for my calendars
3. Select your calendar > Integrate calendar
4. Copy the "Secret address in iCal format"

#### Optional Configuration
```env
OUTPUT_FILE=/path/to/daily_report.txt
```

## 🔧 Usage

### Basic Usage
```bash
# Today's report
python daily_digest.py

# Specific date
python daily_digest.py --date 2025-09-19

# Yesterday's report
python daily_digest.py --date yesterday
```

### Automation (Daily Execution)

#### Option 1: Cron Job
Add to your crontab (`crontab -e`):
```bash
# Run daily at 6 PM
0 18 * * * cd /path/to/daily_digest_package && source venv/bin/activate && python daily_digest.py
```

#### Option 2: macOS Automator
1. Open Automator
2. Create new "Calendar Alarm"
3. Add "Run Shell Script" action:
```bash
cd /path/to/daily_digest_package
source venv/bin/activate
python daily_digest.py
```
4. Schedule for daily execution

#### Option 3: Launchd (macOS)
Create `~/Library/LaunchAgents/com.user.dailydigest.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.dailydigest</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/daily_digest_package/venv/bin/python</string>
        <string>/path/to/daily_digest_package/daily_digest.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/daily_digest_package</string>
</dict>
</plist>
```

Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.user.dailydigest.plist
```

## 📋 Sample Output

```markdown
📌 Resumo do dia — 2025-09-19

GitHub PRs
——————————

- [YourCompany/your-repo] [FIX][PROJ-1492] FIX: View By modal tappable area issue and code cleanup (closed) - https://github.com/YourCompany/your-repo/pull/2972
- [YourCompany/your-repo] 🚀 Release 2.6.0 (closed) - https://github.com/YourCompany/your-repo/pull/2971

Jira Status
———————————

### My Issues in Progress & Review:

**Em andamento:**
  - PROJ-1407: Adjust push notification redirect

**Em análise:**
  - PROD-2142: Create the debugView to analyzer deeplinks em PROD

### My Card Movements on 2025-09-19:
- (sem movimentações de cards)

Google Calendar
———————————————

- Daily (2025-09-19T10:00:00-03:00 → 2025-09-19T10:30:00-03:00)
- iOS Weekly (2025-09-19T14:00:00-03:00 → 2025-09-19T15:00:00-03:00)
- English Class (2025-09-19T16:30:00-03:00 → 2025-09-19T17:30:00-03:00)
```

## 🔍 Testing & Validation

### Test Individual Components

#### Test GitHub Integration
```bash
python -c "
from daily_digest import github_prs
import datetime
prs = github_prs(datetime.date(2025, 9, 19), datetime.date(2025, 9, 19))
print(f'Found {len(prs)} PRs')
"
```

#### Test Jira Integration
```bash
python test_jira_enhanced.py
```

#### Test Google Calendar
```bash
python test_calendar.py
```

### Validate Configuration
```bash
# Check environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['GITHUB_TOKEN', 'JIRA_BASE_URL', 'JIRA_EMAIL', 'JIRA_TOKEN', 'GCAL_ICS_URL']
for var in required:
    status = '✅' if os.getenv(var) else '❌'
    print(f'{status} {var}')
"
```

## 🚨 Troubleshooting

### Common Issues

#### GitHub 401 Error
- **Problem**: Invalid or expired GitHub token
- **Solution**: Generate new personal access token with `repo` scope

#### Jira 401 Error
- **Problem**: Invalid Jira credentials
- **Solution**: Verify email and API token, check Jira base URL

#### Google Calendar "unsupported property" Error
- **Problem**: iCal parsing issue (already fixed in current version)
- **Solution**: The enhanced parser handles this automatically

#### No Issues Found in Jira
- **Problem**: Issues not assigned to your user
- **Solution**: Check if issues are assigned to the email in `JIRA_EMAIL`

#### Missing Calendar Events
- **Problem**: Wrong ICS URL or private calendar access
- **Solution**:
  1. Verify the ICS URL is the "Secret address in iCal format"
  2. Make sure calendar is not set to private
  3. Test the URL in browser

### Debug Mode

Enable debug output by uncommenting the debug line in `daily_digest.py`:
```python
# Uncomment this line for debugging
print(f"[debug] Jira query returned {total_issues} issues, {matched_issues} matched target statuses")
```

### Environment Issues

If dependencies fail to install:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

## 📁 Project Structure

```
daily_digest_package/
├── daily_digest.py              # Main script
├── requirements.txt              # Dependencies
├── .env.example                 # Environment template
├── .env                         # Your credentials (create this)
├── README.md                    # This documentation
├── test_calendar.py             # Calendar testing
├── test_jira_enhanced.py        # Jira testing
└── slack_search_automation.py   # Slack integration (commented out)
```

## 🔒 Security Notes

- **Never commit `.env`** to version control
- **Keep API tokens secure** - they provide access to your accounts
- **Regularly rotate tokens** as per your organization's security policy
- **Use environment variables** in production deployments

## 🔄 Regular Maintenance

### Weekly
- Review generated reports for accuracy
- Check for any API errors in output

### Monthly
- Verify all integrations are working
- Update dependencies if needed:
  ```bash
  pip install --upgrade -r requirements.txt
  ```

### As Needed
- Rotate API tokens when they expire
- Update repository names in `GITHUB_REPOS` if changed
- Adjust `TIMEZONE` if you relocate

## 📞 Support

If you encounter issues:

1. **Check the troubleshooting section** above
2. **Validate your configuration** using the test commands
3. **Check API rate limits** - GitHub: 5000/hour, Jira: varies by plan
4. **Review logs** for specific error messages

## 🎯 Tips for Daily Use

- **Run at end of workday** to capture full day's activity
- **Keep the output file** for historical tracking
- **Use specific dates** to generate reports for past days
- **Automate execution** to build a consistent daily habit
- **Review weekly** to identify patterns in your work

## ⚡ Performance Notes

- **GitHub**: Fetches recent PRs efficiently with pagination
- **Jira**: Queries last 30 days of your assigned issues
- **Calendar**: Parses full iCal but only extracts target date
- **Execution time**: Typically 3-5 seconds for full report

## 🗂️ What Gets Tracked

### GitHub PRs
- PRs you created
- PRs you were assigned to review
- PRs where you commented
- Shows status (open/closed/merged) and direct links

### Jira Issues
- **Current Status**: Issues assigned to you in "Em andamento", "Em análise", or "Revisar"
- **Daily Movements**: Cards you moved between columns on the target date
- Shows issue key, summary, and movement times

### Google Calendar
- All events for the target date
- Shows event titles and time ranges
- Handles recurring events correctly
- Supports Brazilian timezone (America/Sao_Paulo)

## 🔧 Customization

### Adding New Repositories
Update `GITHUB_REPOS` in `.env`:
```env
GITHUB_REPOS=owner1/repo1,owner2/repo2
```

### Changing Output Format
Modify the `lines.append()` statements in `daily_digest.py` to customize the output format.

### Adding New Jira Status Types
Update the status filter in the `jira_enhanced_status()` function:
```python
if status_name in ["Em andamento", "Em análise", "Revisar", "Your New Status"]:
```

---

**Happy tracking! 📊 Your daily digest tool is ready to help you stay organized and productive.** 🚀