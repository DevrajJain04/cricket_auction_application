import requests
import os,json,csv
from dotenv import load_dotenv
from process_scorecard import process_match_data
load_dotenv()
# API_KEY = os.getenv("API_KEY_MAIN")

# params = {
#     "apikey": API_KEY,
#     "offset": 0,
#     "id": "cacf2d34-41b8-41dd-91ed-5183d880084c"
# }

# response  = requests.get(
#     url="https://api.cricapi.com/v1/match_scorecard",
#     params = params
# )

with open("response.json", "r") as f:
    input_result = json.loads(f.read())
    print(input_result["apikey"])
    player_stats = process_match_data(input_result)
    for pid,stats in list(player_stats.items())[:3]:
        print((stats))