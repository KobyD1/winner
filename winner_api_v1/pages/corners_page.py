class CornersPage():

    def __init__(self, page):
        self.page = page


    def get_corners_data(self):
        table_data = {}
        first_team_text = self.page.locator("div[style='padding: 4px 8px 8px;']").all()[0].inner_text()
        second_teams = self.page.locator("div[style='padding: 0px 8px 8px;']").all()
        all_teams = self.page.locator("div[style='padding: 4px 8px 8px;']").all()[1].inner_text()
        first_team_split = first_team_text.split("\n")
        table_data[first_team_split[1]] = first_team_split[3]
        for team in second_teams:
            team_split = team.inner_text().split("\n")
            table_data[team_split[1]] = team_split[3]

        items = all_teams.split("\n")

        groups = [items[i:i + 4] for i in range(0, len(items), 4)]
        for group in groups:
            table_data[group[1]] = group[3]


        return table_data
