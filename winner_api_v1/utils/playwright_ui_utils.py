import time
from playwright.sync_api import sync_playwright, expect

from winner_api_v1.globals import HEADLESS
from winner_api_v1.pages.corners_page import CornersPage
from winner_api_v1.pages.playwright_main_ui import MainPage

class PlaywrightMainUI():
    def __init__(self):
        pass



    def get_corners_table(self,ui_config):
        with sync_playwright() as p:
            print ("start analyze for corners")
            is_headless = (ui_config["headless"] if HEADLESS is None else HEADLESS)
            browser = p.chromium.launch(headless=is_headless, args=[
                        "--disable-blink-features=AutomationControlled"
                    ])
            context = browser.new_context(viewport={ "width": 1920,"height": 1080 },user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36")
            page = context.new_page()
            page.goto(ui_config["ui_corner_url"], wait_until="domcontentloaded")
            page.reload()
            print(f"{page.title()} found " )
            corners_button = page.locator("//div[./span[text()='Corners Per Game']]//button[normalize-space()='See all']").first
            expect(corners_button).to_be_visible(timeout=5000)
            corners_button.click()
            ui_corner_page = CornersPage(page)
            corner_data = ui_corner_page.get_corners_data()
            is_corner_found = len(corner_data) > 0
            if is_corner_found:
                print (f"******* Corners data Completed - found {len(corner_data)} games *******")
            else:
                print (f"*****  Corners data Completed - no Corners games found *****")


            return corner_data , is_corner_found


    def set_main_page(self, days_count, type,ui_config, league):
        with sync_playwright() as p:
            print ("start analyze for games")
            is_headless = (ui_config["headless"] if HEADLESS is None else HEADLESS)
            browser = p.chromium.launch(headless=is_headless)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            page = context.new_page()
            page.goto(ui_config["ui_base_url"])
            page.reload()

            old_site_button = page.get_by_role("button", name="לאתר הישן", exact=True)
            old_site_button.click()
            next_button = page.locator("div.sportLive_calendar_left")
            if not next_button.is_visible():
                print ("Clicking again on old site button")
                old_site_button.click()

            table_data =[]
            ui_main_page = MainPage(page)
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
                print (f"******* Games Analyzer Completed - found {len(table_data)} games *******")
                print (57 * "*")
            else:
                print (57 * "*")
                print (f"****** Games Analyzer Completed - no games found *******")
                print (57 * "*")

            return table_data, is_found
