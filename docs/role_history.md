# Role History Feature

## Overview

The Role History feature tracks which members have historically performed each role in the roster system. This data is critical for the AI Agent when determining who is eligible for a specific role assignment.

## Architecture

### Database Schema

The `role_history` table stores the historical role assignments:

```sql
CREATE TABLE role_history (
    role_name TEXT PRIMARY KEY,           -- Normalized role name (lowercase, trimmed)
    member_ids TEXT NOT NULL,             -- JSON array of member names
    last_updated TIMESTAMP,               -- Last time this role history was updated
    created_at TIMESTAMP                  -- Initial creation timestamp
);
```

**Note:** Role names are normalized to lowercase and trimmed for consistent lookups.

### Key Components

#### 1. `compute_role_history(events, lookback_months=None)`
Analyzes historical events and builds a role → members mapping.

**Input:**
- `events`: List of event dictionaries with members and roles
- `lookback_months`: Optional window to limit how far back to analyze

**Output:**
- Dictionary mapping role names (normalized) to sets of member names

**Example:**
```python
analyzer = AIAnalyzer()
events = [
    {
        "date": "2024-01-01",
        "members": [
            {"name": "張三", "role": "證道"},
            {"name": "李四", "role": "司會"}
        ]
    }
]
role_history = analyzer.compute_role_history(events)
# Returns: {"證道": {"張三"}, "司會": {"李四"}}
```

#### 2. `persist_role_history(role_history)`
Saves the computed role history to the database.

**Input:**
- `role_history`: Dictionary from `compute_role_history`

**Side Effects:**
- Updates or inserts role history records in database
- Sets `last_updated` timestamp to current UTC time

#### 3. `get_eligible_members_for_role(role_name, all_members=None)`
Retrieves members who are eligible for a specific role based on historical assignments.

**Input:**
- `role_name`: Name of the role to query
- `all_members`: Optional fallback list if no history exists

**Output:**
- Sorted list of member names who have performed this role

**Fallback Behavior:**
- If role history exists → returns members with experience in that role
- If no history but `all_members` provided → returns all members
- If no history and no fallback → returns empty list

**Example:**
```python
# With history
eligible = analyzer.get_eligible_members_for_role("證道")
# Returns: ['張三', '李四', '王五']

# Without history (fallback)
eligible = analyzer.get_eligible_members_for_role(
    "新角色",
    all_members=["張三", "李四"]
)
# Returns: ['張三', '李四']
```

#### 4. `recompute_role_history(events, lookback_months=None)`
Orchestration function that computes and persists role history in one call.

**Usage:**
```python
analyzer = AIAnalyzer()
events = fetch_all_events()  # Your data source
role_history = analyzer.recompute_role_history(events, lookback_months=12)
```

This is the **main function** you should call to refresh role history data.

## Integration Guide

### Initial Setup

1. **Run Database Migration**
   ```bash
   # Apply the migration to create the role_history table
   sqlite3 roster.db < migrations/002_role_history.sql
   ```

2. **Initial Data Population**
   ```python
   from src.services.ai_analyzer import AIAnalyzer

   # Initialize analyzer
   analyzer = AIAnalyzer(db_path='path/to/roster.db')

   # Fetch your events (from API or database)
   events = fetch_all_events()

   # Compute and persist role history
   analyzer.recompute_role_history(events)
   ```

### Scheduled Recomputation

Role history should be recomputed periodically (recommended: **monthly**) to keep data current.

**Example with APScheduler:**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.ai_analyzer import AIAnalyzer

def recompute_job():
    analyzer = AIAnalyzer()
    events = fetch_all_events()
    analyzer.recompute_role_history(events, lookback_months=12)
    print("Role history updated")

# Schedule monthly recomputation (1st of each month at 2 AM)
scheduler = BackgroundScheduler()
scheduler.add_job(recompute_job, 'cron', day=1, hour=2)
scheduler.start()
```

### Using Role History in AI Agent

When the AI Agent needs to assign roles, it can query eligible members:

```python
from src.services.ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer()

# Get members who have performed "證道" role before
eligible_speakers = analyzer.get_eligible_members_for_role("證道")

