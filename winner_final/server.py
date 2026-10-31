from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

API_KEY = os.getenv("API_KEY", "6e8b3c65a58f4a05b874d72fe4170fd7")
HEADERS = {"X-Auth-Token": API_KEY}


def get_league_standings(competition_code: str = "PL"):
    """שולף את כל הקבוצות, המיקום והנקודות בקריאה אחת לשרת החיצוני"""
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/standings"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {}

    data = response.json()
    standings = data.get("standings", [])

    # איתור הטבלה הראשית (TOTAL)
    table = []
    for standing in standings:
        if standing.get("type") == "TOTAL":
            table = standing.get("table", [])
            break

    # מיפוי נתונים לפי team_id
    teams_standings = {}
    for row in table:
        team_id = row.get("team", {}).get("id")
        teams_standings[team_id] = {
            "Position": row.get("position"),
            "Points": row.get("points")
        }
    return teams_standings


def get_team_formatted_stats(team_id: int, standings_data: dict, num_matches: int = 8,
                             only_premier_league: bool = True):
    matches_url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
    query_params = {"status": "FINISHED"}

    response = requests.get(matches_url, headers=HEADERS, params=query_params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"שגיאה בשליפת משחקים לקבוצה {team_id}")

    data = response.json()
    matches = data.get("matches", [])

    if only_premier_league:
        matches = [m for m in matches if m.get("competition", {}).get("code") == "PL"]

    matches = sorted(matches, key=lambda x: x.get("utcDate", ""), reverse=True)
    matches = matches[:num_matches]

    total_matches = 0
    goals_for_sum = 0
    goals_against_sum = 0
    total_goals_sum = 0
    match_details = []
    team_name = "Unknown"

    for match in matches:
        is_home = match.get("homeTeam", {}).get("id") == team_id

        score_data = match.get("score", {})
        full_time = score_data.get("fullTime", {})

        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        if home_goals is None or away_goals is None:
            continue

        total_matches += 1

        if is_home:
            gf = home_goals
            ga = away_goals
        else:
            gf = away_goals
            ga = home_goals

        goals_for_sum += gf
        goals_against_sum += ga
        total_goals_sum += (gf + ga)

        match_details.append({
            "competition": match.get("competition", {}).get("name", ""),
            "date": match.get("utcDate"),
            "homeTeam": match.get("homeTeam", {}).get("name", "Unknown"),
            "awayTeam": match.get("awayTeam", {}).get("name", "Unknown"),
            "score": f"{home_goals} - {away_goals}",
            "totalGoals": gf + ga
        })

    # שליפת שם הקבוצה המעודכן
    team_info_url = f"https://api.football-data.org/v4/teams/{team_id}"
    team_resp = requests.get(team_info_url, headers=HEADERS)
    if team_resp.status_code == 200:
        team_name = team_resp.json().get("name", team_name)

    avg_for = (goals_for_sum / total_matches) if total_matches > 0 else 0
    avg_against = (goals_against_sum / total_matches) if total_matches > 0 else 0
    avg_total = (total_goals_sum / total_matches) if total_matches > 0 else 0

    # שליפת המיקום והנקודות מתוך מילון הטבלה שהורד מראש
    team_standing = standings_data.get(team_id, {"Position": 0, "Points": 0})

    return {
        "Team": team_name,
        "Points": team_standing.get("Points", 0),
        "Position": team_standing.get("Position", 0),
        "avgGoalsFor": round(avg_for, 2),
        "avgGoalsAgainst": round(avg_against, 2),
        "avgTotalGoals": round(avg_total, 2),
        "finished_matches": match_details
    }


@app.get("/get-teams-data/{team1_id}/{team2_id}")
def get_teams_data_endpoint(team1_id: int, team2_id: int, num_matches: int = 8, only_premier_league: bool = True):
    # שליפת טבלת הליגה פעם אחת עבור כל הקבוצות
    standings_data = get_league_standings("PL") if only_premier_league else {}

    team1_stats = get_team_formatted_stats(team1_id, standings_data, num_matches, only_premier_league)
    team2_stats = get_team_formatted_stats(team2_id, standings_data, num_matches, only_premier_league)

    return {
        "teams_data": [team1_stats, team2_stats]
    }