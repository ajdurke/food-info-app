import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope for accessing Google Sheets and Drive
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Cache the sheet resource so it only authorizes once per session
@st.cache_resource
def get_sheet():
    # Build credentials from Streamlit secrets under [google]
    creds_dict = {
        "type": st.secrets["google"]["type"],
        "project_id": st.secrets["google"]["project_id"],
        "private_key_id": st.secrets["google"]["private_key_id"],
        "private_key": st.secrets["google"]["private_key"],
        "client_email": st.secrets["google"]["client_email"],
        "client_id": st.secrets["google"]["client_id"],
        "auth_uri": st.secrets["google"]["auth_uri"],
        "token_uri": st.secrets["google"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
        "universe_domain": st.secrets["google"]["universe_domain"]
    }

    # Authorize and open the sheet
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("food_info_app").sheet1
    return sheet

# Function to retrieve food data by food name
def get_food_data(food_name):
    sheet = get_sheet()
    full_list = sheet.col_values(1)  # Column A (food names)

    if food_name not in full_list:
        return None

    row_index = full_list.index(food_name) + 1
    headers = sheet.row_values(1)[1:]         # Skip 'food_name' header
    row_data = sheet.row_values(row_index)[1:]  # Skip 'food_name' column in data

    return dict(zip(headers, row_data))

