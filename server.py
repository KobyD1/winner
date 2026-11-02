from flask import Flask, jsonify
from flask import request
from pyairtable import Api
from nba_api.stats.endpoints import LeagueDashTeamStats

import logging

import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")

BASE_URL = "https://api.football-data.org/v4"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
# =======================================
# NBA API
# ======================================
import requests
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import request, jsonify


def fetch_team_averages(team_id):
    """
    פונקציית עזר לשליפת וחישוב ממוצע נקודות ושלשות לקבוצה בודדת לפי team_id.
    """
    schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    try:
        schedule_data = requests.get(schedule_url, timeout=5).json()
    except Exception:
        return None

    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    valid_events = []

    for event in schedule_data.get("events", []):
        comp = event["competitions"][0]
        if comp["status"]["type"]["completed"]:
            event_date_str = event.get("date")
            try:
                event_date = datetime.strptime(event_date_str.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                event_date = event_date.replace(tzinfo=timezone.utc)
                if event_date >= one_year_ago:
                    valid_events.append(event["id"])
            except Exception:
                pass

    if not valid_events:
        return None

    total_points = 0
    total_3pt_made = 0
    games_count = 0

    # שליפה מקבילית של סיכומי המשחקים של אותה קבוצה
    def fetch_game_stats(event_id):
        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
        try:
            summary_data = requests.get(summary_url, timeout=5).json()
            boxscore = summary_data.get("boxscore", {})
            teams_stats = boxscore.get("teams", [])

            for t_stat in teams_stats:
                t_info = t_stat.get("team", {})
                if str(t_info.get("id")) == str(team_id):
                    points = 0
                    three_pt_made = 0

                    for stat in t_stat.get("statistics", []):
                        name = stat.get("name", "")
                        if name == "points":
                            points = float(stat.get("value", 0))
                        elif "threePointFieldGoalsMade" in name or stat.get("abbreviation") == "3PT":
                            val_str = str(stat.get("displayValue", "0"))
                            if "-" in val_str:
                                three_pt_made = float(val_str.split("-")[0])
                            else:
                                three_pt_made = float(stat.get("value", 0))

                    if points == 0:
                        competitions_header = summary_data.get("header", {}).get("competitions", [{}])[0]
                        for comp_team in competitions_header.get("competitors", []):
                            if str(comp_team.get("team", {}).get("id")) == str(team_id):
                                points = float(comp_team.get("score", 0))

                    return points, three_pt_made
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_game_stats, ev_id): ev_id for ev_id in valid_events}
        for future in as_completed(futures):
            res = future.result()
            if res:
                points, three_pt = res
                total_points += points
                total_3pt_made += three_pt
                games_count += 1

    if games_count == 0:
        return None

    # שליפת שם הקבוצה מה-schedule
    team_name = schedule_data.get("team", {}).get("displayName", f"Team {team_id}")

    return {
        "name": team_name,
        "games_analyzed": games_count,
        "PTS": round(total_points / games_count, 2),
        "FG3M": round(total_3pt_made / games_count, 2)
    }


@app.route("/nba/get-teams-espn", methods=["POST"])
def get_nba_teams_espn():
    data = request.get_json()

    if not data or "team1" not in data or "team2" not in data:
        return jsonify({"error": "Missing team1 or team2 in request body (expected team IDs)"}), 400

    team1_id = data["team1"]
    team2_id = data["team2"]

    # הרצת השליפה לשתי הקבוצות במקביל כדי לחסוך זמן תגובה
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(fetch_team_averages, team1_id)
        future2 = executor.submit(fetch_team_averages, team2_id)

        res1 = future1.result()
        res2 = future2.result()

    if not res1 or not res2:
        return jsonify({"error": "One or both teams not found or have no recent games"}), 404

    avg_pts = (res1["PTS"] + res2["PTS"]) / 2
    avg_3pm = (res1["FG3M"] + res2["FG3M"]) / 2

    return jsonify({
        "team_a": res1,
        "team_b": res2,
        "avg_pts": round(avg_pts, 2),
        "avg_3pm": round(avg_3pm, 2)
    })

@app.route("/nba/calc-under", methods=["POST"])
def calc_nba_under():
    print("Calculating NBA Under/Over based on the request data...")
    app.logger.info("NBA Calculation Called")

    data = request.get_json()

    teams = data["teams"]

    bonus = 0
    offset = 8
    favorite = 0

    avg_teams = (
        teams["team_a"]["PTS"] +
        teams["team_b"]["PTS"]
    ) / 2

    rate = data["rate"]

    if rate - avg_teams > offset:
        favorite = 2  # Under

    elif avg_teams - rate > offset:
        favorite = 1  # Over

    if abs(rate - avg_teams) > 15:
        bonus = 20

    return jsonify({
        "favorite": favorite,
        "score": bonus,
        "game": data["game"],
        "rate": rate,
        "avg_teams": round(avg_teams, 2),
        "difference": round(
            abs(rate - avg_teams),
            2
        )
    })
import pandas as pd
import requests
from flask import jsonify, request

@app.route("/nba/team-stats")
def nba_team_stats():

    tables = pd.read_html(
        "https://www.espn.com/nba/stats/team"
    )

    return jsonify({
        "columns": tables[0].columns.tolist(),
        "rows": len(tables[0])
    })


app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True)



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
