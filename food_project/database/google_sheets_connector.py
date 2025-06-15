import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google"], scope)
    client = gspread.authorize(creds)
    return client.open("food_info_app").sheet1

def get_food_data(food_name):
    sheet = get_sheet()
    food_list = sheet.col_values(1)  # Column A = food names
    if food_name in food_list:
        row_index = food_list.index(food_name) + 1
        row_data = sheet.row_values(row_index)
        return {
            "calories": row_data[1],
            "price": row_data[2],
            "emissions": row_data[3]
        }
    return None
