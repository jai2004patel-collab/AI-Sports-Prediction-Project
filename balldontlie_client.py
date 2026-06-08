import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/v1"

headers = {
    "Authorization": API_KEY
}

def get_player_id(first_name, last_name):
    url = f"{BASE_URL}/players"
    params = {"search": f"{first_name} {last_name}", "per_page": 25}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    players = response.json()["data"]

    if not players:
        raise ValueError("Player not found.")

    return players[0]["id"]


def get_player_stats(player_id, season=2025, per_page=100):
    url = f"{BASE_URL}/stats"
    params = {
        "player_ids[]": player_id,
        "seasons[]": season,
        "per_page": per_page
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()["data"]
