#!/usr/bin/env python3
"""
Helper script to run the scheduler once for manual testing.

This script:
1. Loads configuration from environment variables
2. Creates required service instances
3. Runs the scheduler's roster generation once
4. Writes output to roster-json/ directory
5. Exits with appropriate status code

Usage:
    python scripts/run_scheduler_once.py

    # With custom .env file
    python scripts/run_scheduler_once.py --env-file .env.local

Requirements:
    - Copy .env.example to .env and configure
    - Install dependencies: pip install -r requirements.txt
    - Set up API credentials in .env file
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.config.settings import Settings
from src.services.scheduler import SchedulerService
from src.services.roster_orchestrator import RosterOrchestrator
from src.services.roster_data_agent import RosterDataAgent
from src.services.ai_analyzer import AIAnalyzer
from src.services.roster_api_client import RosterAPIClient


def setup_logging(settings: Settings):
    """Configure logging based on settings"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # If log file is specified, add file handler
    if settings.log_file:
        log_dir = Path(settings.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)


def create_orchestrator(settings: Settings) -> RosterOrchestrator:
    """
    Create orchestrator with real service instances.

    Requires:
        - ROSTER_API_BASE_URL: API endpoint
        - ROSTER_API_KEY: API authentication key (optional)
        - AI_API_KEY: AI service API key (optional)
    """
    logger = logging.getLogger(__name__)

    logger.info("Creating service instances...")

    # Create API client
    api_client = RosterAPIClient(
        base_url=settings.api_base_url,
        api_key=settings.api_key
    )
    logger.info(f"  ✓ API Client: {settings.api_base_url}")

    # Create data agent
    data_agent = RosterDataAgent(api_client)
    logger.info("  ✓ Roster Data Agent")

    # Create AI analyzer
    analyzer = AIAnalyzer(api_client=api_client)
    logger.info("  ✓ AI Analyzer")

    # Create orchestrator
    orchestrator = RosterOrchestrator(data_agent, analyzer)
    logger.info("  ✓ Roster Orchestrator")

    return orchestrator


def run_once(settings: Settings) -> int:
    """
    Run the scheduler once and generate rosters.

    Returns:
        0 on success, non-zero on error
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 60)
        logger.info("Starting one-time roster generation")
        logger.info("=" * 60)

        # Log configuration
        logger.info(f"\nConfiguration:")
        logger.info(f"  API Base URL: {settings.api_base_url}")
        logger.info(f"  Write JSON: {settings.write_roster_json}")
        logger.info(f"  Output Directory: {settings.roster_output_dir}")
        logger.info(f"  Historical Months: {settings.historical_months}")
        logger.info(f"  Future Months: {settings.future_months}")
        logger.info(f"  Dry Run Mode: {settings.dry_run_mode}")

        # Create orchestrator
        logger.info("\nInitializing components...")
        orchestrator = create_orchestrator(settings)

        # Create scheduler
        logger.info("\nCreating scheduler...")
        scheduler = SchedulerService(settings)

        # Run roster generation once
        logger.info("\nRunning roster generation...")
        logger.info("-" * 60)
        scheduler.run_roster_generation(orchestrator=orchestrator)
        logger.info("-" * 60)

        # Check output
        if settings.write_roster_json:
            roster_dir = Path(settings.roster_output_dir)
            if roster_dir.exists():
                files = sorted(roster_dir.glob("roster-*.json"))
                if files:
                    logger.info(f"\n✓ SUCCESS! Found {len(files)} roster file(s):")
                    for f in files[-3:]:  # Show last 3 files
                        logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

                    # Show the latest file path
                    latest = files[-1]
                    logger.info(f"\nLatest file: {latest.absolute()}")
                    logger.info(f"To view: cat {latest}")
                else:
                    logger.warning(f"\n⚠ No roster files found in {roster_dir}/")
                    logger.warning("Check if WRITE_ROSTER_JSON=true in your .env")
            else:
                logger.warning(f"\n⚠ Output directory {roster_dir}/ doesn't exist")
        else:
            logger.info("\n✓ Roster generation completed")
            logger.info("  (File writing disabled - set WRITE_ROSTER_JSON=true to save)")

        logger.info("\n" + "=" * 60)
        logger.info("One-time roster generation completed successfully!")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n\n✗ ERROR: {e}", exc_info=True)
        logger.error("\nRoster generation failed!")
        logger.error("=" * 60)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run roster scheduler once for manual testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with .env file
  python scripts/run_scheduler_once.py

  # Run with custom env file
  python scripts/run_scheduler_once.py --env-file .env.local

  # Run with environment variables
  WRITE_ROSTER_JSON=true LOG_LEVEL=DEBUG python scripts/run_scheduler_once.py

Output:
  Generated rosters will be written to roster-json/ directory
  (if WRITE_ROSTER_JSON=true in your configuration)

Requirements:
  - Valid ROSTER_API_BASE_URL in .env
  - API should be accessible and returning data
  - Optional: AI_API_KEY for AI-powered analysis
        """
    )

    parser.add_argument(
        '--env-file',
        default='.env',
        help='Path to environment file (default: .env)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no actual changes)'
    )

    args = parser.parse_args()

    # Load environment variables
    env_file = Path(args.env_file)
    if env_file.exists():
        print(f"Loading configuration from: {env_file}")
        load_dotenv(env_file)
    else:
        print(f"Note: {env_file} not found, using environment variables and defaults")

    # Override dry-run if specified
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'

    # Load settings
    settings = Settings()

    # Setup logging
    setup_logging(settings)

    # Run once
    exit_code = run_once(settings)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
