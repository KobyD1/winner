import requests

class EspnNbaApi:

    def __init__(self):
        pass

    def clean_score(self,val):
        try:
            return int(val.get("value") if isinstance(val, dict) else val)
        except:
            return 0

    def get_basketball_team_stats(self, team_id: int,is_under_over ,  league='nba'):
        try:
            if (is_under_over):

                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/{league}/teams/{team_id}/schedule"
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                team_data = self.under_over_parser(data,team_id)
                return team_data

            else:
                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/{league}/teams/{team_id}"
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                team_data = self.game_result_parser(data,team_id)
                return team_data

        except:
            print ("get basketball_team_stats error")
            return {}





    def game_result_parser (self, data,team_id):
        team_data = data.get("team", {})
        record_items = team_data.get("record", {}).get("items", [])

        if record_items:
            current_record = record_items[0]
            stats_list = current_record.get("stats", [])

            def get_stat_value(stat_name):
                stat = next((item for item in stats_list if item.get("name") == stat_name), None)
                return stat.get("value") if stat else None

            balance_summary = current_record.get("summary", "N/A")

            win_percentage = get_stat_value("winPercent")

            league_position = get_stat_value("playoffSeed") or get_stat_value("leagueWinPercentRank")
            games_behind = get_stat_value("gamesBehind")
            total_points_scored = get_stat_value("pointsFor")
            avg_points_per_game = get_stat_value("avgPointsFor")
            seed = int(league_position) if league_position is not None else 'N/A'

            avg_points_against = get_stat_value("avgPointsAgainst")
            # calculate avg diff
            if avg_points_per_game is not None and avg_points_against is not None:
                avg_diff = avg_points_per_game - avg_points_against

            print(f"קבוצה: {team_data.get('displayName')}")
            print("-" * 30)
            print(f"  🏆 מיקום בליגה (Seed): {seed}")
            print(f"📊 מאזן (Summary): {balance_summary}")
            print(f"📊 ממוצע הפרשים  : {avg_diff}")


            # הצגת אחוזי ההצלחה בפורמט של אחוזים (למשל 75.0%)
            print(f"📈 אחוזי הצלחה: {win_percentage * 100:.1f}%")
            print(f"📉 משחקים מהמקום הראשון (Games Behind): {games_behind}")
            print(f"🏀 סך נקודות זכות העונה: {total_points_scored}")
            print(f"📊 ממוצע נקודות למשחק: {avg_points_per_game}")
            return {
                "Seed":seed,
                "balance_summary":balance_summary,
                "avg_diff":avg_diff,
                "win_percentage":win_percentage * 100
            }

        else:
            print("לא נמצאו נתונים.")

    def under_over_parser(self,data,team_id):
        team_info = data.get("team") or {}
        team_name = (
            team_info.get("displayName")
            or team_info.get("shortDisplayName")
            or team_info.get("name")
            or str(team_id)
        )

        total_offensive_points = 0
        total_defensive_points = 0
        games_count = 0
        games_list = []

        events = data.get("events") or []
        for event in events:
            competitions = event.get("competitions") or []
            if not competitions:
                continue

            comp = competitions[0]
            status = comp.get("status", {}).get("type", {})
            if not status.get("completed"):
                continue

            competitors = comp.get("competitors") or []
            if len(competitors) < 2:
                continue


            home = next(c for c in competitors if c.get("homeAway") == "home")
            away = next(c for c in competitors if c.get("homeAway") == "away")

            home_team = home.get("team", {})
            away_team = away.get("team", {})

            home_name = home_team.get("displayName") or home_team.get("name")
            away_name = away_team.get("displayName") or away_team.get("name")

            home_score = self.clean_score(home.get("score"))
            away_score = self.clean_score(away.get("score"))

            # does the team is home or away
            if home_name == team_name:
                offensive_points = home_score
                defensive_points = away_score
                opponent = away_name
                location = "בית"
            elif away_name == team_name:
                offensive_points = away_score
                defensive_points = home_score
                opponent = home_name
                location = "חוץ"
            else:
                continue

            games_count += 1
            total_offensive_points += offensive_points
            total_defensive_points += defensive_points

            games_list.append({
                "date": event.get("date", "")[:10],
                "opponent": opponent,
                "location": location,
                "offensive_points": offensive_points,
                "defensive_points": defensive_points
            })

        if games_count == 0:
            print ("לא נמצאו משחקים לקבוצה")
            return None

        avg_offensive_points = total_offensive_points / games_count
        avg_defensive_points = total_defensive_points / games_count
        avg_total_points = (total_offensive_points + total_defensive_points) / games_count
        avg_diff = (total_offensive_points - total_defensive_points) / games_count
        print (f"******* {team_name} Data Information *******")
        print("ממוצע קליעות:", round(avg_offensive_points, 2))
        print("ממוצע ספיגות:", round(avg_defensive_points, 2))
        print("ממוצע נקודות למשחק:", round(avg_total_points, 2))
        print("ממוצע הפרשים:", round(avg_diff, 2))
        for g in games_list:
            print(
                f"{g['date']} | {g['location']} | נגד {g['opponent']} | {g['offensive_points']} - {g['defensive_points']}")

        return {
            "team": team_name,
            "team_id": team_id,
            "games": games_count,
            "avg_offensive_points": avg_offensive_points,
            "avg_defensive_points": avg_defensive_points,
            "avg_total_points": avg_total_points,
            "avg_diff": avg_diff,
            "games_list": games_list

        }


