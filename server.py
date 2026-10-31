from fastapi import FastAPI
import requests

app = FastAPI()

API_KEY = "6e8b3c65a58f4a05b874d72fe4170fd7"


@app.get("/get-stats/{team_id}")
def get_football_stats(team_id: int, num_matches: int = 5, only_pl: bool = True):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED"
    headers = {"X-Auth-Token": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to fetch data from football-data API", "status": response.status_code}

    data = response.json()
    matches = data.get("matches", [])

    if only_pl:
        matches = [m for m in matches if m.get("competition", {}).get("code") == "PL"]

    matches = sorted(matches, key=lambda x: x.get("utcDate", ""), reverse=True)[:num_matches]

    count_1_goal = 0
    count_2_3_goals = 0
    count_over_3_goals = 0
    count_0_goals = 0
    total_matches = 0
    total_goals_sum = 0

    processed_matches = []

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
        processed_matches.append({
            "competition": comp_name,
            "match": f"{home_team} {home_goals} - {away_goals} {away_team}",
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

    avg_goals = (total_goals_sum / total_matches) if total_matches > 0 else 0

    return {
        "total_matches_analyzed": total_matches,
        "average_goals_per_match": round(avg_goals, 2),
        "distribution": {
            "1_goal": count_1_goal,
            "2_3_goals": count_2_3_goals,
            "over_3_goals": count_over_3_goals,
            "0_goals": count_0_goals
        },
        "matches": processed_matches
    }