# Running the Scheduler Locally

This guide shows how to run the roster scheduler once for manual testing and verification.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit configuration (set API URL and keys)
vi .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run scheduler once
python scripts/run_scheduler_once.py

# 5. Check generated roster
ls -lh roster-json/
cat roster-json/roster-*.json
```

## Prerequisites

### 1. Python Environment

- Python 3.9+ installed
- Virtual environment recommended:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `requests` - API client
- `python-dotenv` - Environment variable loading
- `pyyaml` - Configuration files

### 3. Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required: API endpoint
ROSTER_API_BASE_URL=http://localhost:8000

# Optional: API authentication
ROSTER_API_KEY=your_api_key_here

# Optional: AI service (for AI-powered analysis)
AI_API_KEY=your_ai_api_key_here
AI_MODEL=gpt-3.5-turbo

# Roster output settings
WRITE_ROSTER_JSON=true
ROSTER_OUTPUT_DIR=roster-json

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/roster.log

# Generation settings
HISTORICAL_MONTHS=3
FUTURE_MONTHS=3
```

## Running the Scheduler

### Basic Usage

Run the scheduler once:

```bash
python scripts/run_scheduler_once.py
```

Expected output:

```
Loading configuration from: .env
============================================================
Starting one-time roster generation
============================================================

Configuration:
  API Base URL: http://localhost:8000
  Write JSON: True
  Output Directory: roster-json
  Historical Months: 3
  Future Months: 3
  Dry Run Mode: False

Initializing components...
  ✓ API Client: http://localhost:8000
  ✓ Roster Data Agent
  ✓ AI Analyzer
  ✓ Roster Orchestrator

Creating scheduler...

Running roster generation...
------------------------------------------------------------
[Roster generation logs...]
------------------------------------------------------------

✓ SUCCESS! Found 1 roster file(s):
  - roster-2025-10-23-143520.json (1247 bytes)

Latest file: /path/to/roster-mcp/roster-json/roster-2025-10-23-143520.json
To view: cat roster-json/roster-2025-10-23-143520.json

============================================================
One-time roster generation completed successfully!
============================================================
```

### Advanced Options

**Use custom environment file:**

```bash
python scripts/run_scheduler_once.py --env-file .env.local
```

**Dry run mode:**

```bash
python scripts/run_scheduler_once.py --dry-run
```

**Debug logging:**

```bash
LOG_LEVEL=DEBUG python scripts/run_scheduler_once.py
```

**Disable file writing:**

```bash
WRITE_ROSTER_JSON=false python scripts/run_scheduler_once.py
```

## Verifying Output

### 1. Check Generated Files

List generated roster files:

```bash
ls -lh roster-json/
```

Example output:
```
-rw-r--r--  1 user  staff  1.2K Oct 23 14:35 roster-2025-10-23-143520.json
```

### 2. View Roster Content

View the latest roster:

```bash
# Get latest file
LATEST=$(ls -t roster-json/roster-*.json | head -1)

# Pretty-print JSON
cat $LATEST | python -m json.tool

# Or use jq for better formatting
cat $LATEST | jq .
```

### 3. Validate JSON Structure

Expected structure:

```json
{
  "rosters": [
    {
      "date": "2025-10-26",
      "service_type": "chinese",
      "assignments": [
        {
          "role": "證道",
          "name": "張三",
          "member_id": "M001"
        }
      ]
    }
  ],
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "patterns": {
    "total_events": 12,
    "member_frequency": {...}
  },
  "metadata": {
    "months_ahead": 3,
    "category": "chinese",
    "generated_at": "2025-10-23T14:35:20.123456"
  }
}
```

### 4. Check File Naming

Files should follow the pattern:

```
roster-YYYY-MM-DD-HHMMSS.json
```

Example: `roster-2025-10-23-143520.json`

- Year: 4 digits
- Month: 2 digits (zero-padded)
- Day: 2 digits (zero-padded)
- Hour: 2 digits (24-hour format)
- Minute: 2 digits
- Second: 2 digits

## Troubleshooting

### Error: "No module named 'dotenv'"

**Solution:** Install dependencies

```bash
pip install python-dotenv
```

### Error: "Failed to connect to API"

**Possible causes:**

1. **API not running**
   - Start the roster API server
   - Check: `curl http://localhost:8000/health`

