import json
from datetime import date

from nba_api.stats.endpoints import LeagueDashTeamStats


class nbaApi:
    def __init__(self):
        pass

    def get_nba_teams_data(self, season=None):
        # season = "2026-27"
        if season is None:
            today = date.today()
            if today.month < 10:
                season_start_year = today.year -1
            else:
                season_start_year = today.year

        season = f"{season_start_year}-{str(season_start_year + 1)[-2:]}"

        df = LeagueDashTeamStats(
            per_mode_detailed="PerGame",
            season=season
        ).get_data_frames()[0]

        rounds_played = df["GP"].max()

        columns = [
            "TEAM_ID",
            "TEAM_NAME",
            "GP",
            "PTS",
            "FG3M",
        ]

        filtered_df = df[columns]

        return json.loads(filtered_df.to_json(orient="records")),season




