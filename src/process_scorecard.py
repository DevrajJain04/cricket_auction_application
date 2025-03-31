import json
from collections import defaultdict

# Sample data (replace this with your actual JSON data)
data = {
    "apikey": "86a6c1c2-bbc1-4a95-9193-97b01d23c244",
    "data": {
        "id": "cacf2d34-41b8-41dd-91ed-5183d880084c",
        "name": "Kolkata Knight Riders vs Royal Challengers Bengaluru, 1st Match",
        "matchType": "t20",
        "status": "Royal Challengers Bengaluru won by 7 wkts",
        "venue": "Eden Gardens, Kolkata",
        "date": "2025-03-22",
        "dateTimeGMT": "2025-03-22T14:00:00",
        "teams": ["Kolkata Knight Riders", "Royal Challengers Bengaluru"],
        "score": [
            {"r": 174, "w": 8, "o": 20, "inning": "Kolkata Knight Riders Inning 1"},
            {"r": 177, "w": 3, "o": 16.2, "inning": "Royal Challengers Bengaluru Inning 1"}
        ],
        "tossWinner": "Royal Challengers Bengaluru",
        "tossChoice": "bowl",
        "matchWinner": "Royal Challengers Bengaluru",
        "series_id": "d5a498c8-7596-4b93-8ab0-e0efc3345312",
        "scorecard": [
            {
                "batting": [
                    {
                        "batsman": {"id": "000f9f7c-cc24-4a85-8638-b013b0f4760e", "name": "Quinton de Kock"},
                        "dismissal": "catch",
                        "bowler": {"id": "2190c28d-1712-4fd2-ae44-9ac54319fc21", "name": "Josh Hazlewood"},
                        "catcher": {"id": "e28de73b-f5df-49eb-bdf6-c50471319404", "name": "Jitesh Sharma"},
                        "dismissal-text": "c jitesh sharma b hazlewood",
                        "r": 4,
                        "b": 5,
                        "4s": 1,
                        "6s": 0,
                        "sr": 80,
                        "": 0
                    },
                    # ... (rest of the batting data)
                ],
                "bowling": [
                    {
                        "bowler": {"id": "2190c28d-1712-4fd2-ae44-9ac54319fc21", "name": "Josh Hazlewood"},
                        "o": 4,
                        "m": 0,
                        "r": 22,
                        "w": 2,
                        "nb": 0,
                        "wd": 0,
                        "eco": 5.5
                    },
                    # ... (rest of the bowling data)
                ],
                "catching": [
                    {
                        "catcher": {"id": "e28de73b-f5df-49eb-bdf6-c50471319404", "name": "Jitesh Sharma"},
                        "stumped": 0,
                        "runout": 0,
                        "catch": 4,
                        "cb": 0,
                        "lbw": 0,
                        "bowled": 0
                    },
                    # ... (rest of the catching data)
                ],
                "extras": {"r": 6, "b": 0},
                "totals": {},
                "inning": "Kolkata Knight Riders Inning 1"
            },
            # ... (second innings data)
        ],
        "matchStarted": True,
        "matchEnded": True
    },
    "status": "success",
    "info": {
        "hitsToday": 30,
        "hitsUsed": 10,
        "hitsLimit": 100,
        "credits": 0,
        "server": 11,
        "queryTime": 28.933,
        "s": 0,
        "cache": 0
    }
}

def process_match_data(match_data):
    match_data = match_data['data']
    # Initialize player stats dictionary
    player_stats = defaultdict(lambda: {
        'player_name': '',
        'team': '',
        'matches': 1,
        'batting_innings': 0,
        'runs': 0,
        'balls_faced': 0,
        'fours': 0,
        'sixes': 0,
        'strike_rate': 0,
        'dismissals': 0,
        'dismissal_type': '',
        'dismissal_bowler': '',
        'bowling_innings': 0,
        'overs_bowled': 0,
        'maidens': 0,
        'runs_conceded': 0,
        'wickets': 0,
        'no_balls': 0,
        'wides': 0,
        'economy': 0,
        'catches': 0,
        'stumpings': 0,
        'run_outs': 0,
        'match_id': match_data['id'],
        'match_name': match_data['name'],
        'match_date': match_data['date'],
        'venue': match_data['venue']
    })
    
    teams = match_data['teams']
    
    for innings in match_data['scorecard']:
        # Determine which team is batting and which is bowling
        batting_team = innings['inning'].split(' Inning')[0]
        bowling_team = teams[1] if batting_team == teams[0] else teams[0]
        
        # Process batting stats
        for batsman in innings['batting']:
            player_id = batsman['batsman']['id']
            player_name = batsman['batsman']['name']
            
            player_stats[player_id]['player_name'] = player_name
            player_stats[player_id]['team'] = batting_team
            player_stats[player_id]['batting_innings'] += 1
            player_stats[player_id]['runs'] += batsman['r']
            player_stats[player_id]['balls_faced'] += batsman['b']
            player_stats[player_id]['fours'] += batsman['4s']
            player_stats[player_id]['sixes'] += batsman['6s']
            player_stats[player_id]['strike_rate'] = batsman['sr']
            
            if 'dismissal' in batsman:
                player_stats[player_id]['dismissals'] += 1
                player_stats[player_id]['dismissal_type'] = batsman['dismissal']
                player_stats[player_id]['dismissal_bowler'] = batsman['bowler']['name']
        
        # Process bowling stats
        for bowler in innings['bowling']:
            player_id = bowler['bowler']['id']
            player_name = bowler['bowler']['name']
            
            player_stats[player_id]['player_name'] = player_name
            player_stats[player_id]['team'] = bowling_team
            player_stats[player_id]['bowling_innings'] += 1
            player_stats[player_id]['overs_bowled'] += bowler['o']
            player_stats[player_id]['maidens'] += bowler['m']
            player_stats[player_id]['runs_conceded'] += bowler['r']
            player_stats[player_id]['wickets'] += bowler['w']
            player_stats[player_id]['no_balls'] += bowler['nb']
            player_stats[player_id]['wides'] += bowler['wd']
            player_stats[player_id]['economy'] = bowler['eco']
        
        # Process fielding stats
        for fielder in innings['catching']:
            if 'catcher' in fielder:
                player_id = fielder['catcher']['id']
                player_name = fielder['catcher']['name']
                
                player_stats[player_id]['player_name'] = player_name
                player_stats[player_id]['team'] = bowling_team
                player_stats[player_id]['catches'] += fielder['catch']
                player_stats[player_id]['stumpings'] += fielder['stumped']
                player_stats[player_id]['run_outs'] += fielder['runout']
    
    return player_stats

# def write_to_csv(player_stats, filename='player_stats.csv'):
#     headers = [
#         'player_name', 'team', 'matches', 'batting_innings', 'runs', 'balls_faced', 
#         'fours', 'sixes', 'strike_rate', 'dismissals', 'dismissal_type', 
#         'dismissal_bowler', 'bowling_innings', 'overs_bowled', 'maidens', 
#         'runs_conceded', 'wickets', 'no_balls', 'wides', 'economy', 'catches', 
#         'stumpings', 'run_outs', 'match_id', 'match_name', 'match_date', 'venue'
#     ]
    
    # with open(filename, 'w', newline='') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=headers)
    #     writer.writeheader()
        
    #     for player_id, stats in player_stats.items():
    #         writer.writerow(stats)

## Process the data
# match_data = data['data']
# player_stats = process_match_data(match_data)

# # Write to CSV
# import csv
# write_to_csv(player_stats)

# print("Player stats CSV file has been created successfully.")