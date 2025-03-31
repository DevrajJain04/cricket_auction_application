import csv
import requests

# Your CricAPI API key
API_KEY = "c655a210-1d77-46e5-978c-1c219c65448f"
BASE_URL = "https://api.cricapi.com/v1/"

# def get_fantasy_squad(match_id):
#     """
#     Fetches the fantasy squad for the given match.
#     Endpoint: /v1/match_squad
#     Returns a JSON response with two team objects, each containing a list of players.
#     """
#     url = BASE_URL + "match_squad"
#     params = {
#         "apikey": API_KEY,
#         "offset": 0,
#         "id": match_id
#     }
#     response = requests.get(url, params=params)
#     return response.json()

def get_match_scorecard(match_id):
    """
    Fetches the match scorecard for the given match.
    Endpoint: /v1/match_scorecard
    Returns a JSON response containing details about the match, including teams and scores.
    """
    url = BASE_URL + "match_scorecard"
    params = {
        "apikey": API_KEY,
        "offset": 0,
        "id": match_id
    }
    response = requests.get(url, params=params)
    return response.json()

# def get_fantasy_points(match_id, ruleset=0):
#     """
#     Fetches fantasy points for the given match.
#     Endpoint: /v1/match_points
#     Returns a JSON response where the 'totals' array contains player-wise fantasy points.
#     """
#     url = BASE_URL + "match_points"
#     params = {
#         "apikey": API_KEY,
#         "offset": 0,
#         "id": match_id,
#         "ruleset": ruleset  # Change ruleset if needed
#     }
#     response = requests.get(url, params=params)
#     return response.json()

def main():
    # Replace with the actual match ID you want to process
    match_id = "7431523f-7ccb-4a4a-aed7-5c42fc08464c"
    
    # Fetch squad and points data
    scorecard = get_match_scorecard(match_id)
    
    # Build a mapping of player ID to team name from the squad data
    player_team = {}
    # make sure data is not empty
    

    # Write the output to a CSV file
    csv_filename = "scorecard_csk_rcb.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        fieldnames = ["Player Name", "Team", "Fantasy Points"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in player_points:
            writer.writerow(row)
    print(f"CSV file '{csv_filename}' generated successfully.")

if __name__ == "__main__":
    main()
