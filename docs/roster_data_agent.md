# AI Agent Data Gathering

## Overview

The `AIAgent` module is responsible for gathering and preparing data for AI-powered roster generation. It collects historical roster data, evaluates member availability (placeholder), and builds structured payloads ready for AI consumption.

## Module Location

- **Implementation**: `src/services/ai_agent.py`
- **Tests**: `tests/test_services/test_ai_agent.py`

## Usage Example

```python
from src.services.roster_api_client import RosterAPIClient
from src.services.ai_agent import AIAgent

# Initialize the API client
api_client = RosterAPIClient(
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Create the AI Agent
agent = AIAgent(api_client)

# Step 1: Fetch last 3 months of historical events
events = agent.fetch_last_three_months(category='chinese')
print(f"Fetched {len(events)} events")

# Step 2: Extract members from events
members = []
for event in events:
    members.extend(event.get('members', []))

# Step 3: Evaluate availability (placeholder)
availability = agent.evaluate_availability_placeholder(members)

# Step 4: Build AI payload
payload = agent.build_ai_payload(
    historical_events=events,
    availability=availability,
    months_ahead=3,
    category='chinese'
)

# The payload is now ready to be sent to an AI API
import json
print(json.dumps(payload, indent=2))
```

## Key Methods

### `fetch_last_three_months(category: Optional[str] = None) -> List[Dict]`

Fetches roster events from the last 90 days using the `RosterAPIClient`.

**Parameters:**
- `category` (optional): Filter by service category ('chinese', 'english', 'sundayschool')

**Returns:**
- List of event dictionaries from the API

**Example:**
```python
# Fetch all events
events = agent.fetch_last_three_months()

# Fetch only Chinese service events
chinese_events = agent.fetch_last_three_months(category='chinese')
```

### `evaluate_availability_placeholder(members: List[Dict]) -> Dict[str, Any]`

**🚧 PLACEHOLDER METHOD - Replace with real availability logic**

Currently returns deterministic default availability (all members marked as available). This is where you should implement actual availability evaluation logic.

**Parameters:**
- `members`: List of member dictionaries (typically extracted from historical events)

**Returns:**
```python
{
    "status": "placeholder",
    "evaluation_date": "2024-01-15",
    "members": {
        "張三": {
            "available": True,
            "preferences": {},
            "constraints": [],
            "note": "Default availability - replace with actual logic"
        },
        "李四": {
            "available": True,
            "preferences": {},
            "constraints": [],
            "note": "Default availability - replace with actual logic"
        }
    }
}
```

**Future Implementation Points:**
1. **Member Preferences**: Retrieve from database or member profiles
2. **Historical Patterns**: Analyze past scheduling to identify preferences/constraints
3. **Conflict Detection**: Check for vacations, holidays, other commitments
4. **Role-Specific Availability**: Different roles may have different availability requirements
5. **Capacity Constraints**: Limit frequency (e.g., max 2 assignments per month)

**Example:**
```python
members = [
    {"name": "張三", "role": "證道"},
    {"name": "李四", "role": "司會"}
]

availability = agent.evaluate_availability_placeholder(members)
print(availability["status"])  # "placeholder"
```

### `build_ai_payload(historical_events, availability, months_ahead=3, category=None) -> Dict`

Builds a JSON-serializable payload combining historical data, availability, and generation parameters.

**Parameters:**
- `historical_events`: List of historical event dictionaries (from `fetch_last_three_months`)
- `availability`: Availability dictionary (from `evaluate_availability_placeholder`)
- `months_ahead` (optional): Number of months to generate rosters for (default: 3)
- `category` (optional): Service category for the roster generation

