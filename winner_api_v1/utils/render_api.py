import requests


class RenderApi:

    def __init__(self):
        self.render_url = "https://pythonprojectnew-ps0h.onrender.com"

    def get_league_code(self, league_name):
        response = requests.get(f"{self.render_url}/league-code/{league_name}")
        return response.json().get("league_code", None)


    def calc_football_under(self,team_a,team_b,desc="2 Teams Under/Over 2-3 Range"):

        payload = {
            "team_a": team_a,
            "team_b": team_b,
            "desc": desc
        }

        response = requests.post(f"{self.render_url}/football-under",json=payload)

        return response.json()

    def calc_football_banker(self,team_a_data,team_b_data):


        payload = {
            "team_a": team_a_data,
            "team_b": team_b_data
        }

        response_json = requests.post(f"{self.render_url}/football-banker",json=payload).json()

        return response_json["score"], response_json["favorite"]

    def get_config(self):
        response = requests.get(f"{self.render_url}/config")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching UI config: {response.status_code}")
            return None



    def get_all_football_league_data(self,league_code):

        print("getting all data from server , can take 30 sec.")

        standings_response = requests.get(f"{self.render_url}/{league_code}/standings").json()
        matches_response = requests.get(f"{self.render_url}/{league_code}/results").json()

        standings = standings_response["standings"]
        matches = matches_response["results"]

        return matches, standings

    def get_teams_data(self, team_name, matches, standings):

        team_table_data = None

        for team in standings:

            if team["team"] == team_name:
                team_table_data = team
                break

        if team_table_data is None:
            print("הקבוצה לא נמצאה")
            return None

        games = 0
        total_goals_sum = 0

        count_0_1 = 0
        count_2_3 = 0
        count_4_plus = 0

        for match in matches:

            home_team = match["home_team"]
            away_team = match["away_team"]

            if team_name not in [home_team, away_team]:
                continue

            home_goals = match["home_goals"]
            away_goals = match["away_goals"]

            if home_goals is None or away_goals is None:
                continue

            total_goals = home_goals + away_goals

            games += 1
            total_goals_sum += total_goals

            if total_goals <= 1:
                count_0_1 += 1

            elif 2 <= total_goals <= 3:
                count_2_3 += 1

            else:
                count_4_plus += 1
        if games >0 :
            avg_goals = total_goals_sum / games
            pct_0_1 = count_0_1 / games * 100
            pct_2_3 = count_2_3 / games * 100
            pct_4_plus = count_4_plus / games * 100


        team_data = {
            "Position": int(team_table_data["position"]),
            "Team": team_name,
            "Points": int(team_table_data["points"]),
            "avgGoals": round(avg_goals, 2),
            "count_0_1": round(pct_0_1, 2),
            "count_2_3": round(pct_2_3, 2),
            "count_4_plus": round(pct_4_plus, 2),
        }

        print(f"Team data for {team_name}: {team_data}")
        return team_data

    def get_nba_teams_data(self,teams_code,table_data,excel_data,season):

        payload ={
            "team1": excel_data["team_a"],
            "team2": excel_data["team_b"],
            "season": season,
            "table_data": table_data,
            "data": teams_code
        }

        response = requests.post(f"{self.render_url}/nba/calc-under", json=payload)
        data = response.json()

        return data

    def analayze_nba_data(self,results_not_sorted):
        payload = {
            "results_not_sorted": results_not_sorted
        }

        response = requests.post(f"{self.render_url}/nba/analyze", json=payload)
        data = response.json()

        return data




    def check_license(self,hwid ):

        response = requests.get( f"{self.render_url}/check-license/{hwid}" )

        return response.json()["status"]