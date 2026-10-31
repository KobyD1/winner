from winner_final.globals import DAYS, PATH_PROGRAM_TEXT, FILTER
from winner_final.utils.algo_utils import AlgoUtils
from winner_final.utils.espn_nba_api import EspnNbaApi
from winner_final.utils.files_utils import FilesUtils
from winner_final.utils.playwright_telersport_ui import PlaywrightMainUI

espn_nba_api = EspnNbaApi()
playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
algo_utils = AlgoUtils()
table_data =playwright_main.set_telesport_page( FILTER,DAYS,"wnba")
results_not_sorted =[]
for data in table_data:
    excel_data = files_utils.get_team_ids(data, "wnba.xlsx")
    if data["description"]== '2 Teams Under/Over':
        is_under_over = True
    elif data["description"]== '2 Teams Game Results':
        is_under_over = False
    stats_a = espn_nba_api.get_basketball_team_stats(excel_data["ID_A"],is_under_over, 'wnba')
    stats_b = espn_nba_api.get_basketball_team_stats(excel_data["ID_B"], is_under_over,'wnba')
    if stats_a == {} or stats_b == {} or stats_a == None or stats_b == None :
        print ("did not analyze :results by API did not found, missing info at form ... ")
        continue

    results =algo_utils.calculate_game_basketball_algo(stats_a,stats_b,data)
    results_not_sorted.append(results)
results_sorted = sorted(results_not_sorted, key=lambda x: x["score"], reverse=True)
files_utils.print_results(results_sorted)
files_utils.wrote_to_text_file(table_data, PATH_PROGRAM_TEXT,"program")


print ("********  End  *********")