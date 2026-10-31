from winner_final.globals import URL_WINNER
from playwright.sync_api import sync_playwright, expect

from winner_final.pages.playwright_main_ui import telesport_main_page

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.telesport.co.il/%D7%90%D7%96%D7%95%D7%A8%20%D7%95%D7%95%D7%99%D7%A0%D7%A8")
    telesport_page =  telesport_main_page(page)
    telesport_page.set_date()
    telesport_page.set_date()

    telesport_page.set_table_filters("כדורסל")
    table_data = telesport_page.get_table_content()
    print (table_data)
    print ("end")