**Returns:**
See [Payload Structure](#payload-structure) below

**Example:**
```python
payload = agent.build_ai_payload(
    historical_events=events,
    availability=availability,
    months_ahead=3,
    category='chinese'
)

# Payload is JSON-serializable
import json
json_payload = json.dumps(payload)
```

## Payload Structure

The AI payload has the following structure:

```json
{
  "metadata": {
    "generation_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "category": "chinese",
    "date_range": {
      "from": "2024-01-15",
      "to": "2024-04-15"
    },
    "generated_at": "2024-01-15"
  },
  "historical_events": [
    {
      "id": 1,
      "date": "2023-11-01",
      "category": "chinese",
      "serviceInfo": {
        "id": 501,
        "category": "chinese",
        "footnote": ""
      },
      "members": [
        {
          "name": "張三",
          "role": "證道"
        },
        {
          "name": "李四",
          "role": "司會"
        }
      ]
    }
  ],
  "availability": {
    "status": "placeholder",
    "evaluation_date": "2024-01-15",
    "members": {
      "張三": {
        "available": true,
        "preferences": {},
        "constraints": []
      },
      "李四": {
        "available": true,
        "preferences": {},
        "constraints": []
      }
    }
  },
  "generation_params": {
    "months_ahead": 3,
    "strategy": "balanced",
    "note": "Default strategy - can be customized based on requirements"
  }
}
```

### Payload Fields

#### `metadata`
- `generation_request_id`: Unique UUID for this generation request
- `category`: Service category (if specified)
- `date_range`: Target date range for roster generation
  - `from`: Start date (today)
  - `to`: End date (today + months_ahead * 30 days)
- `generated_at`: Timestamp when payload was created

#### `historical_events`
- Array of event objects from the last 3 months
- Each event contains:
  - Event metadata (id, date, category)
  - Service information
  - Member assignments with roles

#### `availability`
- `status`: Currently "placeholder" - will change when real availability logic is implemented
- `evaluation_date`: Date when availability was evaluated
- `members`: Dictionary keyed by member name
  - `available`: Boolean indicating availability
  - `preferences`: Object for member preferences (future use)
  - `constraints`: Array of constraints (future use)

#### `generation_params`
- `months_ahead`: Number of months to generate
- `strategy`: Generation strategy (currently "balanced")
- Additional parameters can be added as needed

## Extending the AIAgent

### Implementing Real Availability Logic

Replace the `evaluate_availability_placeholder` method with actual availability evaluation:

```python
def evaluate_availability(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Real availability evaluation implementation
    """
    availability = {
        "status": "evaluated",
        "evaluation_date": date.today().isoformat(),
        "members": {}
    }

    for member in members:
        member_name = member.get("name")
        if not member_name:
            continue

        # TODO: Implement actual logic
        # - Query member preferences from database
        # - Check historical patterns
        # - Detect conflicts (vacations, etc.)
        # - Apply role-specific rules

        availability["members"][member_name] = {
            "available": self._check_availability(member_name),
            "preferences": self._get_preferences(member_name),
            "constraints": self._get_constraints(member_name)
        }

    return availability
```

### Adding Custom Generation Strategies

Extend `build_ai_payload` to support different generation strategies:

```python
def build_ai_payload(
    self,
    historical_events: List[Dict[str, Any]],
    availability: Dict[str, Any],
    months_ahead: int = 3,
    category: Optional[str] = None,
    strategy: str = "balanced"  # Add strategy parameter
) -> Dict[str, Any]:
    # ... existing code ...

    payload["generation_params"]["strategy"] = strategy

    # Add strategy-specific parameters
    if strategy == "minimize_workload":
        payload["generation_params"]["max_assignments_per_member"] = 2
    elif strategy == "maximize_variety":
        payload["generation_params"]["role_rotation"] = True

    return payload
```

## Testing

The module has comprehensive unit tests in `tests/test_services/test_ai_agent.py`:

```bash
# Run all AI Agent tests
pytest tests/test_services/test_ai_agent.py -v

# Run specific test class
pytest tests/test_services/test_ai_agent.py::TestBuildAIPayload -v

# Run with coverage
pytest tests/test_services/test_ai_agent.py --cov=src.services.ai_agent
```

### Test Coverage

- ✅ Initialization
- ✅ Fetching last 3 months with/without category
- ✅ Date range validation (exactly 90 days)
- ✅ Placeholder availability evaluation
- ✅ Deterministic output
- ✅ Duplicate member handling
- ✅ Payload structure validation
- ✅ JSON serializability
- ✅ Unique request IDs
- ✅ Date range calculations
- ✅ Error handling (API errors, invalid parameters)
- ✅ Full workflow integration

## Integration with RosterAPIClient

The `AIAgent` uses `RosterAPIClient` for all network operations:

```python
# AIAgent delegates to RosterAPIClient
events = agent.fetch_last_three_months(category='chinese')

# Internally calls:
# api_client.get_events(
#     category='chinese',
#     from_date=today - 90 days,
#     to_date=today
# )
```

This keeps the `AIAgent` focused on data preparation logic while the `RosterAPIClient` handles:
- HTTP requests
- Error handling
- Response validation
- Authentication

## Future Enhancements

1. **Availability Integration**
   - Connect to member availability database
   - Implement preference management
   - Add conflict detection

2. **Advanced Analytics**
   - Analyze historical patterns
   - Identify workload imbalances
   - Suggest optimal assignments

3. **Caching**
   - Cache historical data
   - Cache member availability
   - Invalidate on updates

4. **Multiple Strategies**
   - Load balancing strategy
   - Rotation strategy
   - Preference-based strategy

5. **Validation**
   - Validate payload structure
   - Check data completeness
   - Verify date ranges

## See Also

- [Domain Models](models.md) - Event, ServiceInfo, and Member models
- [API Documentation](api.md) - REST API endpoints
- `src/services/roster_api_client.py` - API client implementation
