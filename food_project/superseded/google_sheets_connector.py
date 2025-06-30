# import gspread
# import streamlit as st
# from oauth2client.service_account import ServiceAccountCredentials

# # This list defines what permissions we need to access Google Sheets and Google Drive
# scope = [
#     "https://spreadsheets.google.com/feeds",
#     "https://www.googleapis.com/auth/drive"
# ]

# # This function is only run once per app session thanks to @st.cache_resource
# # That means Streamlit won't reauthorize Google Sheets every time someone interacts with the app
# @st.cache_resource
# def get_sheet():
#     # We build a dictionary of credentials using the secret values stored in Streamlit Cloud
#     creds_dict = {
#         "type": st.secrets["google"]["type"],
#         "project_id": st.secrets["google"]["project_id"],
#         "private_key_id": st.secrets["google"]["private_key_id"],
#         "private_key": st.secrets["google"]["private_key"],
#         "client_email": st.secrets["google"]["client_email"],
#         "client_id": st.secrets["google"]["client_id"],
#         "auth_uri": st.secrets["google"]["auth_uri"],
#         "token_uri": st.secrets["google"]["token_uri"],
#         "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
#         "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
#         "universe_domain": st.secrets["google"]["universe_domain"]
#     }

#     # We use the credentials dictionary to authorize with Google Sheets
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)

#     # Open the spreadsheet named "food_info_app" and return the first sheet
#     sheet = client.open("food_info_app").sheet1
#     return sheet

# # This function takes a food name and returns a dictionary of info about it (like calories, water use, etc.)
# def get_food_data(food_name):
#     # Load the sheet (uses the cached version if available)
#     sheet = get_sheet()

#     # Get the list of all food names from column A
#     full_list = sheet.col_values(1)

#     # If the food is not in the list, return None
#     if food_name not in full_list:
#         return None

#     # If found, get the row index (Google Sheets rows start at 1)
#     row_index = full_list.index(food_name) + 1

#     # Get the column headers from the first row (excluding the first column which is just the food name)
#     headers = sheet.row_values(1)[1:]

#     # Get the values from the matching row (again skipping the food name)
#     row_data = sheet.row_values(row_index)[1:]

#     # Combine headers and row data into a dictionary and return it
#     return dict(zip(headers, row_data))