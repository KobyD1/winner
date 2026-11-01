import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from winner_final.globals import EXCEL_PREFIX


import unicodedata
import pandas as pd
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display
import arabic_reshaper
from reportlab.platypus import SimpleDocTemplate, Paragraph



class FilesUtils:
    def __init__(self):
        pass



    def get_teams_names_from_excel(self,excel_file: str, team_a: str, team_b: str):


        teams_data_excel = {}
        df = pd.read_excel(EXCEL_PREFIX + excel_file)
        teams_telesport = df["Telesport"]
        team_a_data = df[teams_telesport.str.contains(team_a, na=False)]
        result_a = team_a_data.iloc[0].to_dict()
        team_b_data = df[teams_telesport.str.contains(team_b, na=False)]

        result_b = team_b_data.iloc[0].to_dict()
        teams_data_excel["team_a"] = result_a["Team"].strip()
        teams_data_excel["team_b"] = result_b["Team"].strip()
        teams_data_excel["League"] = result_a["League"].strip()
        return teams_data_excel




    def get_team_data_from_excel(self,excel_path: str, team_a: str, team_b: str):

        teams_data_excel = {}
        try:

            df = pd.read_excel(excel_path)
            teams_telesport = df["Telesport"]
            team_a_data = df[teams_telesport == team_a]
            result_a = team_a_data.iloc[0].to_dict()

            team_b_data = df[teams_telesport == team_b]
            result_b = team_b_data.iloc[0].to_dict()
            teams_data_excel["Team_A"]= result_a["Team"]
            teams_data_excel["ID_A"]= str(result_a["ESPN_Team_ID"]).split(".")[0]
            teams_data_excel["Team_B"] = result_b["Team"]
            teams_data_excel["ID_B"] = str(result_b["ESPN_Team_ID"]).split(".")[0]

        except:
            print (f"team data not found at excel {excel_path} ,teams : {team_a}, {team_b}")


        return teams_data_excel


    def get_teams(self,team_a,team_b, excel_file):
        path = EXCEL_PREFIX + excel_file
        teams_telesport = self.get_team_data_from_excel(path, team_a, team_b)
        print ("break")

    def get_team_ids(self,table_data, excel_file="wnba.xlsx"):
        path= EXCEL_PREFIX+excel_file
        if table_data:
            team_a = table_data["team_a"]
            team_b =  table_data["team_b"]
            teams_telesport = self.get_team_data_from_excel(path,team_a,team_b)
            table_data["Team_A"] =teams_telesport["Team_A"]
            table_data["ID_A"] =teams_telesport["ID_A"]
            table_data["Team_B"] = teams_telesport["Team_B"]
            table_data["ID_B"] = teams_telesport["ID_B"]

            return table_data
        else:
            print (f"Data did not found at Table {excel_file}")
            return None

    def visual_length(self, text):
        count = 0
        for ch in text:
            if unicodedata.bidirectional(ch) in ("R", "AL"):
                count += 1
            else:
                count += 1
        return count

    def print_results(self, results_sorted ,headers,title="Results"):
        print(f"\033[1m{title}\033[0m")
        if results_sorted:

            rows = [
                [
                    str(item["favorite"]),
                    str(item["game"]),
                    str(item["plan"]),
                    f"{item['score']:.2f}",
                    str(item["bet"]),
                    str(item["avg_total"]) ,
                    str(item.get("home_count",0)),
                    str(item.get("away_count", 0))
                ]
                for item in results_sorted
            ]

            # calc. width of Col.
            col_widths = []
            for col in range(len(headers)):
                max_len = max(
                    self.visual_length(headers[col]),
                    max(self.visual_length(row[col]) for row in rows)
                )
                col_widths.append(max_len)

            def build_separator(left, fill, middle, right):
                parts = [left]
                for i, w in enumerate(col_widths):
                    parts.append(fill * (w + 2))
                    parts.append(middle if i < len(col_widths) - 1 else right)
                return "".join(parts)

            def build_row(values):
                parts = ["│"]
                for i, v in enumerate(values):
                    pad = col_widths[i] - self.visual_length(v)
                    parts.append(" " + v + " " * (pad + 1))
                    parts.append("│")
                return "".join(parts)

            print(build_separator("┌", "─", "┬", "┐"))
            print(build_row(headers))
            print(build_separator("├", "─", "┼", "┤"))

            for row in rows:
                print(build_row(row))

            print(build_separator("└", "─", "┴", "┘"))

    def print_results_basketball(self, results_sorted):
        if results_sorted:
            headers = ["Favorite", "Game", "Plan", "Score", "Bet"]

            rows = [
                [
                    str(item["favorite"]),
                    str(item["game"]),
                    str(item["plan"]),
                    f"{item['score']:.2f}",
                    str(item["bet"]),
                ]
                for item in results_sorted
            ]

            # calc. width of Col.
            col_widths = []
            for col in range(len(headers)):
                max_len = max(
                    self.visual_length(headers[col]),
                    max(self.visual_length(row[col]) for row in rows)
                )
                col_widths.append(max_len)

            def build_separator(left, fill, middle, right):
                parts = [left]
                for i, w in enumerate(col_widths):
                    parts.append(fill * (w + 2))
                    parts.append(middle if i < len(col_widths) - 1 else right)
                return "".join(parts)

            def build_row(values):
                parts = ["│"]
                for i, v in enumerate(values):
                    pad = col_widths[i] - self.visual_length(v)
                    parts.append(" " + v + " " * (pad + 1))
                    parts.append("│")
                return "".join(parts)

            print(build_separator("┌", "─", "┬", "┐"))
            print(build_row(headers))
            print(build_separator("├", "─", "┼", "┤"))

            for row in rows:
                print(build_row(row))

            print(build_separator("└", "─", "┴", "┘"))


    def save_output(self, items, path, prefix, file_type="txt"):


        timestamp = datetime.now().strftime("%m_%d_%H_%M")
        filename = f"{prefix}_{timestamp}.{file_type}"
        full_path = os.path.join(path, "results", filename)

        print(f"Saving file to : {full_path}")

        os.makedirs(os.path.join(path, "results"), exist_ok=True)

        if file_type == "txt":
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("-" * 40 + "\n")
                for item in items:
                    item.pop("description", None)
                    f.write(str(item) + "\n")


        return full_path







    def get_file_name(self,path,prefix):
        timestamp = datetime.now().strftime("%m_%d_%H_%M")
        filename = f"{prefix}_{timestamp}.txt"
        full_path = os.path.join(path, "results", filename)

        return full_path

        print(f"Saving file to : {full_path}")





    def convert_txt_folder_to_pdf(self,folder_path):
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontName = "DejaVu"
        style.fontSize = 12
        style.leading = 16
        style.rightIndent = 0
        style.leftIndent = 0

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".txt"):
                txt_path = os.path.join(folder_path, filename)
                pdf_path = os.path.join(folder_path, filename[:-4] + ".pdf")

                doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                        rightMargin=40, leftMargin=40,
                                        topMargin=40, bottomMargin=40)

                story = []

                with open(txt_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.replace("\xa0", "")

                        reshaped = arabic_reshaper.reshape(line)
                        bidi_text = get_display(reshaped)
                        bidi_text
                        story.append(Paragraph(bidi_text, style))

                doc.build(story)
                print(f"Created  PDF: {pdf_path}")

    def wrote_to_text_file(self,list,path , prefix):
        timestamp = datetime.now().strftime("%m_%d_%H_%M")
        file = path+"/results/"+prefix+"_"+timestamp+".txt"
        print (f"Writing to file : {file}")
        with open(file, "w", encoding="utf-8") as f:
            f.write("-" * 40 + "\n")

            for item in list:
                f.write(str(item) + "\n")

