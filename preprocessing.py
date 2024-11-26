import json
import os
import pandas as pd
import datetime
import altair as alt

import gspread
import warnings
warnings.simplefilter('ignore')
import numpy as np
from datetime import datetime
from google.oauth2.service_account import Credentials

creds_path = os.getenv('CREDS_PATH', "token.json")
sheets_json_path = os.getenv('SHEETS_JSON_PATH', "sheets.json")

def read_sheets_from_json():
    if os.path.exists(sheets_json_path):
        with open(sheets_json_path, 'r') as file:
            return json.load(file)
    return {}

scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(creds_path, scopes = scope)
gc = gspread.authorize(credentials)

######################################################################################
#####################------------Data Fetch Helper functions--------------############
######################################################################################

# Fetch data from a Google Sheet
def sheet_to_df(sheet_id):
    worksheet = gc.open_by_key(sheet_id).sheet1
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Fetch data from a Google Sheet
def fetch_track_sheet_data(sheet_id):
    worksheet = gc.open_by_key(sheet_id).sheet1
    data = worksheet.get_all_values()
    
    # Ensure data is not empty
    if not data:
        return pd.DataFrame()  # Return an empty DataFrame if no data is found
    
    # Extract headers and data rows
    headers = data[0]
    data_rows = data[1:]

    # Create DataFrame with updated headers
    data = pd.DataFrame(data_rows, columns=headers)
    
    # Convert 'Date' columns to datetime with specified formats
    # First "Date" column with format "%d/%m/%Y"
    data["Date"] = pd.to_datetime(data["Date"], format="%d/%m/%Y", errors='coerce')
    data["Writing Date"] = pd.to_datetime(data["Writing Date"], format="%d/%m/%Y", errors='coerce')
    data["Proofreading Date"] = pd.to_datetime(data["Proofreading Date"], format="%d/%m/%Y", errors='coerce')
    data["Formatting Date"] = pd.to_datetime(data["Formatting Date"], format="%d/%m/%Y", errors='coerce')
    
    return data

# Fetch data from a Google Sheet
def fetch_writing_sheet_data(sheet_id):
    worksheet = gc.open_by_key(sheet_id).sheet1
    data = worksheet.get_all_values()
    
    # Ensure data is not empty
    if not data:
        return pd.DataFrame()  # Return an empty DataFrame if no data is found
    
    # Extract headers and data rows
    headers = data[0]
    data_rows = data[1:]

    # Create DataFrame with updated headers
    df = pd.DataFrame(data_rows, columns=headers)
    df['Date'] = pd.to_datetime(df['Date'],format="%d/%m/%Y", errors='coerce')
    
    return df

def track_writing_sheet_preproces(df, by_col = 'Date'):
    df['Book Title'] = df['Book Title'].shift(1)
    df = df.iloc[1:]
    df = df.replace('', pd.NA) 
    df = df.dropna(how = 'all')
    df = df[df[by_col].dt.year == 2024]
    df['Month'] = df[by_col].dt.strftime('%B')

    return df

def operations_preprocess(data):
    import pandas as pd

    # Replace empty strings with NaN
    data = data.replace('', pd.NA)
    
    # Drop rows where all elements are NaN
    data = data.dropna(how='all')

    # Convert 'Date' columns to datetime
    date_columns = [
        'Date', 
        'Writing Start Date', 'Writing End Date', 
        'Proofreading Start Date', 'Proofreading End Date', 
        'Formating Start Date', 'Formating End Date'
    ]
    for col in date_columns:
        if col in data.columns:
            # Convert to datetime64[ns] first
            data[col] = pd.to_datetime(data[col], format="%d/%m/%Y", errors='coerce')

    if 'Date' in data.columns:
        # Filter data by the specified year
        data = data[data['Date'].dt.year == 2024]

        # Add a column for the month name
        data['Month'] = data['Date'].dt.strftime('%B')

        # Add a column for the days since enrollment
        current_date = pd.Timestamp.now()  # Current datetime
        data['Since Enrolled'] = (current_date - data['Date']).dt.days

    return data

#####################################################################################################
#####################-----------  Current day status dataframe ----------######################
####################################################################################################



def work_done_status(df):
    from datetime import datetime, timedelta

    # Get today's and yesterday's dates
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Filter rows where any of the dates match today or yesterday
    filtered_df = df[
        (df['Writing End Date'].dt.date == today) | (df['Writing End Date'].dt.date == yesterday) |
        (df['Proofreading End Date'].dt.date == today) | (df['Proofreading End Date'].dt.date == yesterday) |
        (df['Formating End Date'].dt.date == today) | (df['Formating End Date'].dt.date == yesterday)
    ]

    # Add a column to indicate which work was done
    def identify_work_done(row):
        work_done = []
        if row['Writing End Date'] and row['Writing End Date'].date() in [today, yesterday]:
            work_done.append('Writing')
        if row['Proofreading End Date'] and row['Proofreading End Date'].date() in [today, yesterday]:
            work_done.append('Proofreading')
        if row['Formating End Date'] and row['Formating End Date'].date() in [today, yesterday]:
            work_done.append('Formatting')
        return ', '.join(work_done)

    filtered_df['Work Done'] = filtered_df.apply(identify_work_done, axis=1)
    filtered_df = filtered_df[['Book ID', 'Book Title', 'Date','Month', 'Since Enrolled', 'Work Done','Writing Complete', 'Writing By',
       'Writing Start Date', 'Writing Start Time', 'Writing End Date',
       'Writing End Time', 'Proofreading Complete', 'Proofreading By',
       'Proofreading Start Date', 'Proofreading Start Time',
       'Proofreading End Date', 'Proofreading End Time', 'Formating Complete',
       'Formating By', 'Formating Start Date', 'Formating Start Time',
       'Formating End Date', 'Formating End Time']].fillna('Pending')
    
    return filtered_df


#####################################################################################################
#####################-----------  Bar chart Number of Books in Month ----------######################
####################################################################################################


def create_grouped_bar_chart(data, title, color_scheme):
    # Main bar chart with grouped bars
    bars = alt.Chart(data).mark_bar().encode(
        x=alt.X('Category:N', title=None, axis=alt.Axis(labelAngle=-65, labelOverlap="greedy"),scale=alt.Scale(padding=0.2)),
        y=alt.Y('Count:Q', title='Count'),
        color=alt.Color('Status:N', scale=alt.Scale(range=color_scheme), legend=alt.Legend(title="Status")),
        xOffset='Status:N'  # Offset by 'Status' for grouping effect
    ).properties(
        width=300,  
        height=400,
        title=title
    )
    
    # Text labels on each bar
    text = bars.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text='Count:Q'
    )
    
    return bars + text