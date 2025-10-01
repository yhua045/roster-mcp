# Examples

This directory contains example scripts demonstrating how to use the Roster MCP system.

## AI Agent Demo

**File:** `ai_agent_demo.py`

Demonstrates the AI Agent functionality for roster generation:

1. **Basic Usage**: Initialize and use the AI Agent with default settings
2. **Custom Rules**: Configure custom roster generation rules
3. **Historical Data**: Fetch and analyze historical roster data
4. **Category-Specific**: Generate rosters for specific service categories
5. **Validation**: Validate roster assignments

### Running the Examples

```bash
# Make sure you're in the project root
cd roster-mcp

# Run the demo script
python examples/ai_agent_demo.py
```

**Note:** Some examples may show errors if the API is not running. This is expected behavior for demonstration purposes.

### Example Output

```
============================================================
AI Agent for Roster Generation - Examples
============================================================

============================================================
Example 1: Basic AI Agent Usage
============================================================

Generating rosters for the next 3 months (dry run)...

Status: success
Generated: 12 rosters
Validated: 12 rosters
Submitted: 0 rosters
```

## Requirements

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Configuration

The examples use environment variables from `.env` or default values. To customize:

1. Copy `.env.example` to `.env`
2. Update the configuration values
3. Run the examples

## Adding New Examples

To add a new example:

1. Create a new Python file in this directory
2. Follow the naming convention: `<feature>_demo.py`
3. Include docstrings explaining what the example demonstrates
4. Update this README with information about your example
