from winner_final.globals import DAYS, FILTER, PATH_PROGRAM_TEXT
from winner_final.utils.algo_utils import AlgoUtils
from winner_final.utils.espn_nba_api import EspnNbaApi
from winner_final.utils.files_utils import FilesUtils
from winner_final.utils.playwright_telersport_ui import PlaywrightMainUI
import sys

playwright_main = PlaywrightMainUI()
files_utils = FilesUtils()
algo_utils = AlgoUtils()

path = files_utils.get_file_name(PATH_PROGRAM_TEXT,"program")
original_stdout = sys.stdout
sys.stdout = open(path, "w", encoding="utf-8")
table_data  =playwright_main.set_telesport_page(0,0,"wnba")

sys.stdout.close()
sys.stdout = original_stdout
files_utils.convert_txt_folder_to_pdf(PATH_PROGRAM_TEXT+"/results")

print ("********  End  *********")