# -*- coding: utf-8 -*-

class AlgoUtils:
    def __init__(self):
        pass

    def calc_football_bancker_algo(self, team_a_data, team_b_data):
         scores = 0
         favorite = 0
         position_diff = int(team_a_data["Position"])-int(team_b_data["Position"])
         position_diff_abs = abs(position_diff)
         points_diff = int(team_a_data["Points"]) - int(team_b_data["Points"])
         points_diff = abs(points_diff)
         if position_diff_abs>9:
             print ("Teams  found for Bancker Algo by position")
             scores = position_diff_abs*10
         if (position_diff_abs > 9) and (position_diff_abs>9):
             print("Teams  found for Bancker Algo by points")
             scores = scores + (points_diff * 10)
             # add points in case of home and calculate favorite
         if position_diff < 0 and (position_diff_abs>9):
             scores+=20
             favorite = 1
         if position_diff > 0 and (position_diff_abs>9):
             favorite = 2

         print(f"{scores}  scores found favorite = {favorite} ")
         return scores,favorite


    def calc_football_under_over_algo(self,team_a,team_b, desc):
        bonus = 0
        favorite = ""
        team_a_avg_total = team_a["avgTotalGoals"]
        team_b_avg_total = team_b["avgTotalGoals"]
        avg_total = (team_a_avg_total + team_b_avg_total) / 2
        if abs(team_a_avg_total - team_a_avg_total)<0.6:
            bonus += 10
            print (f"2 teams under over found with similar average total goals: {team_a["Team"]} ,{team_b["Team"]}")

        if abs(team_a_avg_total - team_a_avg_total)>1.5:
            bonus -= 10
            print (f"*** 2 teams found with none similar average goals!!! {team_a["Team"]} ,{team_b["Team"]}***")

        if desc == "2 Teams Under/Over 2-3 Range":

            match avg_total:
                case x if x < 1.0:
                    favorite = 1
                    bonus += 20
                case x if 1.6 <= x < 2.5:
                    favorite = 3
                case x if x > 3.1:
                    favorite = 2
                    high_bonus = (avg_total-3)*15
                    bonus =bonus+ 30 +high_bonus
                case _:
                    print("Other scoring range")
                    favorite = 0





        elif desc == "2 Teams Under/Over":
            pass
        print (f"Summery  - Bonus: {bonus} ,favorite: {favorite} , avg_total: {avg_total}")
        return bonus , favorite,avg_total


    def calculate_game_basketball_algo(self,team_a_data,team_b_data,data):
        result = {}

        match data["description"]:
            case "2 Teams Game Results":

                print(f"Calculate Game results {team_a_data} and {team_b_data}")

                team_added = data["team_with_added_points"]
                rate = data["rate"]


                if data["team_b"] == team_added:
                    added_diff = team_b_data['avg_diff']
                    other_diff = team_a_data['avg_diff']
                    bet_added = data["bet2"]
                    bet_other = data["bet1"]
                    favorite_added = "2"
                    favorite_other = "gov_1"

                else:
                    added_diff = team_a_data['avg_diff']
                    other_diff = team_b_data['avg_diff']
                    bet_added = data["bet1"]
                    bet_other = data["bet2"]
                    favorite_added = "gov_1"
                    favorite_other = "2"

                score = added_diff + rate - other_diff

                if score > 0:
                    favorite = favorite_added
                    result["bet"] = bet_added
                else:
                    favorite = favorite_other
                    result["bet"] = bet_other
                    score = -score

                    team_to_add,score_add = self.presentage_calculator(team_a_data, team_b_data,favorite)
                    if team_to_add ==favorite:
                        score =score+score_add
                        print (f"adding bonus {score_add} for presentage found ")
                print(f"****  Score found, score = {score} ,favorite = {favorite} game = {data["team_a"]} VS {data["team_b"]} ****")


                result["favorite"] = favorite
                result["score"] = score
                result = self.data_parser(data,result)

                return result

            case  "2 Teams Under/Over":
                print(f"Calculate Game results for under over {team_a_data} and {team_b_data}")
                avg_total = (team_a_data['avg_total_points'] + team_b_data['avg_total_points']) / 2
                diff = int(avg_total - data["rate"])
                if abs(diff) > 10:
                    result["score"] = diff + 5  # bonus for high def
                    print(
                        f"***** High Under found Under/Over, avg_total = {avg_total} ,rate = {data["rate"]} game = {data["team_a"]} VS{data["team_b"]}")

                elif diff < 10 and diff >-10 :
                    result["score"] = diff
                    print(
                        f"***** Under/Over results, ממוצע נקודות למשחק = {avg_total} |ערך נקודות מטופס = {data["rate"]}| game = {data["team_a"]} VS{data["team_b"]} *****")

                if diff>0 : # case of Over
                    result["favorite"]="gov_1"
                    result["bet"] = data["bet1"]
                else:  # case of Under
                    result["favorite"]="2"
                    result["bet"] = data["bet2"]

                result = self.data_parser(data,result)


                return result

            case "2 Teams 3 points Under/Over":
             pass

    def data_parser(self,data,result):
        game = data["game"].split(" ")[2].replace(".", "").strip()
        plan = data["game"].split(" ")[0][1:2]

        result["game"] = game
        result["plan"] = plan
        return result

    def presentage_calculator(self,team_a_data,team_b_data,favorite):
        score_add = (team_b_data['win_percentage'] - team_a_data['win_percentage']) / 10

        if team_b_data['win_percentage'] > team_a_data['win_percentage'] and favorite == "2":
            team_to_add = "2"

        elif team_b_data['win_percentage'] < team_a_data['win_percentage'] and favorite == "gov_1":
            team_to_add = "gov_1"
        return team_to_add,score_add










