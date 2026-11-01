import time

import pandas as pd
import requests
class FootballDataApi:

    def __init__(self):

        self.url = f"https://api.football-data.org/v4/competitions/"
        self.headers = {"X-Auth-Token": "6e8b3c65a58f4a05b874d72fe4170fd7"}

    def get_teams_data(self, league, teams=None) -> list[dict]:
        response = requests.get(
            f"{self.url}{league}/standings", headers=self.headers
        )
        if (response.status_code == 429):
            print ("429 found sleep and re-running.")
            time.sleep(30)
            response = requests.get(f"{self.url}{league}/standings", headers=self.headers)

        data = response.json()

        teams_data = []
        for team in teams:

            for entry in data["standings"][0]["table"]:
                team_name = entry["team"]["name"]

                if team_name==team:

                    played = entry["playedGames"]
                    goals_for = entry["goalsFor"]
                    goals_against = entry["goalsAgainst"]
                    total_goals = goals_for + goals_against

                    teams_data.append(
                        {
                            "Position": int(entry["position"]),
                            "Team": team_name,
                            "Points": int(entry["points"]),
                            "avgGoalsFor": round(goals_for / played, 2),
                            "avgGoalsAgainst": round(goals_against / played, 2),
                            "avgTotalGoals": round(total_goals / played, 2),
                        }

                    )


        for teams in teams_data:
            print (f"Team {teams['Team']} found at position {teams['Position']},points:{teams['Points']}. For goals:{teams['avgGoalsFor']},Agienst goals:{teams['avgGoalsAgainst']}")


        return teams_data
    # PL (England), PD (Spain), SA (Italy)
    def get_team_data(self,league,team=""):
        response = requests.get(f"{self.url}{league}/standings", headers=self.headers)
        response.raise_for_status()
        data = response.json()

        teams_data = []

        for entry in data["standings"][0]["table"]:
            team_name = entry["team"]["name"]

            if team and team.lower() not in team_name.lower():
                continue

            played = entry["playedGames"]
            goals_for = entry["goalsFor"]
            goals_against = entry["goalsAgainst"]
            total_goals = goals_for + goals_against

            if played > 0:
                teams_data.append(
                    {
                        "Position": int(entry["position"]),
                        "Team": team_name,
                        "Points": int(entry["points"]),
                        "avgGoalsFor": round(goals_for / played, 2),
                        "avgGoalsAgainst": round(goals_against / played, 2),
                        "avgTotalGoals": round(total_goals / played, 2),
                    }
                )

        df = pd.DataFrame(teams_data)

        if not df.empty:
            print(f" {teams_data[0]['Team']} Position: {teams_data[0]["Position"]}, Points: {teams_data[0]["Points"]}")
            print (f"Avg Goals : For -{teams_data[0]['avgGoalsFor']},Against -{teams_data[0]['avgGoalsAgainst']},Total -{teams_data[0]['avgTotalGoals']}")
        else:
            print("No team matching the search criteria was found.")
        return df

