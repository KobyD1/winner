import re
from asyncio.windows_events import NULL


class telesport_main_page:

    def __init__(self,page):
        self.page = page

    def set_table_filters(self,index = 2):
        title=""
        if index == 1 :
            title = "כדורסל"
        if index == 2:
            title = "כדורגל"
        self.page.locator("div.ddlTitleFilters").wait_for(state="visible")
        self.page.locator("div.ddlTitleFilters").click()
        self.page.locator("#ddlBoxFilters").get_by_text(title).click()
        print (f"success to click on {title}")

    def set_table_league(self,league="wnba"):
        is_found = True
        self.page.get_by_text("ליגות").nth(0).click()
        match league:
            case "wnba":
                loc = self.page.locator("#checkbox_1663")
            case "Spain":
                loc = self.page.locator("#checkbox_248")

            case "England-PLeague":
                loc = self.page.locator("#checkbox_90")
            case _:
                print("league not found")
                loc = None


        if loc.is_visible():
            loc.click()
        else:
            print (45 * "*")
            print ("*****   ERROR : לא נמצאו ליגה פעילה בתכניה   *****")
            print (45 * "*")
            is_found = False



        self.page.locator("div.sportlive_LeagueSelect_btnFilter").click()
        print (f"success to click on {league}")
        return is_found

    def set_date(self):
        self.page.locator("div.sportLive_calendar_left").click()

    def row_data_parser(self,row,team_a,team_b,rate,description,team_with_added_points):
        row_data = {}
        game = row.locator(".tdWinId").inner_text().replace(".", "")

        status_time = row.locator(".tdWinnerStatus").inner_text().strip()

        row_data["status_time"] = status_time
        row_data["team_a"] = team_a
        row_data["team_b"] = team_b
        row_data["rate"] = rate
        row_data["description"] = description
        row_data["team_with_added_points"] = team_with_added_points
        row_data["game"] = game
        if ")" in  row_data["game"]:
            row_data["program"] = row_data["game"].split(")")[0].replace("(", "")
            row_data["game_in_program"] = row_data["game"].split(")")[1].strip()
        return row_data

    def get_football_table_content(self):

        table_content = []

        rows = self.page.locator("tr.winnerBodyTr:visible").all()

        actual_index = 1
        for row in rows:

            if not row.is_visible():
                continue

            teams = row.locator(".th_td_WinnerteamsAndBetType").inner_text().strip()
            teams=teams.replace("\xa0", "")

            match True:


                case _ if any(term in teams for term in ["מאצ'אפ", "כן/לא", "מחצית", "דקה"]):
                    print("Not Rellevant game found")
                    continue

                case _ if any(term in teams for term in ["שערים", "טווחים"]):
                    team_a, team_b, rate, description, team_with_added_points = self.teams_data_parser_uder_over(teams)
                    row_data = self.row_data_parser(row, team_a, team_b, rate, description, team_with_added_points)
                    row_data, bet_empty_counter = self.bet_parser(row, row_data)

                case _ if "(" not in teams:
                    team_a, team_b, rate, description, team_with_added_points = self.teams_data_parser_game(teams)
                    row_data = self.row_data_parser(row, team_a, team_b, rate, description, team_with_added_points)
                    row_data, bet_empty_counter = self.bet_parser(row, row_data)

                case _:
                    print("Not Rellevant game found")
                    continue





            if  ":"  in row_data["status_time"] and len(row_data)>0 and bet_empty_counter <1:
                print(f"---- משחק פעיל נמצא בתכניה ----")
                if "bet3" in row_data:
                    row_data['bet2'], row_data['bet3'] = row_data['bet3'], row_data['bet2']

                    print(

                    f" יחסי הימורים ל: תיקו- {row_data['bet3']}, "
                        f" 2 - {row_data['bet2']}, "
                        f" gov_1 - {row_data['bet1']}"
                    )


                else:
                    print(f"יחסי הימורים: 2- {row_data['bet2']} , gov_1- {row_data['bet1']}")


                print(f" שעת משחק: {row_data["status_time"]}")
                print(f"  משחק: {teams}")
                print(f"  פרטי משחק (תכניה-משחק): {row_data["program"]} - {row_data["game_in_program"]}")
                row_data["team_with_added_points"] = team_with_added_points
                table_content.append(row_data)
            actual_index += 1
        return table_content

    def get_table_content(self):

        table_content = []

        status_time=""
        rows = self.page.locator("tr.winnerBodyTr:visible").all()

        actual_index = 1
        for row in rows:

            if not row.is_visible():
                continue

            teams = row.locator(".th_td_WinnerteamsAndBetType").inner_text().strip()
            teams=teams.replace("\xa0", "")
            if teams.count("מעל")or teams.count("טווחים") :
                team_a,team_b,rate,description,team_with_added_points = self.teams_data_parser_uder_over(teams)
                row_data = self.row_data_parser(row,team_a,team_b,rate,description,team_with_added_points)


                score = row.locator(".tdWinScore").inner_text().strip()
                row_data, bet_empty_counter = self.bet_parser(row, row_data)

            else:
                team_a,team_b,rate,description,team_with_added_points = self.teams_data_parser_game(teams)
                row_data = self.row_data_parser(row,team_a,team_b,rate,description,team_with_added_points)

                score = row.locator(".tdWinScore").inner_text().strip()
                row_data,bet_empty_counter = self.bet_parser(row,row_data)


            if  ":"  in row_data["status_time"] and len(row_data)>0 and bet_empty_counter <1:
                print(f"---- משחק פעיל נמצא בתכניה ----")
                if "bet3" in row_data:
                    print(
                        f" יחסי הימורים ל: תיקו- {row_data['bet2']}, "
                        f"2 - {row_data['bet3']}, "
                        f"gov_1 - {row_data['bet1']}"
                    )


                else:
                    print(f"יחסי הימורים: 2- {row_data['bet2']} , gov_1- {row_data['bet1']}")


                print(f" שעת משחק: {row_data["status_time"]}")
                print(f"  משחק: {teams}")

                print(f"  פרטי משחק (תכניה-משחק): {row_data["program"]} - {row_data["game_in_program"]}")
                row_data["team_with_added_points"] = team_with_added_points
                table_content.append(row_data)
            actual_index += 1
        return table_content

    def teams_data_parser_uder_over(self, teams):
        match teams:
            case _ if teams.count("(") > 1:
                parts = teams.split("(")
                team_part = parts[1].split(")")[0]
                number_part = parts[2].split(")")[0]
                team = team_part.strip()
                rate = float(number_part)
                team_b = "not found"
                description = 'gov_1 Team Under/Over'
                team_with_added_points = ""

                return team, team_b, rate, description, team_with_added_points

            case _ if "שלשות" in teams:
                parts = teams.split("-")
                team_b = parts[1].strip()
                index_1 = parts[0].index(")") + 1
                index_2 = parts[0].index("(")

                team_a = parts[0][index_1:].strip()
                rate = float(parts[0][index_2 + 1:index_1 - 1].strip())
                description = '2 Teams 3 points Under/Over'
                team_with_added_points = "not found"

                return team_a, team_b, rate, description, team_with_added_points


            case _ if "מעל/מתחת שערים" in teams and "-" not in teams:
                parts = teams.split(")")
                player = parts[1].strip()
                rate = re.findall(r"\d+", parts[0])
                description = 'gov_1 Player Under/Over'
                return player, NULL, rate, description, NULL


            case _ if "מעל/מתחת" in teams:
                parts = teams.split("-")
                team_b = parts[1].strip()
                index_1 = parts[0].index(")") + 1
                index_2 = parts[0].index("(")

                team_a = parts[0][index_1:].strip()
                rate = float(parts[0][index_2 + 1:index_1 - 1].strip())
                description = '2 Teams Under/Over'
                team_with_added_points = "not found"

                return team_a, team_b, rate, description, team_with_added_points


            case _ if "טווחים" in teams:
                teams = teams[teams.index(")")+1:]
                parts = teams.split("-")
                team_b = parts[1].strip()
                team_a = parts[0].strip()

                rate = None
                description = '2 Teams Under/Over 2-3 Range'
                team_with_added_points = None

                return team_a, team_b, rate, description, team_with_added_points

            case _:
                return "not found", "not found", "not found", "not found", "not found"
    def parse_teams_under_over(self):
        pass

    def teams_data_parser_game(self,teams):
        row_data = {}
        team_a = ""
        team_b = ""
        parts = []
        index= teams.index("-")
        parts.append(teams[:index])
        parts.append(teams[index+1:])

        if (parts[1].count("(") > 0):
            team_b = parts[1].strip().split("(")[0].strip()
            team_a = parts[0].strip()

            part_with_ref = parts[1]
            team_with_added_points = team_b
        elif (parts[0].count("(") > 0):

            team_a= parts[0].strip().split("(")[0].strip()
            part_with_ref = parts[0]
            team_with_added_points = team_a
            team_b = parts[1].strip()
        else:
            if parts[0].count(" ") < 3:
                team_a = parts[0].strip()
            team_b = parts[1].strip()
            part_with_ref = None
            team_with_added_points="not found"
            rate = 0.0


        if team_with_added_points==team_a or team_with_added_points==team_b:
            added_points =part_with_ref.split(")")[0].replace(")","")
            num= re.findall(r"\d+", added_points)
            rate = float(num[0])
            row_data['description'] = '2 Teams Game Results'

        description = '2 Teams Game Results'
        return team_a,team_b,rate,description,team_with_added_points


    def add_row_data_to_table(self):
        pass

    def bet_parser(self,row,row_data):

        bets = row.locator('[class*="th_td_WinnerBet"]').all()
        for bet in bets:
            bet_empty_counter = 0
            index = bets.index(bet)
            if "." in bet.inner_text():
                row_data[f"bet{index}"] = bet.inner_text().strip()
            if "-" in bet.inner_text():
                bet_empty_counter += 1

        return row_data,bet_empty_counter


