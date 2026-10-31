from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

API_KEY = os.getenv("API_KEY", "6e8b3c65a58f4a05b874d72fe4170fd7")
HEADERS = {"X-Auth-Token": API_KEY}


@app.get("/get-two-teams/{team1_id}/{team2_id}")
def get_two_teams_data(team1_id: int, team2_id: int):
    teams_result = {}

    # מעבר על שתי הקבוצות ושליפת הנתונים לכל אחת
    for index, team_id in enumerate([team1_id, team2_id], start=1):
        url = f"https://api.football-data.org/v4/teams/{team_id}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"שגיאה בשליפת הנתונים עבור קבוצה מספר {team_id}"
            )

        data = response.json()

        # סינון הנתונים הרצויים עבור הקבוצה
        team_info = {
            "id": data.get("id"),
            "name": data.get("name"),
            "shortName": data.get("shortName"),
            "tla": data.get("tla"),
            "crest": data.get("crest"),  # סמל הקבוצה
            "venue": data.get("venue"),  # האצטדיון
            "clubColors": data.get("clubColors"),
            "founded": data.get("founded")
        }

        teams_result[f"team_{index}"] = team_info

    return teams_result