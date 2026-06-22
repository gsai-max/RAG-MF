import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.app.ingestion.run import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("scheduler")

# Indian Standard Time (IST) is UTC +5:30
IST = timezone(timedelta(hours=5, minutes=30))

def get_next_run_time(now_ist: datetime, target_hour: int = 9, target_minute: int = 15) -> datetime:
    """Calculate the next occurrence of target_hour:target_minute in IST."""
    target = now_ist.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if now_ist >= target:
        target += timedelta(days=1)
    return target

def start_scheduler(target_hour: int = 9, target_minute: int = 15):
    """Run the scheduler background loop checking every 10 seconds."""
    logger.info(f"Starting scheduler. Target run time: {target_hour:02d}:{target_minute:02d} AM IST daily.")
    
    # Calculate the first run
    now = datetime.now(IST)
    next_run = get_next_run_time(now, target_hour, target_minute)
    logger.info(f"Next ingestion scheduled at: {next_run.strftime('%Y-%m-%d %I:%M:%S %p')} IST")
    
    while True:
        try:
            time.sleep(10)
            now = datetime.now(IST)
            if now >= next_run:
                logger.info("Scheduler target time reached. Initiating ingestion pipeline run...")
                
                # Advance target before running to prevent overlapping triggers
                next_run = get_next_run_time(now + timedelta(minutes=1), target_hour, target_minute)
                
                success = run_ingestion(force=True)
                if success:
                    logger.info("Daily ingestion pipeline completed successfully.")
                else:
                    logger.error("Daily ingestion pipeline failed.")
                
                logger.info(f"Next ingestion scheduled at: {next_run.strftime('%Y-%m-%d %I:%M:%S %p')} IST")
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in scheduler execution loop: {e}", exc_info=True)
            # Sleep a bit longer on error to prevent CPU thrashing
            time.sleep(30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mutual Fund FAQ Ingestion Daily Scheduler")
    parser.add_argument("--now", action="store_true", help="Trigger ingestion run immediately once and exit")
    parser.add_argument("--hour", type=int, default=9, help="Hour to run daily (0-23)")
    parser.add_argument("--minute", type=int, default=15, help="Minute to run daily (0-59)")
    parser.add_argument("--limit", type=int, help="Limit number of schemes to process for debugging")
    parser.add_argument("--force", action="store_true", help="Force fetching fresh content instead of using cache")
    args = parser.parse_args()

    if args.now:
        logger.info(f"Forced immediate ingestion run initiated via CLI flag (limit={args.limit}, force={args.force})...")
        success = run_ingestion(limit=args.limit, force=args.force)
        sys.exit(0 if success else 1)
    else:
        start_scheduler(target_hour=args.hour, target_minute=args.minute)
