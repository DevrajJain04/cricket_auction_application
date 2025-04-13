import os
import sys
from sqlalchemy.orm import Session
from decimal import Decimal, getcontext

# Set precision for Decimal operations if needed (default is usually sufficient)
# getcontext().prec = 28

# Add src directory to Python path to import database module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from database import engine, SessionLocal, Player, Shroff_teams, TeamPlayer
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print("Ensure database.py is in the same directory or src is in the Python path.")
    sys.exit(1)

# --- Auction Data ---

# Team name mapping
TEAM_MAP = {
    "SC": "Shroff Conquerers",
    "BB": "Bumrah Brigadiers",
    "SSSG": "Shroff Superwizards Supergiants Snakes", # Updated based on ppdb.py
    "RSS": "Rising Shroff Supergiants",
    "RCT": "Royal Challengers Thalasons",
    "LKF": "Lalu ki Fauj"
}

# Player data structure: {Team Abbreviation: [(Player Name, Price), ...]}
AUCTION_DATA = {
    "SC": [
        ("Nehal Wadhera", 4), ("Shreyas Iyer", 9), ("Virat Kohli", 19.5),
        ("Tristan Stubbs", 5), # Corrected name
        ("Manish Pandey", 1.5), ("Rohit Sharma", 7),
        ("Ravindra Jadeja", 6.5), ("Anshul Kamboj", 0.5), ("Liam Livingstone", 4.5),
        ("Angkrish Raghuvanshi", 3), ("Ravisrinivasan Sai Kishore", 1.5),
        ("Sameer Rizvi", 1.75), # Corrected name (trimmed space if any)
        ("Nicholas Pooran", 11), ("Ishan Kishan", 5),
        ("Kuldeep Sen", 2.25), ("Akash Madhwal", 2.25), ("Wanindu Hasaranga", 1),
        ("Jofra Archer", 6.5), # Name verified
        ("Mohsin Khan", 2), ("Rahul Chahar", 2), ("Kagiso Rabada", 5.25),
        ("Suyash Sharma", 1), ("Bhuvneshwar Kumar", 6.75), ("Josh Hazlewood", 5.5),
        ("Arshdeep Singh", 5.5)
    ],
    "BB": [
        ("Travis Head", 21), ("Rovman Powell", 2), ("Devdutt Padikkal", 2.25),
        ("Yashasvi Jaiswal", 11), ("Tilak Varma", 13), ("Glenn Phillips", 2),
        ("Rachin Ravindra", 3), ("Marco Jansen", 3), ("Washington Sundar", 3),
        ("Rahul Tewatia", 2.25), ("Abhishek Sharma", 7.5), ("Robin Minz", 1.5),
        ("Deepak Chahar", 7), ("Noor Ahmad", 1.25), ("Vaibhav Arora", 2),
        ("Arjun Tendulkar", 14.25), ("Yuzvendra Chahal", 9), ("Varun Chakaravarthy", 7.25),
        ("Maheesh Theekshana", 2), ("Ishant Sharma", 0.75), ("Mohammed Siraj", 5)
    ],
    "SSSG": [
        ("Sai Sudharsan", 8.75), # Corrected name
        ("Faf du Plessis", 2), ("Aiden Markram", 2),
        ("Suryakumar Yadav", 13.5), ("David Miller", 2.75), ("Shimron Hetmyer", 2.5),
        ("Harpreet Brar", 1.25), ("Nitish Kumar Reddy", 10.25), ("Hardik Pandya", 9.5),
        ("Shahbaz Ahmed", 1), ("Vijay Shankar", 0.5), ("Jos Buttler", 11.5),
        ("Vishnu Vinod", 0.5), ("Abishek Porel", 2.5), ("Heinrich Klaasen", 11.5),
        ("Dhruv Jurel", 4), ("Harshit Rana", 6.5), ("Karn Sharma", 0.75),
        ("Mayank Yadav", 3.75), ("Prasidh Krishna", 4.5), ("Pat Cummins", 8.25),
        ("Ravichandran Ashwin", 3.25), ("Avesh Khan", 2.25), ("Mukesh Kumar", 2.25),
        ("Sandeep Sharma", 4.25)
    ],
    "RSS": [
        ("Sachin Baby", 1.25), ("Deepak Hooda", 2.25), ("Ajinkya Rahane", 8),
        ("Ayush Badoni", 5.5),
        ("Ramandeep Singh", 3), # Corrected name (trimmed space if any)
        ("Vaibhav Suryavanshi", 1),
        ("Prabhsimran Singh", 3.25), # Corrected name (was Simran Singh)
        ("Rajat Patidar", 10.5), ("Venkatesh Iyer", 6.75), ("Marcus Stoinis", 4.75),
        ("Mitchell Santner", 1), ("Glenn Maxwell", 7), ("Will Jacks", 4.5),
        ("Abdul Samad", 0.5), ("Andre Russell", 6), ("Axar Patel", 6.5),
        ("Atharva Taide", 0.5), ("Anuj Rawat", 2.25), ("Rishabh Pant", 8.75),
        ("Matheesha Pathirana", 7.5), ("Rashid Khan", 10.5),
        ("Akash Deep", 3.75),
        ("Mohammed Shami", 8.25), # Corrected name
        ("Kuldeep Yadav", 5),
        ("Jaydev Unadkat", 1)
    ],
    "RCT": [
        ("Jake Fraser-McGurk", 9.25), # Corrected name
        ("Luvnith Sisodia", 0.5), ("Rinku Singh", 9), ("Riyan Parag", 5.5),
        ("Raj Bawa", 7.75), ("Sam Curran", 4.75), ("Swapnil Singh", 2),
        ("Harshal Patel", 5), ("Jacob Bethell", 0.75), ("Tim David", 1),
        ("Rajvardhan Hangargekar", 0.5), ("Mahipal Lomror", 2), ("Sunil Narine", 7.25),
        ("Jitesh Sharma", 4), ("Sanju Samson", 10.5), ("MS Dhoni", 3.75),
        ("T Natarajan", 7), ("Trent Boult", 17),
        ("Khaleel Ahmed", 4), # Corrected name
        ("Gerald Coetzee", 2), ("Tushar Deshpande", 2.5), ("Jasprit Bumrah", 12.5)
    ],
    "LKF": [
        ("Shashank Singh", 4.5), ("Devon Conway", 8), ("Shivam Dube", 9),
        ("Rahul Tripathi", 2.75), ("Shubman Gill", 13.5), ("Bevon Jacobs", 5.25), # New player?
        ("Ruturaj Gaikwad", 7.25), ("Shahrukh Khan", 2), ("Ashutosh Sharma", 3.25),
        ("Krunal Pandya", 4.75), ("Nitish Rana", 4.25), ("Abhinav Manohar", 1),
        ("Naman Dhir", 5.75), ("Josh Inglis", 1.25), ("KL Rahul", 14.5),
        ("Philip Salt", 12), ("Quinton de Kock", 2),
        ("Rasikh Dar Salam", 2.75), # Corrected name
        ("Mohit Sharma", 1.25), ("Allah GhazanFar", 1.25), # New player?
        ("Mitchell Starc", 7), ("Umran Malik", 0.7), ("Yash Thakur", 0.5),
        ("Ravi Bishnoi", 4.25), ("Yash Dayal", 1.25)
    ]
}

