from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("FOOTBALL_API_KEY")


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Football Stats API Running"
    })


@app.route("/stats")
def stats():

    team_id = request.args.get("team_id", 66, type=int)
    only_premier_league = (
        request.args.get("premier_only", "true").lower() == "true"
    )
    num_matches = request.args.get("matches", 8, type=int)

    url = (
        f"https://api.football-data.org/v4/teams/"
        f"{team_id}/matches?status=FINISHED"
    )

    headers = {
        "X-Auth-Token": API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": f"Football API returned {response.status_code}",
            "details": response.text
        }), response.status_code

    data = response.json()
    matches = data.get("matches", [])

    if only_premier_league:
        matches = [
            m for m in matches
            if m.get("competition", {}).get("code") == "PL"
        ]

    matches = sorted(
        matches,
        key=lambda x: x.get("utcDate", ""),
        reverse=True
    )[:num_matches]

    count_0 = 0
    count_1 = 0
    count_2_3 = 0
    count_4_plus = 0

    total_matches = 0
    total_goals = 0

    result_matches = []

    for match in matches:

        full_time = match.get("score", {}).get("fullTime", {})

        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        if home_goals is None or away_goals is None:
            continue

        goals = home_goals + away_goals

        total_matches += 1
        total_goals += goals

        if goals == 0:
            count_0 += 1
        elif goals == 1:
            count_1 += 1
        elif 2 <= goals <= 3:
            count_2_3 += 1
        else:
            count_4_plus += 1

        result_matches.append({
            "date": match.get("utcDate"),
            "competition": match.get("competition", {}).get("name"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "total_goals": goals
        })

    avg_goals = (
        round(total_goals / total_matches, 2)
        if total_matches > 0 else 0
    )

    return jsonify({
        "team_id": team_id,
        "matches_checked": total_matches,
        "average_goals": avg_goals,
        "stats": {
            "0_goals": count_0,
            "1_goal": count_1,
            "2_3_goals": count_2_3,
            "4_plus_goals": count_4_plus
        },
        "matches": result_matches
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)