
from winner_api_v1.globals import DAYS, LEAGUE
from winner_api_v1.utils.atable_api import AirTableApi
from winner_api_v1.utils.nba_api import nbaApi
from winner_api_v1.utils.render_api import RenderApi
from winner_api_v1.utils.files_utils import FilesUtils
from winner_api_v1.utils.football_data_api import FootballDataApi
from winner_api_v1.utils.playwright_ui_utils import PlaywrightMainUI

football_data_api = FootballDataApi()
playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
nba_api_utils = nbaApi()
results_not_sorted =[]

render_api = RenderApi()
config = render_api.get_config()
is_table = AirTableApi(config).check_atable()
table_data, is_found =playwright_main.set_main_page(DAYS, 1, config,LEAGUE)
if is_found and is_table:
    for data in table_data:
        print (f"******* Game : {data["game"]} - {data['team_a']} VS {data['team_b']} *******")
        if data["description"] == '2 Teams Under/Over':

            teams_data_excel= files_utils.get_teams_names_from_excel("nba.xlsx",data.get("team_a"),data.get("team_b") )
            df, season = nba_api_utils.get_nba_teams_data()
            print(f"ניתוח תוצאות לעונת  {season}")

            server_data = render_api.get_nba_teams_data(df,data,teams_data_excel, season)
            favorite = server_data["favorite"]
            if (favorite != 0):
                bet = data[f"bet{favorite}"]
                server_data["bet"] = bet
                results_not_sorted.append(server_data)
                print (f"נמצאה התאמה  {data.get('team_a')} נגד  {data.get('team_b')} ערך {favorite} יחס {bet}")

    result_sorted = render_api.analayze_nba_data(results_not_sorted)
    files_utils.print_results_by_row( result_sorted)







