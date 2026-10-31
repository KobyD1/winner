from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

API_KEY = os.getenv("API_KEY", "6e8b3c65a58f4a05b874d72fe4170fd7")
HEADERS = {"X-Auth-Token": API_KEY}


def get_team_formatted_stats(team_id: int, num_matches: int = 8, only_premier_league: bool = True):
    # כתובת לשליפת משחקים
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

    team_name = "Unknown"

    for match in matches:
        is_home = match.get("homeTeam", {}).get("id") == team_id

        # הגדרת שם הקבוצה
        if is_home:
            team_name = match.get("homeTeam", {}).get("name", "Unknown")
        else:
            team_name = match.get("awayTeam", {}).get("name", "Unknown")

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

    # שליפת נתוני הטבלה/מיקום ונקודות אם נדרש (או ערכים מחושבים)
    # לצורך הדוגמה נשלף את פרטי הקבוצה הכלליים מה-API
    team_info_url = f"https://api.football-data.org/v4/teams/{team_id}"
    team_resp = requests.get(team_info_url, headers=HEADERS)
    if team_resp.status_code == 200:
        team_name = team_resp.json().get("name", team_name)

    avg_for = (goals_for_sum / total_matches) if total_matches > 0 else 0
    avg_against = (goals_against_sum / total_matches) if total_matches > 0 else 0
    avg_total = (total_goals_sum / total_matches) if total_matches > 0 else 0

    # מבנה הנתונים המדויק כמו בצילום המסך שלך
    return {
        "Team": team_name,
        "Points": 0,  # ניתן לעדכן בהתאם לטבלת הליגה אם נדרש
        "Position": 0,  # ניתן לעדכן בהתאם למיקום בטבלה
        "avgGoalsFor": round(avg_for, 2),
        "avgGoalsAgainst": round(avg_against, 2),
        "avgTotalGoals": round(avg_total, 2)
    }


@app.get("/get-teams-data/{team1_id}/{team2_id}")
def get_teams_data_endpoint(team1_id: int, team2_id: int, num_matches: int = 8, only_premier_league: bool = True):
    team1_stats = get_team_formatted_stats(team1_id, num_matches, only_premier_league)
    team2_stats = get_team_formatted_stats(team2_id, num_matches, only_premier_league)

    # מחזיר רשימה (list) של 2 מילונים בדיוק כמו teams_data בצילום המסך
    teams_data = [team1_stats, team2_stats]

    return {
        "teams_data": teams_data
    }