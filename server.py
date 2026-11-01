from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")
API_KEY = "6e8b3c65a58f4a05b874d72fe4170fd7"

BASE_URL = "https://api.football-data.org/v4"


def get_headers():
    return {
        "X-Auth-Token": API_KEY
    }


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "api": "Football Data API"
    })
@app.route("/<league_code>/football-under/<taeam_a/<team_b>/<desc>")
def calc_football_under_over_api_algo(self, team_a, team_b, desc):
    bonus = 0
    favorite = ""
    team_a_avg_total = team_a["avgGoals"]
    team_b_avg_total = team_b["avgGoals"]
    avg_total = (team_a_avg_total + team_b_avg_total) / 2
    if abs(team_a_avg_total - team_a_avg_total) < 0.6:
        bonus += 10
        print(f"2 teams under over found with similar average total goals: {team_a["Team"]} ,{team_b["Team"]}")

    if abs(team_a_avg_total - team_a_avg_total) > 1.5:
        bonus -= 10
        print(f"*** 2 teams found with none similar average goals!!! {team_a["Team"]} ,{team_b["Team"]}***")

    if desc == "2 Teams Under/Over 2-3 Range":

        match avg_total:
            case x if x < 1.0:
                favorite = 1
                bonus += 20
            case x if 1.6 <= x < 2.65:
                favorite = 3
            case x if x > 3.1:
                favorite = 2
                high_bonus = (avg_total - 3) * 15
                bonus = bonus + 30 + high_bonus
            case _:
                print("Other scoring range")
                favorite = 0



    elif desc == "2 Teams Under/Over":
        pass
    print(f"Summery  - Bonus: {bonus} ,favorite: {favorite} , avg_total: {avg_total}")
    return jsonify({
        "bonus": bonus,
        "favorite": favorite,
        "avg_total": avg_total
    })



@app.route("/<league_code>/teams")
def get_teams(league_code):
    url = f"{BASE_URL}/competitions/{league_code}/teams"
    response = requests.get(url, headers=get_headers())

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
        "league": league_code,
        "total_teams": len(teams),
        "teams": teams
    })


@app.route("/<league_code>/teams")
def get_teams(league_code):

    url = f"{BASE_URL}/competitions/{league_code}/teams"

    response = requests.get(url, headers=get_headers())


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
        "league": league_code,
        "total_teams": len(teams),
        "teams": teams
    })


@app.route("/<league_code>/matches")
def matches(league_code):

    url = f"{BASE_URL}/competitions/{league_code}/matches"

    response = requests.get(url,headers=get_headers())


    if response.status_code != 200:
        return jsonify({
            "error": response.status_code,
            "details": response.text
        }), response.status_code

    data = response.json()

    results = []

    for match in data.get("matches", []):

        full_time = match.get(
            "score", {}
        ).get(
            "fullTime", {}
        )

        results.append({
            "matchday": match.get("matchday"),
            "date": match.get("utcDate"),
            "status": match.get("status"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "home_goals": full_time.get("home"),
            "away_goals": full_time.get("away")
        })

    return jsonify({
        "league": league_code,
        "matches": results
    })


@app.route("/<league_code>/results")
def results(league_code):

    url = f"{BASE_URL}/competitions/{league_code}/matches"

    response = requests.get(url,headers=get_headers())


    if response.status_code != 200:
        return jsonify({
            "error": response.status_code,
            "details": response.text
        }), response.status_code

    data = response.json()

    results = []

    for match in data.get("matches", []):

        if match.get("status") != "FINISHED":
            continue

        full_time = match.get(
            "score", {}
        ).get(
            "fullTime", {}
        )

        results.append({
            "matchday": match.get("matchday"),
            "date": match.get("utcDate"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "home_goals": full_time.get("home"),
            "away_goals": full_time.get("away")
        })

    return jsonify({
        "league": league_code,
        "results": results
    })


@app.route("/<league_code>/standings")
def standings(league_code):

    url = f"{BASE_URL}/competitions/{league_code}/standings"

    response = requests.get(url,headers=get_headers())


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

    return jsonify({
        "league": league_code,
        "standings": table
    })

@app.route("/<league_code>/all-stats")
def all_stats(league_code):

    standings_url = (f"{BASE_URL}/competitions/{league_code}/standings")
    matches_url = (f"{BASE_URL}/competitions/{league_code}/matches")

    standings_response = requests.get(standings_url,headers=get_headers())
    matches_response = requests.get(matches_url,headers=get_headers())

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
            "goal_difference": row["goalDifference"],
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
        "competition": league_code,
        "teams": teams
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )