#!/usr/bin/env python3
"""
Daily database update script for the Shroff Premier League.
This script should be scheduled to run daily (e.g., at 1 AM) to:
1. Fetch and process match data from the previous day
2. Update player statistics and fantasy points
3. Handle any auction/team management operations if needed

Can be executed directly or as a scheduled task on Render.
"""
import os
import sys
from pathlib import Path
import logging
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("daily_update")

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import required modules
try:
    from database import SessionLocal, Match, Player, Shroff_teams, TeamPlayer
    from ppdb import fetch_match_data, process_match_data, populate_database, df
    from auction_manager import populate_auction_data
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


def get_yesterdays_match():
    """Get match data for yesterday's date from Match_data.csv"""
    yesterday = datetime.now().date() - timedelta(days=1)
    logger.info(f"Looking for matches played on {yesterday}")
    
    matches = df[df["date"] == yesterday][["id", "date"]].to_dict('records')
    logger.info(f"Found {len(matches)} matches for {yesterday}")
    return matches


def process_match(match_id):
    """Process a single match and update the database"""
    logger.info(f"Processing match ID: {match_id}")
    
    # Check if match already exists in database
    db = SessionLocal()
    try:
        existing = db.query(Match).filter(Match.match_id == match_id).first()
        if existing:
            logger.info(f"Match {match_id} already exists in database, skipping")
            return False
            
        # Fetch match data
        match_data = fetch_match_data(match_id)
        if match_data.get("status") == "error":
            logger.error(f"Error fetching match {match_id}: {match_data.get('message')}")
            return False
            
        # Populate database with match data
        result = populate_database(match_data)
        if result:
            logger.info(f"Successfully processed match {match_id}")
            return True
        else:
            logger.error(f"Failed to process match {match_id}")
            return False
    except Exception as e:
        logger.error(f"Error during match processing: {e}")
        return False
    finally:
        db.close()


def ensure_teams_initialized():
    """Ensure all Shroff teams are initialized in the database"""
    db = SessionLocal()
    try:
        teams_count = db.query(Shroff_teams).count()
        if teams_count == 0:
            logger.info("No teams found in database. Initializing Shroff teams.")
            from ppdb import populate_database
            # Create a mock match data structure just to initialize teams
            mock_data = {"status": "success", "data": {"id": "init", "name": "Init", 
                        "date": datetime.now().strftime("%Y-%m-%d"), 
                        "venue": "Init", "teams": ["Init1", "Init2"],
                        "scorecard": []}}
            populate_database(mock_data)
            logger.info("Teams initialized successfully")
        else:
            logger.info(f"Found {teams_count} teams in database")
        return teams_count > 0
    except Exception as e:
        logger.error(f"Error ensuring teams are initialized: {e}")
        return False
    finally:
        db.close()


def ensure_auction_data_populated():
    """Check if auction data has been populated, and populate if needed"""
    db = SessionLocal()
    try:
        # Check if TeamPlayer records exist (sign of auction being populated)
        player_count = db.query(TeamPlayer).count()
        if player_count == 0:
            logger.info("No team players found. Populating auction data.")
            # Close the current session and run auction manager's populate function
            db.close()
            auction_db = SessionLocal()
            try:
                # Import and run the auction data population
                populate_auction_data(auction_db)
                logger.info("Auction data populated successfully")
                return True
            except Exception as e:
                logger.error(f"Error populating auction data: {e}")
                return False
            finally:
                auction_db.close()
        else:
            logger.info(f"Found {player_count} team player records, auction data already populated")
            return True
    except Exception as e:
        logger.error(f"Error checking auction data: {e}")
        return False
    finally:
        db.close()


def run_daily_update():
    """Main function to run all daily update operations"""
    logger.info("Starting daily database update")
    start_time = time.time()
    
    # Step 1: Ensure teams are initialized
    if not ensure_teams_initialized():
        logger.warning("Failed to initialize teams, continuing anyway")
    
    # Step 2: Ensure auction data is populated
    if not ensure_auction_data_populated():
        logger.warning("Failed to populate auction data, continuing anyway")
    
    # Step 3: Process yesterday's matches
    matches = get_yesterdays_match()
    processed = 0
    
    for match in matches:
        match_id = str(match['id'])
        match_date = match['date']
        logger.info(f"Processing match {match_id} from {match_date}")
        
        if process_match(match_id):
            processed += 1
            # Add a small delay between API calls
            if len(matches) > 1:
                time.sleep(2)
    
    # Complete
    elapsed_time = time.time() - start_time
    logger.info(f"Daily update completed in {elapsed_time:.2f} seconds")
    logger.info(f"Processed {processed}/{len(matches)} matches")
    
    return processed


if __name__ == "__main__":
    try:
        run_daily_update()
    except Exception as e:
        logger.error(f"Unexpected error in daily update: {e}")
        sys.exit(1)