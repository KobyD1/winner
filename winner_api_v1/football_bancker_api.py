
import sys
from pathlib import Path

from winner_api_v1.utils.atable_api import tableApi
from winner_api_v1.utils.files_utils import FilesUtils
from winner_api_v1.utils.playwright_ui_utils import PlaywrightMainUI
from winner_api_v1.utils.render_api import RenderApi

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
from globals import DAYS, LEAGUE

# football_data_api = FootballDataApi()
playwright_main = PlaywrightMainUI()
render_api = RenderApi()
config = render_api.get_config()
is_table = tableApi(config).check_atable()

files_utils = FilesUtils()
results_not_sorted =[]
if LEAGUE == 'All':
    leagues = ['England-PLeague','Spain','Italy-Serie A']
    print ("Running at All Mode")
else:
    leagues = [LEAGUE]
results_not_sorted = []


for league in leagues:
    league_code=render_api.get_league_code(league)
    table_data, is_found =playwright_main.set_main_page(DAYS, 2, config,league)
    matches, standings = render_api.get_all_football_league_data(league_code)

    results = {}
    results_temp = []

    if is_found and is_table:
        for data in table_data:
            if data["description"]=='2 Teams Game Results':
                print (f"*** Analyze {data.get('team_a')} vs {data.get('team_b')} ***")
                teams_data_excel= files_utils.get_teams_names_from_excel("football_all.xlsx",data.get("team_a"),data.get("team_b"),league )
                team_data_a =render_api.get_teams_data(teams_data_excel.get("team_a"),matches,standings)
                team_data_b =render_api.get_teams_data(teams_data_excel.get("team_b"),matches,standings)
                scores,favorite  = render_api.calc_football_banker(team_data_a, team_data_b)

                print (f"Found {scores} scores  , game {data.get('team_a')} vs {data.get('team_b')}")
                if favorite != 0:
                    bet = data.get(f"bet{favorite}")
                    results = {
                        "Bet": {"id": 4, "value": bet},
                        "Favorite": {"id": 1, "value": favorite},
                        "Game": {"id": 2, "value": data.get("game")},
                        "Points": {"id": 3, "value": scores},
                        "Home Team": {
                            "id": 5,
                            "value": f"{team_data_a.get('Team', '--')} ({team_data_a.get('Position', '0')})",
                        },
                        "Away Team": {
                            "id": 6,
                            "value": f"{team_data_b.get('Team', '--')} ({team_data_b.get('Position', '--')})",
                        },

                    }


                    results_temp.append(results)
    for item in results_temp:
        results_not_sorted.append(item)



results_sorted = render_api.sort_and_prapre_to_print(results_not_sorted)
if results_sorted: files_utils.print_results_by_row(results_sorted)

print ("********  End  *********")