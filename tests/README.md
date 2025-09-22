# Tests

This directory contains test scripts to validate individual components of the daily digest tool.

## Running Tests

Before running tests, make sure you have:
1. Configured your `.env` file with API credentials
2. Activated your virtual environment: `source venv/bin/activate`

## Available Tests

### Core Functionality
- `test_calendar.py` - Test Google Calendar integration
- `test_jira_enhanced.py` - Test enhanced Jira functionality
- `test_jira_simple.py` - Test basic Jira integration

### Daily Report Testing
- `test_enhanced_today.py` - Test today's complete report
- `test_current_status.py` - Test current status checking

### Slack Integration (Optional)
- `test_slack_output.py` - Test Slack API connectivity
- `test_slack_scopes.py` - Test Slack permissions
- `test_slack_search.py` - Test Slack search functionality
- `test_huddle_detection.py` - Test huddle detection

## Usage

Run individual tests:
```bash
python tests/test_calendar.py
python tests/test_jira_enhanced.py
```

Or run all tests:
```bash
# From project root
for test in tests/test_*.py; do echo "Running $test"; python "$test"; echo; done
```

## Notes

- Tests use the same environment variables as the main script
- Slack tests require proper OAuth tokens (see main README)
- All tests are safe to run and won't modify your data