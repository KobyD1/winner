from flask import Flask, jsonify
from flask import request
from pyairtable import Api
import os

import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")

BASE_URL = "https://api.football-data.org/v4"


def get_headers():
    return {"X-Auth-Token": API_KEY}


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "api": "Football Data API"
    })


@app.route("/league-code/<league_name>")
def get_league_code_route(league_name):

    match league_name:

        case "Spain":
            league_code = "PD"

        case "England-PLeague":
            league_code = "PL"

        case "NBA":
            league_code = "NBA"

        case "Italy-Serie A":
            league_code = "SA"

        case _:
            league_code = None

    return jsonify({
        "league_name": league_name,
        "league_code": league_code
    })


@app.route("/football-banker", methods=["POST"])
def calc_football_banker_algo():

    data = request.get_json()

    team_a_data = data["team_a"]
    team_b_data = data["team_b"]

    scores = 0
    favorite = 0

    position_diff = (
        int(team_a_data["Position"]) -
        int(team_b_data["Position"])
    )

    position_diff_abs = abs(position_diff)

    points_diff = (
        int(team_a_data["Points"]) -
        int(team_b_data["Points"])
    )

    points_diff = abs(points_diff)

    if position_diff_abs > 9:

        print(
            "Teams found for Banker Algo by position"
        )

        scores += position_diff_abs * 10

    if (
        position_diff_abs > 9 and
        points_diff > 9
    ):

        print(
            "Teams found for Banker Algo by points"
        )

        scores += points_diff * 10

    # team_a better ranked
    if (
        position_diff < 0 and
        position_diff_abs > 9
    ):

        scores += 20
        favorite = 1

    # team_b better ranked
    elif (
        position_diff > 0 and
        position_diff_abs > 9
    ):

        favorite = 2

    print(
        f"{scores} scores found "
        f"favorite = {favorite}"
    )

    return jsonify({
        "score": scores,
        "favorite": favorite,
        "position_diff": position_diff_abs,
        "points_diff": points_diff
    })
@app.route("/football-under", methods=["POST"])
def calc_football_under_over_api_algo():
    data = request.get_json()

    team_a = data["team_a"]
    team_b = data["team_b"]
    desc = data["desc"]

    bonus = 0
    favorite = 0

    team_a_avg_total = team_a["avgGoals"]
    team_b_avg_total = team_b["avgGoals"]

    avg_total = (team_a_avg_total + team_b_avg_total) / 2
    difference = abs(team_a_avg_total - team_b_avg_total)

    if difference < 0.6:
        bonus += 10

        print(
            f"2 teams under over found with similar "
            f"average total goals: "
            f"{team_a['Team']} , {team_b['Team']}"
        )

    if difference > 1.5:
        bonus -= 10

        print(
            f"*** 2 teams found with none similar "
            f"average goals!!! "
            f"{team_a['Team']} , {team_b['Team']} ***"
        )

    if desc == "2 Teams Under/Over 2-3 Range":

        match avg_total:
            case x if x < 1.0:
                favorite = 1
                bonus += 20
                home_count = team_a.get("count_0_1", 0)
                away_count = team_b.get("count_0_1", 0)

            case x if 1.6 <= x < 2.65:
                favorite = 3
                home_count = team_a.get("count_2_3", 0)
                away_count = team_b.get("count_2_3", 0)

            case x if x > 3.1:
                favorite = 2
                high_bonus = (avg_total - 3) * 15
                home_count = team_a.get("count_4_plus", 0)
                away_count = team_b.get("count_4_plus", 0)
                bonus += 30 + high_bonus

            case _:
                favorite = 0
                home_count = 0
                away_count = 0
    elif desc == "2 Teams Under/Over":

        if avg_total < 2.5:
            favorite = 1
        else:
            favorite = 2

    print(
        f"Summary - Bonus: {bonus}, "
        f"favorite: {favorite}, "
        f"avg_total: {avg_total}"
    )

    return jsonify({
        "score": round(bonus, 2),
        "favorite": favorite,
        "home_count": home_count,
        "away_count": away_count,
        "avg_total": round(avg_total, 2)
    })


@app.route("/<league_code>/teams")
def get_teams(league_code):
    url = f"{BASE_URL}/competitions/{league_code}/teams"

    response = requests.get(
        url,
        headers=get_headers()
    )

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

    response = requests.get(url, headers=get_headers())

    if response.status_code != 200:
        return jsonify({
            "error": response.status_code,
            "details": response.text
        }), response.status_code

    data = response.json()

    results = []

    for match in data.get("matches", []):
        full_time = match.get("score", {}

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

    response = requests.get(url, headers=get_headers())

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

    response = requests.get(url, headers=get_headers())

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

    standings_response = requests.get(
        standings_url,
        headers=get_headers()
    )

    matches_response = requests.get(
        matches_url,
        headers=get_headers()
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

@app.route("/config")
def config():
    BASE_URL = os.getenv("URL_WINNER")
    AIRTABLE_API_KEY = os.getenv("AIR_TABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

    return jsonify({
        "ui_base_url": BASE_URL,
        "airtable_api_key": AIRTABLE_API_KEY,
        "airtable_base_id": AIRTABLE_BASE_ID,
        "airtable_table_name": AIRTABLE_TABLE_NAME
    })

@app.route("/check-license/<hwid>")
def check_license(hwid):


    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
    api = Api(AIRTABLE_API_KEY)

    table = api.table(
        AIRTABLE_BASE_ID,
        AIRTABLE_TABLE_NAME
    )

    formula = f"{{HWID}}='{hwid}'"

    records = table.all(
        formula=formula
    )

    if records:

        fields = records[0]["fields"]

        status = fields.get(
            "Status",
            ""
        )

        return jsonify({
            "hwid": hwid,
            "status": status,
            "valid": status == "Valid"
        })

    table.create({
        "HWID": hwid,
        "Status": "Pending"
    })

    return jsonify({
        "hwid": hwid,
        "status": "Pending",
        "valid": False
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
