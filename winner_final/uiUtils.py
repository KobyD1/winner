
from playwright.sync_api import sync_playwright, expect

from winner_final.pages.playwright_main_ui import telesport_main_page


class playwrightUtils():
    def __init__(self):
        pass

    def demo(self):
        print ("gfgfgf")

    def setup_winner(self,url):
        print("### Test start ###")

        # 1. איתחול ה-Context Manager באמצעות with וסוגריים לפונקציית המקור בלבד
        with sync_playwright() as playwright:
            # 2. הרמת הדפדפן - משתמשים ב-playwright כאובייקט (בלי סוגריים!)
            browser = playwright.chromium.launch(headless=False)

            # 3. יצירת קשר (Context) ועמוד חדש
            context = browser.new_context()
            page = context.new_page()

            # 4. ניווט לכתובת
            page.goto(url)

            # --- כאן מגיע הקוד שלך (למשל הלולאה שסורקת את השורות) ---
            print("העמוד נטען בהצלחה!")

            # 5. סגירה מסודרת בסיום (חלק בלתי נפרד מניהול ההקשר)
            page.close()
            context.close()
            browser.close()
