from flask import Flask, jsonify
from flask import request
from pyairtable import Api

import logging

import requests
import os

app = Flask(__name__)

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

FOOTBALL_BASE_URL = "https://api.football-data.org/v4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def get_headers():
    return {"X-Auth-Token": FOOTBALL_API_KEY}




HEBREW_TO_ENGLISH_TEAMS = {
    "מכבי תל אביב": "Maccabi Tel Aviv",
    "מכבי חיפה": "Maccabi Haifa",
    "מכבי נתניה": "Maccabi Netanya",
    "הפועל באר שבע": "H. Be'er Sheva",
    'בית"ר ירושלים': "Beitar Jerusalem",
    "הפועל תל אביב": "Hapoel Tel Aviv",
    "הפועל חיפה": "Hapoel Haifa",
    "בני סכנין": "Bnei Sakhnin",
    "מכבי פתח תקווה": "Maccabi Petah Tikva",
    "הפועל רמת גן": "Hapoel Ramat Gan",
    "הפועל קרית שמונה": "Ironi Kiryat Shmona",
    "הפועל פתח תקווה": "Hapoel Petah Tikva",
    "הפועל ירושלים": "Hapoel Jerusalem",
    "עירוני טבריה": "Ironi Tiberias"

}


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "api": "Football Data API"
    })


@app.route("/analyze", methods=["POST"])
def sort_and_analyze_results():
    req_data = request.get_json()
    results_not_sorted =req_data["results_not_sorted"]
    results_sorted = sorted(results_not_sorted, key=lambda x: x["score"], reverse=True)

    headers =  ["Favor.", "Game", "Score", "Bet", " Under/Over Rate","Teams Rate","Home Points", "Home - Game Points","Away Points", "Away - Game Points"]
    rows = [
        [
            str(item["favorite"]),
            str(item["game"]),
            f"{item['score']:.2f}",
            str(item["bet"]),
            str(item["rate"]),
            str(item["avg_pts"]),
            str(item["team_a"].get("PTS", 0)),
            str(item["team_a"].get("PTS_GAME", 0)),

            str(item["team_b"].get("PTS", 0)),
            str(item["team_b"].get("PTS_GAME", 0)),

        ]
        for item in results_sorted
    ]


    return jsonify({
            "results_sorted": results_sorted,
            "headers": headers,
            "rows": rows,
        }), 200
@app.route('/sort_and_prapare_print', methods=['POST'])
def sort_and_prapare_to_print():

    results_not_sorted = request.get_json()
    results_sorted = sorted(
        results_not_sorted,
        key=lambda x: x.get("Points", {}).get("value", 0),
        reverse=True
    )
    headers = [k for k, v in sorted(results_sorted[0].items(), key=lambda x: x[1]["id"])]
    rows = [
        [
            str(v["value"])
            for _, v in sorted(item.items(), key=lambda x: x[1]["id"])
        ]
        for item in results_sorted
    ]

    return jsonify({
        "results_sorted": results_sorted,
        "headers": headers,
        "rows": rows,
    }), 200

@app.route('/israel-corners/analyze', methods=['POST'])
def analyze_corners():
    data = request.get_json()
    table_data_converted=data.get("table_data")
    corner_data = data.get("corner_data")
    offset = data.get("offset", 2)
    if offset == -1 : offset = 2
    logger.info(f"running with offset {offset}")


    results_not_sorted = []

    for item in table_data_converted["data"]:
        if item["description"] != "Corners 2 Teams":
            continue

        corner_a = float(corner_data.get(item["team_a"], 0))
        corner_b = float(corner_data.get(item["team_b"], 0))
        logger.info(f"Corner teams values :corner_a ={corner_a} ,corner_b ={corner_b} ")

        total_corner = corner_a + corner_b
        favorite = 0
        rate = ""
        points = 0

        if total_corner < (9 - offset):
            favorite = 1
            rate = "under 9-11"

        elif total_corner > (11 + offset):
            favorite = 2
            rate = "over 9-11"

        if total_corner > 14 or total_corner < 6:
            points += 25

        if abs(corner_a - corner_b) < 3:
            points += 15
        if (favorite!= 0 ):
            result_data = {}
            logger.info(f"Corner game favorite found the value is   {favorite}  ")
            for i, (name, value) in enumerate({
                                                  "Favorite": favorite,
                                                  "Game": item.get("game"),
                                                  "Points": points,
                                                  "Bet": item.get(f"bet{favorite}") if favorite != 0 else "",
                                                  "Rate": rate,
                                                  "Teams Corners": round(corner_a + corner_b,2),
                                                  "Team Home": f"{item.get("team_a")} ({corner_a})",
                                                  "Team Away": f"{item.get("team_b")} ({corner_b})",

                                              }.items(), start=1):
                result_data[name] = {
                    "id": i,
                    "value": value
                }
            results_not_sorted.append(result_data)

    return jsonify(results_not_sorted)

