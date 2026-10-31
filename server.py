from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")
API_KEY = "6e8b3c65a58f4a05b874d72fe4170fd7"


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


@app.route("/teams")
def get_teams():

    url = "https://api.football-data.org/v4/competitions/PL/teams"

    headers = {
        "X-Auth-Token": API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": response.status_code,
            "details": response.text
        }), response.status_code

    data = response.json()

    teams = []

    for team in data.get("teams", []):

        teams.append({
            "id": team.get("id"),
            "name": team.get("name"),
            "shortName": team.get("shortName"),
            "tla": team.get("tla")
        })

    return jsonify({
        "total_teams": len(teams),
        "teams": teams
    })

@app.route("/all-results")
def all_results():

    url = "https://api.football-data.org/v4/competitions/PL/matches"

    headers = {
        "X-Auth-Token": API_KEY
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
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "home_goals": full_time.get("home"),
            "away_goals": full_time.get("away")
        })

    return jsonify(results)