# --- Functions ---

def get_or_create_player(db: Session, player_name: str) -> Player:
    """Fetches a player by name or creates a new one if not found."""
    player = db.query(Player).filter(Player.player_name == player_name).first()
    if player:
        return player
    else:
        # Player not found, create a new entry
        print(f"⚠️ Player '{player_name}' not found in database. Creating new record.")
        new_player = Player(
            player_name=player_name,
            team="Unknown", # Cannot determine IPL team from auction data alone
            # Initialize other stats to 0 or default values
            matches_played=0,
            total_runs=0,
            total_balls_faced=0,
            total_fours=0,
            total_sixes=0,
            total_wickets=0,
            total_overs_bowled=0.0,
            total_maidens=0,
            total_runs_conceded=0,
            total_catches=0,
            total_stumpings=0,
            total_run_outs=0,
            total_fantasy_points=0.0
        )
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        print(f"✅ Created new player: {player_name} (ID: {new_player.id})")
        return new_player

def populate_auction_data(db: Session):
    """Populates the TeamPlayer table from the auction data using Decimal for precision."""
    print("Starting auction data population...")
    # Use Decimal for the initial purse
    initial_purse = Decimal('120.0')

    for team_abbr, players in AUCTION_DATA.items():
        full_team_name = TEAM_MAP.get(team_abbr)
        if not full_team_name:
            print(f"❌ Error: Team abbreviation '{team_abbr}' not found in TEAM_MAP.")
            continue

        # Find the Shroff team
        shroff_team = db.query(Shroff_teams).filter(Shroff_teams.team_name == full_team_name).first()
        if not shroff_team:
            print(f"❌ Error: Shroff team '{full_team_name}' not found in database. Skipping.")
            continue

        print(f"Processing team: {full_team_name} ({team_abbr})")
        # Initialize total spent as Decimal
        total_spent = Decimal('0.0')

        for player_name, price_float in players:
            # Convert price to Decimal
            price = Decimal(str(price_float)) # Convert float to string first for accuracy

            # Get or create the player record
            player = get_or_create_player(db, player_name)
            if not player: # Should not happen with get_or_create, but check anyway
                 print(f"❌ Error finding or creating player '{player_name}'. Skipping.")
                 continue

            # Check if player already assigned to a team in this initial auction phase
            existing_assignment = db.query(TeamPlayer).filter(
                TeamPlayer.player_id == player.id,
                TeamPlayer.left_at_match == None # Check active players
            ).first()

            if existing_assignment:
                 # This player is already on a team - could be from a previous run or data issue
                 # For idempotency, let's check if it's the *same* team and price
                 # Convert stored bought_for to Decimal for comparison
                 if existing_assignment.team_id == shroff_team.id and Decimal(str(existing_assignment.bought_for)) == price and existing_assignment.joined_at_match == 0:
                      print(f"ℹ️ Player '{player_name}' already assigned to '{full_team_name}' with correct price. Skipping.")
                      total_spent += price # Still account for spending if re-running
                      continue
                 else:
                      # Assigned elsewhere or different details - potential issue
                      print(f"⚠️ Warning: Player '{player_name}' (ID: {player.id}) is already assigned (Team ID: {existing_assignment.team_id}, Joined: {existing_assignment.joined_at_match}). Check data.")
                      # Decide how to handle: skip this assignment? Overwrite? For now, skip.
                      continue # Skip adding this player

            # Create the TeamPlayer record for the auction
            team_player_entry = TeamPlayer(
                team_id=shroff_team.id,
                player_id=player.id,
                bought_for=float(price), # Store back as float in DB if column is Float
                joined_at_match=0,  # 0 signifies the initial auction draft
                is_captain=False,
                is_vice_captain=False
                # left_at_match remains None
            )
            db.add(team_player_entry)
            total_spent += price
            print(f"  Assigning {player_name} (Price: {price})") # Print Decimal price

        # Update the team's purse using Decimal arithmetic
        remaining_purse = initial_purse - total_spent
        # Store as float if the DB column is Float, otherwise, it might store as string/numeric
        shroff_team.purse = float(remaining_purse)
        print(f"  Total spent by {team_abbr}: {total_spent}")
        print(f"  Updating {full_team_name} purse to: {remaining_purse}")

        # Commit changes for the current team
        try:
            db.commit()
            print(f"✅ Committed data for team {full_team_name}")
        except Exception as e:
            db.rollback()
            print(f"❌ Error committing data for team {full_team_name}: {e}")

    print("Auction data population finished.")

# --- Main Execution ---

if __name__ == "__main__":
    db = SessionLocal()
    try:
        populate_auction_data(db)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        db.close()
        print("Database session closed.") 