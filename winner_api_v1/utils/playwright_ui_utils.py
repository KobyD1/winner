import time
from playwright.sync_api import sync_playwright, expect

from winner_api_v1.pages.playwright_main_ui import main_page

class PlaywrightMainUI():
    def __init__(self):
        pass


    def set_main_page(self, days_count, type,ui_config, league="nba"):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False,args=["--start-maximized"])

            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.goto(ui_config["ui_base_url"])
            page.reload()

            old_site_button = page.get_by_role("button", name="לאתר הישן", exact=True)
            old_site_button.click()
            table_data =[]
            ui_main_page = main_page(page)
            for i in range(days_count):
                print (f"Set date to {i+1} days")
                ui_main_page.set_date()


            match type:
                 case 0:
                    print (" Run without filters ")

                 case 1:
                    print (" Run in basketball mode ")
                    ui_main_page.set_table_filters(type)
                    is_found = ui_main_page.set_table_league(league)

                 case 2:
                    print (" Run in football mode ")
                    is_found = ui_main_page.set_table_league(league)

            if is_found:
                table_data = ui_main_page.get_filterd_table_content()
                print (57 * "*")
                print (f"******* Winner Analyzer Completed - found {len(table_data)} games *******")
                print (57 * "*")
            else:
                print (57 * "*")
                print (f"****** Winner Analyzer Completed - no games found *******")
                print (57 * "*")

            return table_data, is_found

