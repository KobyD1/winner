from winner_final.globals import DAYS, PATH_PROGRAM_TEXT, FILTER, LEAGUE
from winner_final.utils.algo_utils import AlgoUtils
from winner_final.utils.files_utils import FilesUtils
from winner_final.utils.football_data_api import FootballDataApi
from winner_final.utils.playwright_telersport_ui import PlaywrightMainUI

football_data_api = FootballDataApi()
playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
algo_utils = AlgoUtils()
results_not_sorted =[]

table_data, is_found =playwright_main.set_telesport_page( DAYS,2,LEAGUE)
if is_found:
    for data in table_data:
        print (f"******* Game : {data["game"]} - {data['team_a']} VS {data['team_b']} *******")
        if data["description"] == '2 Teams Under/Over 2-3 Range':

            teams_data_excel= files_utils.get_teams_names_from_excel("football_all.xlsx",data.get("team_a"),data.get("team_b") )
            teams_data = football_data_api.get_teams_data(teams_data_excel.get("League"),[teams_data_excel.get("team_a"),teams_data_excel.get("team_b")])

            score , favorite ,avg_total = algo_utils.calc_football_under_over_algo(teams_data[0], teams_data[1],data["description"])
            if (favorite != 0 ):
                bet = data[f"bet{favorite}"]
                if favorite == 3: favorite = "X"
                results_not_sorted.append({"bet":bet,"score": score, "favorite": favorite,"plan": data["game"],'game': data["game_in_program"],"avg_total":avg_total})




    headers =  ["Favorite", "Game", "Plan", "Score", "Bet", "Avg Goals"]
    results_sorted = sorted(results_not_sorted, key=lambda x: x["score"], reverse=True)
    files_utils.print_results(results_sorted,headers,"** Summery Results for Under-Over 2-3 goals **")


print ("********  End  *********")