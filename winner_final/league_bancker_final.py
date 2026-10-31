from winner_final.globals import DAYS, LEAGUE
from winner_final.utils.algo_utils import AlgoUtils
from winner_final.utils.files_utils import FilesUtils
from winner_final.utils.football_data_api import FootballDataApi
from winner_final.utils.playwright_telersport_ui import PlaywrightMainUI

football_data_api = FootballDataApi()
playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
algo_utils = AlgoUtils()
results = []
table_data , is_found =playwright_main.set_telesport_page( DAYS,2,LEAGUE)
if is_found:
    for data in table_data:
        if data["description"]=='2 Teams Game Results':
            print (f"*** Analyze {data.get('team_a')} vs {data.get('team_b')} ***")
            teams_data_excel= files_utils.get_teams_names_from_excel("football_all.xlsx",data.get("team_a"),data.get("team_b") )

            teams_data = football_data_api.get_teams_data(teams_data_excel.get("League"),[teams_data_excel.get("team_a"),teams_data_excel.get("team_b")])
            scores,favorite  = algo_utils.calc_football_bancker_algo(teams_data[0], teams_data[1])

            print (f"Found {scores} scores  , game {data.get('team_a')} vs {data.get('team_b')}")
            if favorite != 0:
                bet = data.get(f"bet{favorite}")

                results.append({
                    "bet": bet,
                    "score": scores,
                    "favorite": favorite,
                    "plan": data.get("game"),
                    "game": data.get("game_in_program"),
                    "avg_total":"-"
                })




    headers = ["Favorite", "Game", "Plan", "Score", "Bet", "Avg Goals"]
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)

    files_utils.print_results(results_sorted, headers, "** Summary Results for Bancker **")
print ("********  End  *********")