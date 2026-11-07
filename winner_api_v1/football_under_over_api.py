from winner_api_v1.globals import DAYS, LEAGUE
from winner_api_v1.utils.atable_api import tableApi
from winner_api_v1.utils.render_api import RenderApi
from winner_api_v1.utils.files_utils import FilesUtils
from winner_api_v1.utils.playwright_ui_utils import PlaywrightMainUI

playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
results_not_sorted =[]
render_api = RenderApi()

if LEAGUE == 'All':
    leagues = ['England-PLeague','Spain','Italy-Serie A']
    print ("Running at All Mode")
else:
    leagues = [LEAGUE]

for league in leagues:
    league_code=render_api.get_league_code(league)
    config = render_api.get_config()
    is_table = tableApi(config).check_atable()
    table_data, is_found =playwright_main.set_main_page(DAYS, 2, config,league)
    matches, standings = render_api.get_all_football_league_data(league_code)



    if is_found and is_table:
        for data in table_data:
            print (f"******* Game : {data["game"]} - {data['team_a']} VS {data['team_b']} *******")
            if data["description"] == '2 Teams Under/Over 2-3 Range':

                teams_data_excel= files_utils.get_teams_names_from_excel("football_all.xlsx",data.get("team_a"),data.get("team_b"),league )
                team_data_a =render_api.get_teams_data(teams_data_excel.get("team_a"),matches,standings)
                team_data_b =render_api.get_teams_data(teams_data_excel.get("team_b"),matches,standings)
                under_response = render_api.calc_football_under(team_data_a, team_data_b, 0,data["description"])
                favorite = under_response["favorite"]
                if (favorite != 0):
                    bet = data[f"bet{favorite}"]
                    if favorite == 3: favorite = "X"
                    results_not_sorted.append({"bet": bet, "score":under_response["score"], "favorite":favorite, "plan": data["game"],
                                               'game': data["game_in_program"], "avg_total": under_response["avg_total"],"away_count": under_response["away_count"],"home_count": under_response["home_count"]})

headers =  ["Favorite", "Game", "Plan", "Score", "Bet", "Avg Goals", "Home Count %", "Away Count %"]
results_sorted = sorted(results_not_sorted, key=lambda x: x["score"], reverse=True)
files_utils.print_results(results_sorted,headers,"** Summery Results for Under-Over 2-3 goals **")





