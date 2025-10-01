# AI Agent for Roster Generation

## Overview

The AI Agent is the core component responsible for automated roster generation. It orchestrates the entire process of analyzing historical data and generating optimal rosters for future services.

## Architecture

```
AIAgent
  ├── RosterAPIClient (fetches data from API)
  ├── AIAnalyzer (analyzes patterns and generates recommendations)
  └── RosterGenerationRules (configurable rules and constraints)
```

## Job Description

The AI Agent performs the following responsibilities:

1. **Data Collection**: Retrieves the last 3 months of roster data from the API
2. **Pattern Analysis**: Identifies trends, workload distribution, and team dynamics
3. **Roster Generation**: Creates balanced rosters for the next 3 months
4. **Validation**: Ensures generated rosters meet all requirements and constraints
5. **Submission**: Submits approved rosters back to the system (optional)

### Key Responsibilities

- Maintain fair workload distribution across all team members
- Ensure adequate role coverage for all services
- Preserve successful team combinations and chemistry
- Respect member availability and preferences
- Optimize for service quality and team satisfaction
- Handle conflicts and constraints gracefully

## Configuration

### Environment Variables

Configure the AI Agent behavior through environment variables:

```bash
# Historical data period
HISTORICAL_MONTHS=3

# Future roster generation period
FUTURE_MONTHS=3

# Workload rules
MAX_ASSIGNMENTS_PER_MONTH=4
MIN_REST_DAYS=7
PREFER_ROLE_ROTATION=true

# Operation modes
DRY_RUN=false
AUTO_APPROVE=false
```

### Rules Configuration

The AI Agent follows configurable rules defined in `config/roster_rules.yaml`:

```yaml
# Workload Balancing
max_assignments_per_month: 4
min_rest_days: 7

# Role Distribution
prefer_role_rotation: true
allow_multiple_roles_same_day: false

# Team Composition
maintain_team_chemistry: true
balance_experience_levels: true

# Decision Weights (must sum to 1.0)
workload_balance_weight: 0.3
role_coverage_weight: 0.3
team_chemistry_weight: 0.2
availability_weight: 0.2
```

## Usage

### Basic Usage

```python
from src.services import AIAgent, RosterGenerationRules
from src.services import RosterAPIClient, AIAnalyzer

# Initialize components
api_client = RosterAPIClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)
ai_analyzer = AIAnalyzer()

# Create AI Agent with default rules
agent = AIAgent(
    api_client=api_client,
    ai_analyzer=ai_analyzer
)

# Generate rosters
results = agent.execute_roster_generation(
    months_ahead=3,
    category="chinese",
    dry_run=True
)

print(f"Status: {results['status']}")
print(f"Generated: {results['generated_count']} rosters")
print(f"Validated: {results['validated_count']} rosters")
```

### Custom Rules

```python
# Create custom rules
custom_rules = RosterGenerationRules(
    max_assignments_per_person_per_month=5,
    min_rest_days_between_assignments=10,
    prefer_role_rotation=True,
    maintain_team_chemistry=True
)

# Create agent with custom rules
agent = AIAgent(
    api_client=api_client,
    ai_analyzer=ai_analyzer,
    rules=custom_rules
)
```

### Integration with Scheduler

The AI Agent is automatically integrated with the SchedulerService:

```python
from src.services import SchedulerService
from src.config import Settings

# Initialize with settings
settings = Settings()
scheduler = SchedulerService(settings)

# Run roster generation
results = scheduler.run_roster_generation()
```

## Methods

### `execute_roster_generation()`

Main entry point for generating rosters.

**Parameters:**
- `months_ahead` (int): Number of months to generate rosters for (default: 3)
- `category` (str, optional): Service category filter ('chinese', 'english', 'sundayschool')
- `dry_run` (bool): If True, validate without submitting to API (default: True)

**Returns:**
- Dictionary with generation results:
  ```python
  {
      "status": "success",
      "generated_count": 12,
      "validated_count": 12,
      "submitted_count": 0,
      "errors": [],
      "warnings": []
  }
  ```

### `fetch_historical_data()`

Retrieves historical roster data from the API.

**Parameters:**
- `months_back` (int): Number of months of historical data (default: 3)
- `category` (str, optional): Service category filter

**Returns:**
- List of historical event dictionaries

### `generate_future_rosters()`

Generates rosters for upcoming services.

**Parameters:**
- `months_ahead` (int): Number of months to generate rosters for (default: 3)
- `category` (str, optional): Service category filter
- `available_members` (list, optional): List of available members

**Returns:**
- List of generated roster assignments

### `validate_generated_roster()`

Validates a generated roster against rules.

**Parameters:**
- `roster` (dict): Roster to validate

**Returns:**
- Validation result dictionary:
  ```python
  {
      "is_valid": True,
      "errors": [],
      "warnings": []
  }
  ```

## Roster Generation Rules

### RosterGenerationRules Class

Configurable rules that guide roster generation:

**Workload Balancing:**
- `max_assignments_per_person_per_month`: Maximum assignments per person (default: 4)
- `min_rest_days_between_assignments`: Minimum rest days between assignments (default: 7)

**Role Distribution:**
- `prefer_role_rotation`: Rotate people through different roles (default: True)
- `allow_multiple_roles_same_day`: Allow multiple roles per person per day (default: False)

**Team Composition:**
- `maintain_team_chemistry`: Preserve successful team combinations (default: True)
- `balance_experience_levels`: Mix experienced and new members (default: True)

**Availability:**
- `respect_member_availability`: Honor member preferences (default: True)
- `require_minimum_team_size`: Minimum team size required (default: 3)

**Decision Weights:**
- `workload_balance_weight`: Weight for workload balancing (default: 0.3)
- `role_coverage_weight`: Weight for role coverage (default: 0.3)
- `team_chemistry_weight`: Weight for team chemistry (default: 0.2)
- `availability_weight`: Weight for availability (default: 0.2)

All weights must sum to 1.0.

## Error Handling

The AI Agent handles errors gracefully:

```python
try:
    results = agent.execute_roster_generation()
    
    if results["status"] == "failed":
        for error in results["errors"]:
            print(f"Error: {error}")
    
    for warning in results["warnings"]:
        print(f"Warning: {warning}")
        
except Exception as e:
    print(f"Fatal error: {e}")
```

## Dry Run Mode

Use dry run mode to test roster generation without submitting to the API:

```python
# Dry run - validate without submitting
results = agent.execute_roster_generation(dry_run=True)

# Check results before actual submission
if results["status"] == "success" and results["validated_count"] > 0:
    # Now run for real
    results = agent.execute_roster_generation(dry_run=False)
```

## Testing

Run AI Agent tests:

```bash
# Run all AI Agent tests
pytest tests/test_services/test_ai_agent.py -v

# Run specific test
pytest tests/test_services/test_ai_agent.py::TestAIAgent::test_execute_roster_generation_success -v
```

## Future Enhancements

Planned improvements for the AI Agent:

1. **Machine Learning Integration**: Use actual ML models for pattern recognition
2. **Member Availability API**: Integrate with availability tracking system
3. **Conflict Resolution**: Advanced logic for handling scheduling conflicts
4. **Performance Metrics**: Track and optimize roster performance over time
5. **Multi-service Optimization**: Optimize across multiple service types simultaneously
6. **Real-time Adjustments**: Dynamic roster updates based on last-minute changes

## See Also

- [AIAnalyzer Documentation](./ai_analyzer.md)
- [API Client Documentation](../api.md)
- [Configuration Guide](./configuration.md)
