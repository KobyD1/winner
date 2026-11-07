from winner_api_v1.globals import DAYS, LEAGUE, OFFSET
from winner_api_v1.utils.atable_api import tableApi
from winner_api_v1.utils.render_api import RenderApi
from winner_api_v1.utils.files_utils import FilesUtils
# from winner_api_v1.utils.football_data_api import FootballDataApi
from winner_api_v1.utils.playwright_ui_utils import PlaywrightMainUI

# football_data_api = FootballDataApi()
playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
results_not_sorted =[]
LEAGUE = "IsraelCorner"

render_api = RenderApi()
config = render_api.get_config()
is_table = tableApi(config).check_atable()
table_data, is_found =playwright_main.set_main_page(DAYS, 2, config,LEAGUE)

corner_data, is_corner =playwright_main.get_corners_table(config)
table_data_converted = render_api.get_israel_league_data(table_data)
if is_found and is_table:
    results_not_sorted = render_api.analyze_israel_corner_data(table_data_converted,corner_data,OFFSET)
    results_sorted = render_api.sort_and_prapre_to_print(results_not_sorted)
    if results_sorted:files_utils.print_results_by_row(results_sorted)





print ("end")