2. **Wrong API URL**
   - Verify `ROSTER_API_BASE_URL` in `.env`
   - Should not have trailing slash

3. **Network issues**
   - Check firewall settings
   - Verify API is accessible

**Solution:**

```bash
# Check API is running
curl http://localhost:8000/api/events

# Test with correct URL
ROSTER_API_BASE_URL=http://localhost:8000 python scripts/run_scheduler_once.py
```

### Error: "No roster files found"

**Possible causes:**

1. **Writing disabled**
   - Check `WRITE_ROSTER_JSON=true` in `.env`

2. **Permission error**
   - Check write permissions for `roster-json/` directory

3. **Generation failed**
   - Check logs for errors
   - Verify API is returning data

**Solution:**

```bash
# Enable writing
echo "WRITE_ROSTER_JSON=true" >> .env

# Check directory permissions
ls -ld roster-json/
chmod 755 roster-json/

# Run with debug logging
LOG_LEVEL=DEBUG python scripts/run_scheduler_once.py
```

### Error: "JSON serialization error"

**Cause:** Data contains non-serializable objects (e.g., datetime objects)

**Solution:**

Check the error log for details. The orchestrator should return JSON-serializable data. If you see datetime objects, they need to be converted to ISO format strings.

### Error: "API key not configured"

**Solution:**

Some APIs require authentication. Set in `.env`:

```bash
ROSTER_API_KEY=your_api_key_here
```

### Logs Not Appearing

**Check log configuration:**

```bash
# View log file location
grep LOG_FILE .env

# Create log directory
mkdir -p logs

# Run with console logging
LOG_FILE= python scripts/run_scheduler_once.py
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ROSTER_API_BASE_URL` | API endpoint URL | `http://localhost:8000` | Yes |
| `ROSTER_API_KEY` | API authentication key | None | No |
| `WRITE_ROSTER_JSON` | Enable JSON file writing | `true` | No |
| `ROSTER_OUTPUT_DIR` | Output directory path | `roster-json` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FILE` | Log file path | None | No |
| `HISTORICAL_MONTHS` | Months of history to analyze | `3` | No |
| `FUTURE_MONTHS` | Months to generate | `3` | No |
| `DRY_RUN` | Dry run mode (no changes) | `false` | No |

### Log Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

## Testing Workflow

### 1. Initial Test

```bash
# Run with defaults
python scripts/run_scheduler_once.py

# Verify output
ls roster-json/
```

### 2. Test Different Configurations

```bash
# Test with different months
HISTORICAL_MONTHS=6 FUTURE_MONTHS=1 python scripts/run_scheduler_once.py

# Test dry run
python scripts/run_scheduler_once.py --dry-run

# Test without file writing
WRITE_ROSTER_JSON=false python scripts/run_scheduler_once.py
```

### 3. Verify Data Quality

```bash
# Check latest roster
LATEST=$(ls -t roster-json/*.json | head -1)

# Count rosters
cat $LATEST | jq '.rosters | length'

# Check validation
cat $LATEST | jq '.validation.is_valid'

# View errors/warnings
cat $LATEST | jq '.validation.errors'
cat $LATEST | jq '.validation.warnings'
```

## Integration with Development

### Git Workflow

The `.env` file is gitignored, so you can safely configure local settings without affecting others:

```bash
# Your local configuration
vi .env

# Not tracked by git
git status  # .env won't appear
```

### Team Setup

Share configuration template:

```bash
# Team member updates template
vi .env.example

# Commit changes
git add .env.example
git commit -m "docs: update configuration template"
```

### CI/CD

For automated testing, set environment variables directly:

```bash
# In CI pipeline
export ROSTER_API_BASE_URL=http://test-api:8000
export WRITE_ROSTER_JSON=true
python scripts/run_scheduler_once.py
```

## Next Steps

After verifying the scheduler works locally:

1. **Integrate with API** - Connect to real roster API
2. **Add AI Analysis** - Configure AI API for intelligent suggestions
3. **Schedule Automatically** - Set up cron job or systemd timer
4. **Monitor Output** - Set up log monitoring
5. **Production Deploy** - Deploy with production configuration

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review logs in `logs/roster.log`
3. Run with `LOG_LEVEL=DEBUG` for detailed output
4. Check GitHub issues: https://github.com/yhua045/roster-mcp/issues
5. Ask in team chat or create new issue