# Get members for a new role with fallback
all_available = ["張三", "李四", "王五", "趙六"]
eligible = analyzer.get_eligible_members_for_role(
    "翻譯",
    all_members=all_available
)
```

## Configuration

### Database Path
By default, the analyzer uses `roster.db` in the current working directory. You can specify a custom path:

```python
analyzer = AIAnalyzer(db_path='/path/to/custom.db')
```

### Lookback Window
Control how far back to analyze events:

```python
# Last 12 months only
analyzer.recompute_role_history(events, lookback_months=12)

# All history (default)
analyzer.recompute_role_history(events)
```

**Recommendation:** Use `lookback_months=12` for most cases to balance data freshness with performance.

## Data Normalization

### Role Names
Role names are automatically normalized to ensure consistent lookups:
- **Lowercase:** "Speaker" → "speaker"
- **Trimmed:** "  證道  " → "證道"

This means lookups are case-insensitive:
```python
analyzer.get_eligible_members_for_role("證道")  # Works
analyzer.get_eligible_members_for_role("證道")  # Also works
```

### Member Names
Member names are stored as-is (case-sensitive) to preserve original formatting.

## Edge Cases

### Repeated Assignments
If a member performs the same role multiple times, they appear only once in the history:
```python
events = [
    {"date": "2024-01-01", "members": [{"name": "張三", "role": "證道"}]},
    {"date": "2024-01-08", "members": [{"name": "張三", "role": "證道"}]},
    {"date": "2024-01-15", "members": [{"name": "張三", "role": "證道"}]}
]
role_history = analyzer.compute_role_history(events)
# Returns: {"證道": {"張三"}}  (not 3 entries)
```

### Missing Data
- **Missing role:** Member is skipped (logged as debug)
- **Missing name:** Assignment is skipped (logged as debug)
- **Invalid date:** Event is skipped if using lookback window (logged as warning)

### Empty Results
- **Empty events list:** Returns empty dictionary `{}`
- **No history for role:** Returns `None` from `get_role_history_from_db`
- **No eligible members:** Returns empty list `[]` from `get_eligible_members_for_role`

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_services/test_ai_analyzer.py -v
```

Tests cover:
- Role name normalization (case, whitespace)
- Historical computation with various edge cases
- Database persistence and retrieval
- Lookback window filtering
- Unicode support (Chinese characters)
- End-to-end workflows

## Performance Considerations

### Database Size
The `role_history` table is typically small (one row per unique role). Even with hundreds of roles, the table remains lightweight.

### Computation Time
- **Initial computation:** O(n × m) where n = events, m = avg members per event
- **Database persistence:** O(r) where r = unique roles

For typical datasets (thousands of events), computation completes in milliseconds.

### Caching
Role history is persisted in the database, so repeated queries are fast (single DB lookup per role).

## Future Enhancements

Potential improvements for production use:

1. **Person ID Support:** Use stable `person_id` instead of names for member identification
2. **Role History Versioning:** Track changes over time with historical snapshots
3. **Analytics Dashboard:** Visualize role distribution and member participation trends
4. **Smart Recommendations:** Use role history to suggest optimal assignments
5. **Access Control:** Add authentication/authorization for role history management
6. **Performance Monitoring:** Add metrics and logging for recomputation jobs

## Troubleshooting

### "No eligible members found"
**Cause:** No historical data exists for the role.
**Solution:**
1. Check if role name is correct (remember: normalized to lowercase)
2. Ensure `recompute_role_history` has been run
3. Provide `all_members` fallback parameter

### "Database is locked"
**Cause:** Concurrent access to SQLite database.
**Solution:**
1. Ensure only one recomputation job runs at a time
2. Consider using connection pooling or write-ahead logging (WAL mode)

### "Role history not updating"
**Cause:** `recompute_role_history` not being called.
**Solution:**
1. Verify scheduled job is running
2. Check logs for errors during recomputation
3. Manually trigger: `analyzer.recompute_role_history(events)`

## API Reference

See inline docstrings in `src/services/ai_analyzer.py` for detailed API documentation.

Key methods:
- `AIAnalyzer.__init__(ai_client=None, db_path=None)`
- `AIAnalyzer.compute_role_history(events, lookback_months=None)`
- `AIAnalyzer.persist_role_history(role_history)`
- `AIAnalyzer.get_role_history_from_db(role_name)`
- `AIAnalyzer.get_eligible_members_for_role(role_name, all_members=None)`
- `AIAnalyzer.recompute_role_history(events, lookback_months=None)`