@app.route('/israel-corners/translate-teams', methods=['POST'])
def translate_teams():
    data = request.get_json()

    logger.info(f"/israel-corners/translate-teams -Total get  {len(data)} games ")

    updated_data = []
    for item in data:
        new_item = item.copy()

        if "team_a" in new_item and new_item["team_a"] in HEBREW_TO_ENGLISH_TEAMS:
            new_item["team_a"] = HEBREW_TO_ENGLISH_TEAMS[new_item["team_a"]]

        if "team_b" in new_item and new_item["team_b"] in HEBREW_TO_ENGLISH_TEAMS:
            new_item["team_b"] = HEBREW_TO_ENGLISH_TEAMS[new_item["team_b"]]

        updated_data.append(new_item)

    logger.info(f"Total found : {len(updated_data)} games ")

    return jsonify({"status": "success", "data": updated_data}), 200





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
        logger.info(f"Teams found for Banker Algo by position diff: {position_diff_abs}")


        scores += position_diff_abs * 10

    if (position_diff_abs > 9) and (points_diff > 9):


        scores += points_diff * 10

    # team_a better ranked
    if (position_diff > 0) and (position_diff_abs > 9):
        logger.info(f"Teams found for Banker Algo by Home Team: {points_diff}")

        scores += 20
        favorite = 2

    # team_b better ranked
    elif (position_diff < 0 ) and (position_diff_abs>9):

        logger.info(f"Teams found for Banker Algo by Away Team: {points_diff}")
        favorite = 1

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
    logger.info(f"into /football-under ")

    team_a = data["team_a"]
    team_b = data["team_b"]
    desc = data["desc"]
    offset = data.get("offset",0)
    if offset == -1 :offset = 0
    logger.info(f"running with offset {offset}")
    bonus = 0
    favorite = 0

    team_a_avg_total = team_a["avgGoals"]
    team_b_avg_total = team_b["avgGoals"]

    avg_total = (team_a_avg_total + team_b_avg_total) / 2
    difference = abs(team_a_avg_total - team_b_avg_total)

    if difference < 0.6:
        bonus += 10

        logger.info(
            f"2 teams under over found with similar "
            f"average total goals: "
            f"{team_a['Team']} , {team_b['Team']}"
        )

    if difference > 1.5:
        bonus -= 10

        logger.info(
            f"*** 2 teams found with none similar "
            f"average goals!!! "
            f"{team_a['Team']} , {team_b['Team']} ***"
        )

    if desc == "2 Teams Under/Over 2-3 Range":

        match avg_total:
            case x if x < 0.9-offset:
                favorite = 1
                bonus += 20
                home_count = team_a.get("count_0_1", 0)
                away_count = team_b.get("count_0_1", 0)

            case x if 1.6 <= x < 2.65:
                favorite = 3
                home_count = team_a.get("count_2_3", 0)
                away_count = team_b.get("count_2_3", 0)

            case x if x > 3.1+offset:
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

    logger.info(
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
    url = f"{FOOTBALL_BASE_URL}/competitions/{league_code}/teams"

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
    url = f"{FOOTBALL_BASE_URL}/competitions/{league_code}/matches"

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
    url = f"{FOOTBALL_BASE_URL}/competitions/{league_code}/matches"

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
    url = f"{FOOTBALL_BASE_URL}/competitions/{league_code}/standings"

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
    standings_url = (f"{FOOTBALL_BASE_URL}/competitions/{league_code}/standings")
    matches_url = (f"{FOOTBALL_BASE_URL}/competitions/{league_code}/matches")

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
# =======================================
# NBA API
# ======================================


@app.route("/nba/calc-under", methods=["POST"])
def calc_under():
    req_data = request.get_json()
    app.logger.info("Request  calc-under received")



    if not req_data:
        return jsonify({"error": "data not found at request"}), 400
    game = req_data["table_data"]["game"]
    rate = req_data["table_data"]["rate"]
    team1 = req_data.get("team1")
    team2 = req_data.get("team2")
    favorite = req_data.get("favorite")
    offset = req_data.get("offset",8)
    if offset == -1 : offset = 8
    logger.info(f"running with offset {offset}")

    data = req_data.get("data", [])

    row1 = next((item for item in data if item.get("TEAM_NAME") == team1), None)
    row2 = next((item for item in data if item.get("TEAM_NAME") == team2), None)

    logger.info(f"game -  {game},home : {team1}, away: {team2}")
    logger.info(f"Home team - PTS: {row1['PTS']},3PM: {row1['FG3M']}, PLUS_MINUS: {row1['PLUS_MINUS']}")
    logger.info(f"Away team - PTS: {row2['PTS']},3PM: {row2['FG3M']}, PLUS_MINUS: {row2['PLUS_MINUS']}")

    avg_pts_team1 = row1["PTS"]
    avg_pts_team2 = row2["PTS"]

    avg_pts_team1_other = (avg_pts_team1- row1["PLUS_MINUS"])
    avg_pts_team2_other = (avg_pts_team2 - row2["PLUS_MINUS"])

    avg_pts_team1_all = avg_pts_team1_other + avg_pts_team1
    avg_pts_team2_all = avg_pts_team2_other + avg_pts_team2
    logger.info(f" avg_pts_team1_all: {avg_pts_team1_all},avg_pts_team2_all: {avg_pts_team2_all}")
    avg_pts = (avg_pts_team1_all +avg_pts_team2_all) / 2
    logger.info(f" avg_pts: {avg_pts},rate: {rate}")


    avg_3pm = (row1["FG3M"] + row2["FG3M"])
    score = 0

    if avg_pts - rate > offset:
        favorite = 2
        score = avg_pts - rate

    if rate - avg_pts > offset:
        favorite = 1
        score = rate - avg_pts


    if abs(avg_pts - rate) > 15:
        score = 20

    if abs(row1["PTS"] - row2["PTS"]) < 10:
        score = 10 +abs(row1["PTS"] - row2["PTS"])

    if abs(avg_pts_team1_all-avg_pts_team2_all) < 10:
        score = 10 + abs(avg_pts_team1_all-avg_pts_team2_all)


    return jsonify({
        "team_a": {
            "name": team1,
            "PTS": round(float(avg_pts_team1), 2),
            "PTS_GAME": round(float(avg_pts_team1_all), 2),
            "FG3M": float(row1["FG3M"])
        },
        "team_b": {
            "name": team2,
            "PTS": round(float(avg_pts_team2), 2),
            "PTS_GAME": round(float(avg_pts_team2_all), 2),
            "FG3M": float(row2["FG3M"])
        },
        "avg_pts": round(float(avg_pts), 2),
        "avg_3pm": round(float(avg_3pm), 2),
        "favorite": favorite,
        "game": game,
        "rate": rate,
        "score": round(float(score), 2),

    }), 200
@app.route("/nba/analyze", methods=["POST"])
def sort_results():
    req_data = request.get_json()
    results_not_sorted =req_data["results_not_sorted"]
    results_sorted = sorted(results_not_sorted, key=lambda x: x["score"], reverse=True)

    headers =  ["Favor.", "Game", "Score", "Bet", " Under/Over Rate","Teams Rate","Home Points", "Home - Game Points","Away Points", "Away - Game Points"]
    rows = [
        [
            str(item["favorite"]),
            str(item["game"]),
            f"{item['score']:.2f}",
            str(item["bet"]),
            str(item["rate"]),
            str(item["avg_pts"]),
            str(item["team_a"].get("PTS", 0)),
            str(item["team_a"].get("PTS_GAME", 0)),

            str(item["team_b"].get("PTS", 0)),
            str(item["team_b"].get("PTS_GAME", 0)),

        ]
        for item in results_sorted
    ]


    return jsonify({
            "results_sorted": results_sorted,
            "headers": headers,
            "rows": rows,
        }), 200
# =======================================
# NBA API - End
# ======================================

@app.route("/config")
def config():
    UI_BASE_URL = os.getenv("URL_WINNER")
    CORNER_URL = os.getenv("URL_CORNER")
    AIRTABLE_API_KEY = os.getenv("AIR_TABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")


    return jsonify({
        "ui_base_url": UI_BASE_URL,
        "ui_corner_url" : CORNER_URL,
        "airtable_api_key": AIRTABLE_API_KEY,
        "airtable_base_id": AIRTABLE_BASE_ID,
        "headless": True,
        "airtable_table_name": AIRTABLE_TABLE_NAME
    })

@app.route("/check-license/<hwid>")
def check_license(hwid):

    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
    api = Api(AIRTABLE_API_KEY)

    table = api.table(AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME)
    formula = f"{{HWID}}='{hwid}'"

    records = table.all(formula=formula)

    if records:

        fields = records[0]["fields"]
        status = fields.get("Status", "")

        return jsonify({
            "hwid": hwid,
            "status": status,
            "valid": status == "Valid"
        })

    table.create({"HWID": hwid,"Status": "Pending"})

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
