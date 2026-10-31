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
@app.route("/standings")
def standings():

    url = "https://api.football-data.org/v4/competitions/PL/standings"

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

    table = []

    for row in data["standings"][0]["table"]:

        table.append({
            "position": row["position"],
            "team": row["team"]["name"],
            "points": row["points"],
            "played": row["playedGames"],
            "won": row["won"],
            "draw": row["draw"],
            "lost": row["lost"],
            "goals_for": row["goalsFor"],
            "goals_against": row["goalsAgainst"],
            "goal_difference": row["goalDifference"]
        })

    return jsonify(table)

@app.route("/all-stats")
def all_stats():

    headers = {
        "X-Auth-Token": API_KEY
    }

    standings_url = "https://api.football-data.org/v4/competitions/PL/standings"
    matches_url = "https://api.football-data.org/v4/competitions/PL/matches"

    standings_response = requests.get(
        standings_url,
        headers=headers
    )

    matches_response = requests.get(
        matches_url,
        headers=headers
    )

    if standings_response.status_code != 200:
        return jsonify({
            "error": "standings error",
            "status": standings_response.status_code
        }), 500

    if matches_response.status_code != 200:
        return jsonify({
            "error": "matches error",
            "status": matches_response.status_code
        }), 500

    standings_data = standings_response.json()
    matches_data = matches_response.json()

    teams = {}

    table = standings_data["standings"][0]["table"]

    for row in table:

        team_name = row["team"]["name"]

        teams[team_name] = {
            "position": row["position"],
            "points": row["points"],
            "played": row["playedGames"],
            "won": row["won"],
            "draw": row["draw"],
            "lost": row["lost"],
            "goals_for": row["goalsFor"],
            "goals_against": row["goalsAgainst"],
            "matches": []
        }

    for match in matches_data["matches"]:

        if match["status"] != "FINISHED":
            continue

        full_time = match["score"]["fullTime"]

        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]

        game = {
            "date": match["utcDate"],
            "matchday": match["matchday"],
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": full_time["home"],
            "away_goals": full_time["away"],
            "total_goals": (
                full_time["home"] +
                full_time["away"]
            )
        }

        if home_team in teams:
            teams[home_team]["matches"].append(game)

        if away_team in teams:
            teams[away_team]["matches"].append(game)

    return jsonify({
        "competition": "Premier League",
        "teams": teams
    })