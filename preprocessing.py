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


######################################################################################
######################------------- 45 days data-------------#########################
######################################################################################

def process_book_timings(data, by_col='Date'):
    """
    Process book timings data to combine date and time columns, handle missing values,
    calculate durations, and filter data for a specific year.

    Args:
        data (pd.DataFrame): Input DataFrame containing timing data for books.
        by_col (str): Column name to filter the data by year. Default is 'Date'.

    Returns:
        pd.DataFrame: Processed DataFrame with additional datetime and duration columns.
    """
    # Replace empty strings with NA and drop rows where all values are NA
    data = data.replace('', pd.NA)
    data = data.dropna(how='all')

    # Convert 'Date' column to datetime
    data[by_col] = pd.to_datetime(data[by_col], format="%d/%m/%Y", errors='coerce')

    # Ensure date and time columns are strings and fill missing values with "Pending"
    date_time_columns = [
        'Writing Start Date', 'Writing Start Time',
        'Writing End Date', 'Writing End Time',
        'Proofreading Start Date', 'Proofreading Start Time',
        'Proofreading End Date', 'Proofreading End Time',
        'Formating Start Date', 'Formating Start Time',
        'Formating End Date', 'Formating End Time'
    ]
    for col in date_time_columns:
        data[col] = data[col].fillna("Pending").astype(str)

    # Define the correct datetime format
    datetime_format = '%d/%m/%Y %I:%M'

    # Helper function to parse datetime or return "Pending"
    def parse_datetime(date, time):
        if date == "Pending" or time == "Pending":
            return "Pending"
        try:
            return pd.to_datetime(f"{date} {time}", format=datetime_format)
        except ValueError:
            return "Pending"

    # Combine date and time for Writing
    data['Writing Start Datetime'] = data.apply(
        lambda row: parse_datetime(row['Writing Start Date'], row['Writing Start Time']), axis=1
    )
    # Combine date and time for Writing
    data['Writing End Datetime'] = data.apply(
        lambda row: parse_datetime(row['Writing End Date'], row['Writing End Time']), axis=1
    )

    # Combine date and time for Proofreading
    data['Proofreading Start Datetime'] = data.apply(
        lambda row: parse_datetime(row['Proofreading Start Date'], row['Proofreading Start Time']), axis=1
    )
    data['Proofreading End Datetime'] = data.apply(
        lambda row: parse_datetime(row['Proofreading End Date'], row['Proofreading End Time']), axis=1
    )

    # Combine date and time for Formatting
    data['Formatting Start Datetime'] = data.apply(
        lambda row: parse_datetime(row['Formating Start Date'], row['Formating Start Time']), axis=1
    )
    data['Formatting End Datetime'] = data.apply(
        lambda row: parse_datetime(row['Formating End Date'], row['Formating End Time']), axis=1
    )

    # Filter data by the specified year
    data = data[data[by_col].dt.year == 2024]

    # Add a column for the month name
    data['Month'] = data[by_col].dt.strftime('%B')
    data = data.fillna('Pending')

    return data

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