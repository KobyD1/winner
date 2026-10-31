import time
from playwright.sync_api import sync_playwright, expect

from winner_final.globals import FILTER
from winner_final.pages.playwright_main_ui import telesport_main_page

class PlaywrightMainUI():
    def __init__(self):
        pass


    def set_telesport_page(self,days_count, type,league="nba"):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized"]
            )

            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.goto("https://www.telesport.co.il/%D7%90%D7%96%D7%95%D7%A8%20%D7%95%D7%95%D7%99%D7%A0%D7%A8")
            page.reload()
            # page.locator("div.sportLive_calendar_left").wait_for(state="visible")

            telesport_page = telesport_main_page(page)
            for i in range(days_count):
                telesport_page.set_date()


            match type:
                 case 0:
                    print (" Run without filters ")
                    table_data = telesport_page.get_table_content()

                 case 1:
                    print (" Run in basketball mode ")
                    telesport_page.set_table_filters(type)
                    is_braek = telesport_page.set_table_league(league)
                    table_data = telesport_page.get_table_content()

                 case 2:
                    print (" Run in football mode ")
                    is_break = telesport_page.set_table_league(league)
                    table_data = telesport_page.get_football_table_content()


            print (57 * "*")
            print (f"******* Winner Analyzer Completed - found {len(table_data)} games *******")
            print (57 * "*")

            return table_data, is_break


