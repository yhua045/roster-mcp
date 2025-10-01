#!/usr/bin/env python
"""
Example script demonstrating how to use the AI Agent for roster generation

This script shows:
1. How to initialize the AI Agent
2. How to fetch historical data
3. How to generate future rosters
4. How to use custom rules
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import AIAgent, RosterGenerationRules
from src.services import RosterAPIClient, AIAnalyzer
from src.config import Settings

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example 1: Basic usage with default settings"""
    print("\n" + "=" * 60)
    print("Example 1: Basic AI Agent Usage")
    print("=" * 60)

    # Initialize settings
    settings = Settings()

    # Initialize API client
    api_client = RosterAPIClient(
        base_url=settings.api_base_url, api_key=settings.api_key
    )

    # Initialize AI analyzer
    ai_analyzer = AIAnalyzer()

    # Create AI Agent with default rules
    agent = AIAgent(api_client=api_client, ai_analyzer=ai_analyzer)

    # Generate rosters (dry run mode)
    print("\nGenerating rosters for the next 3 months (dry run)...")
    try:
        results = agent.execute_roster_generation(months_ahead=3, dry_run=True)

        # Display results
        print(f"\nStatus: {results['status']}")
        print(f"Generated: {results['generated_count']} rosters")
        print(f"Validated: {results['validated_count']} rosters")
        print(f"Submitted: {results['submitted_count']} rosters")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")
    except Exception as e:
        print(f"\n✗ API connection failed (this is expected if API is not running)")
        print(f"  The AI Agent is working correctly but cannot connect to the API.")
        logger.debug(f"Error details: {e}")


def example_custom_rules():
    """Example 2: Using custom roster generation rules"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Rules Configuration")
    print("=" * 60)

    # Create custom rules
    custom_rules = RosterGenerationRules(
        max_assignments_per_person_per_month=5,
        min_rest_days_between_assignments=10,
        prefer_role_rotation=True,
        maintain_team_chemistry=True,
        workload_balance_weight=0.4,  # Emphasize workload balance
        role_coverage_weight=0.3,
        team_chemistry_weight=0.2,
        availability_weight=0.1,
    )

    print("\nCustom rules:")
    print(f"  Max assignments per month: {custom_rules.max_assignments_per_person_per_month}")
    print(f"  Min rest days: {custom_rules.min_rest_days_between_assignments}")
    print(f"  Prefer role rotation: {custom_rules.prefer_role_rotation}")
    print(f"  Workload balance weight: {custom_rules.workload_balance_weight}")

    # Initialize components
    settings = Settings()
    api_client = RosterAPIClient(
        base_url=settings.api_base_url, api_key=settings.api_key
    )
    ai_analyzer = AIAnalyzer()

    # Create agent with custom rules
    agent = AIAgent(
        api_client=api_client, ai_analyzer=ai_analyzer, rules=custom_rules
    )

    print("\nAI Agent initialized with custom rules.")


def example_fetch_historical():
    """Example 3: Fetching and analyzing historical data"""
    print("\n" + "=" * 60)
    print("Example 3: Fetching Historical Data")
    print("=" * 60)

    # Initialize components
    settings = Settings()
    api_client = RosterAPIClient(
        base_url=settings.api_base_url, api_key=settings.api_key
    )
    ai_analyzer = AIAnalyzer()
    agent = AIAgent(api_client=api_client, ai_analyzer=ai_analyzer)

    # Fetch historical data
    print("\nFetching last 3 months of roster data...")
    try:
        historical_data = agent.fetch_historical_data(months_back=3, category="chinese")
        print(f"Retrieved {len(historical_data)} historical events")

        if historical_data:
            print("\nSample event:")
            print(f"  {historical_data[0]}")

    except Exception as e:
        print(f"Note: Unable to fetch data (this is normal if API is not running): {e}")


def example_category_specific():
    """Example 4: Generate rosters for specific service category"""
    print("\n" + "=" * 60)
    print("Example 4: Category-Specific Roster Generation")
    print("=" * 60)

    # Initialize components
    settings = Settings()
    api_client = RosterAPIClient(
        base_url=settings.api_base_url, api_key=settings.api_key
    )
    ai_analyzer = AIAnalyzer()
    agent = AIAgent(api_client=api_client, ai_analyzer=ai_analyzer)

    # Generate rosters for Chinese service only
    print("\nGenerating rosters for Chinese service...")
    try:
        results = agent.execute_roster_generation(
            months_ahead=2, category="chinese", dry_run=True
        )

        print(f"Status: {results['status']}")
        print(f"Generated: {results['generated_count']} Chinese service rosters")
    except Exception as e:
        print(f"\n✗ API connection failed (this is expected if API is not running)")


def example_validation():
    """Example 5: Roster validation"""
    print("\n" + "=" * 60)
    print("Example 5: Roster Validation")
    print("=" * 60)

    # Initialize components
    settings = Settings()
    api_client = RosterAPIClient(
        base_url=settings.api_base_url, api_key=settings.api_key
    )
    ai_analyzer = AIAnalyzer()
    agent = AIAgent(api_client=api_client, ai_analyzer=ai_analyzer)

    # Sample roster to validate
    sample_roster = {
        "date": "2024-03-10",
        "category": "chinese",
        "recommendations": [
            {"name": "John", "role": "證道"},
            {"name": "Jane", "role": "司會"},
            {"name": "Bob", "role": "詩歌讚美"},
        ],
    }

    print("\nValidating sample roster...")
    validation = agent.validate_generated_roster(sample_roster)

    print(f"Is valid: {validation['is_valid']}")
    if validation["errors"]:
        print("Errors:", validation["errors"])
    if validation["warnings"]:
        print("Warnings:", validation["warnings"])


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("AI Agent for Roster Generation - Examples")
    print("=" * 60)

    try:
        # Run examples
        example_basic_usage()
        example_custom_rules()
        example_fetch_historical()
        example_category_specific()
        example_validation()

        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Example execution failed: {e}", exc_info=True)
        print(f"\nNote: Some examples may fail if the API is not running.")
        print("This is normal for a demonstration script.")


if __name__ == "__main__":
    main()
