from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "api": "Premier League Results"
    })


@app.route("/premier-league")
def premier_league():
    url = "https://api.football-data.org/v4/competitions/PL/matches"

    headers = {
        "X-Auth-Token": "6e8b3c65a58f4a05b874d72fe4170fd7"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": response.status_code,
            "details": response.text
        }), response.status_code

    data = response.json()

    results = []

    for match in data.get("matches", []):
        full_time = match.get("score", {}).get("fullTime", {})

        results.append({
            "matchday": match.get("matchday"),
            "date": match.get("utcDate"),
            "status": match.get("status"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
    })
