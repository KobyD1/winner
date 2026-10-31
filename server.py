from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

# משיכת מפתח ה-API ממשתני הסביבה או שימוש במפתח שהגדרת
API_KEY = os.getenv("API_KEY", "6e8b3c65a58f4a05b874d72fe4170fd7")
HEADERS = {"X-Auth-Token": API_KEY}


def calculate_team_stats(team_id: int, num_matches: int = 8, only_premier_league: bool = True):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"שגיאה בשליפת נתונים לקבוצה מספר {team_id}"
        )

    data = response.json()
    matches = data.get("matches", [])

    # סינון לפי ליגה אם הוגדר True
    if only_premier_league:
        matches = [m for m in matches if m.get("competition", {}).get("code") == "PL"]

    # מיון המשחקים לפי תאריך מהחדש לישן וחיתך לפי הכמות המבוקשת
    matches = sorted(matches, key=lambda x: x.get("utcDate", ""), reverse=True)
    matches = matches[:num_matches]

    count_1_goal = 0
    count_2_3_goals = 0
    count_over_3_goals = 0
    count_0_goals = 0
    total_matches = 0
    total_goals_sum = 0

    match_details = []

    for match in matches:
        score_data = match.get("score", {})
        full_time = score_data.get("fullTime", {})

        home_team = match.get("homeTeam", {}).get("name", "Unknown")
        away_team = match.get("awayTeam", {}).get("name", "Unknown")

        home_goals = full_time.get("home") if "home" in full_time else full_time.get("homeTeam")
        away_goals = full_time.get("away") if "away" in full_time else full_time.get("awayTeam")

        if home_goals is None or away_goals is None:
            continue

        total_game_goals = home_goals + away_goals
        total_matches += 1
        total_goals_sum += total_game_goals

        comp_name = match.get("competition", {}).get("name", "")
        match_details.append({
            "competition": comp_name,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "total_goals": total_game_goals
        })

        if total_game_goals == 1:
            count_1_goal += 1
        elif 2 <= total_game_goals <= 3:
            count_2_3_goals += 1
        elif total_game_goals > 3:
            count_over_3_goals += 1
        else:
            count_0_goals += 1

    pct_1 = (count_1_goal / total_matches * 100) if total_matches > 0 else 0
    pct_2_3 = (count_2_3_goals / total_matches * 100) if total_matches > 0 else 0
    pct_over_3 = (count_over_3_goals / total_matches * 100) if total_matches > 0 else 0
    pct_0 = (count_0_goals / total_matches * 100) if total_matches > 0 else 0

    avg_goals_per_match = (total_goals_sum / total_matches) if total_matches > 0 else 0

    return {
        "team_id": team_id,
        "total_analyzed_matches": total_matches,
        "avg_goals_per_match": round(avg_goals_per_match, 2),
        "statistics": {
            "goals_0_count": count_0_goals,
            "goals_0_pct": round(pct_0, 2),
            "goals_1_count": count_1_goal,
            "goals_1_pct": round(pct_1, 2),
            "goals_2_3_count": count_2_3_goals,
            "goals_2_3_pct": round(pct_2_3, 2),
            "goals_over_3_count": count_over_3_goals,
            "goals_over_3_pct": round(pct_over_3, 2)
        },
        "matches_history": match_details
    }


@app.get("/get-teams-stats/{team1_id}/{team2_id}")
def get_two_teams_statistics(team1_id: int, team2_id: int, num_matches: int = 8, only_premier_league: bool = True):
    # הפעלת החישוב עבור שתי הקבוצות במקביל
    stats_team1 = calculate_team_stats(team1_id, num_matches, only_premier_league)
    stats_team2 = calculate_team_stats(team2_id, num_matches, only_premier_league)

    return {
        "team_1": stats_team1,
        "team_2": stats_team2
    }