import json
import os
import pandas as pd
import altair as alt
import streamlit as st

import gspread
import warnings
warnings.simplefilter('ignore')
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
@st.cache_data(show_spinner=False)
def sheet_to_df(sheet_id):
    worksheet = gc.open_by_key(sheet_id).sheet1
    data = worksheet.get_all_records()
    return pd.DataFrame(data)


# def mastersheet_preprocess(df):

#     cols = ['Date','Book ID', 'Writing', 'Apply ISBN', 'ISBN', 'Cover Page', 'Back Page Update', 'Ready to Print','Print',
#         'Amazon Link', 'AGPH Link', 'Google Link', 'Flipkart Link','Final Mail', 'Deliver', 'Google Review' ]

#     for i in cols:
#         df[i] = df[i].shift(-1)

#     df['Date'] = pd.to_datetime(df['Date'],  format= "%d/%m/%Y")
#     df['Book ID'] = pd.to_numeric(df['Book ID'], errors='coerce')
#     df['Date'] = df['Date'].ffill()
#     df['Book ID'] = df['Book ID'].ffill()
#     df = df[df['Date'].dt.year == 2024]

#     return df

def operations_preprocess(data):
    import pandas as pd

    # Replace empty strings with NaN
    data = data.replace('', pd.NA)
    
    # Drop rows where all elements are NaN
    data = data.dropna(how='all')
    #data.columns = data.columns.str.strip()

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

    if 'Date' in data.columns and not data['Date'].isna().all():
        # Filter data by the specified year
        data = data[data['Date'].dt.year >= 2024]

        # Add a column for the month name
        data['Month'] = data['Date'].dt.strftime('%B')
        data['Year'] = data['Date'].dt.year

        # Add a column for the days since enrollment
        current_date = pd.Timestamp.now()  # Current datetime
        data['Since Enrolled'] = (current_date - data['Date']).dt.days

    return data

def ijisem_preprocess(data):
    # Replace empty strings with NaN
    data = data.replace('', pd.NA)
    
    # Drop rows where all elements are NaN
    data = data.dropna(how='all')

    # Convert 'Date' columns to datetime
    date_columns = [
        'Receiving Date', 'Review Date', 'Formatting Date', 'Paper Uploading Date']
    
    for col in date_columns:
        if col in data.columns:
            # Convert to datetime64[ns] first
            data[col] = pd.to_datetime(data[col], format="%d/%m/%Y", errors='coerce')

    # Add a column for the month name
    data['Month'] = data['Receiving Date'].dt.strftime('%B')
    data['Year'] = data['Receiving Date'].dt.year

    return data

def check_number_or_string(value):
    return isinstance(value, (int, float, str))

#####################################################################################################
#####################-----------  Work done Books on Previous day & Today ----------######################
####################################################################################################



def work_done_status(df):
    from datetime import datetime, timedelta

    # Ensure date columns are datetime objects
    date_columns = ['Date','Writing Start Date','Writing End Date', 'Proofreading Start Date',
                    'Proofreading End Date', 'Formating Start Date','Formating End Date']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

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
        if pd.notna(row['Writing End Date']) and row['Writing End Date'].date() in [today, yesterday]:
            work_done.append('Writing')
        if pd.notna(row['Proofreading End Date']) and row['Proofreading End Date'].date() in [today, yesterday]:
            work_done.append('Proofreading')
        if pd.notna(row['Formating End Date']) and row['Formating End Date'].date() in [today, yesterday]:
            work_done.append('Formatting')
        return ', '.join(work_done)  # Ensure this is a string

    filtered_df['Work Done'] = filtered_df.apply(identify_work_done, axis=1)

    for col in date_columns:
        filtered_df[col] = filtered_df[col].dt.strftime('%d %B %Y')

    # Select and reorder columns
    filtered_df = filtered_df[['Book ID', 'Book Title', 'Date','Since Enrolled', 'No of Author','Work Done',
                               'Writing Complete', 'Writing By', 'Writing Start Date', 'Writing Start Time',
                               'Writing End Date', 'Writing End Time', 'Proofreading Complete', 'Proofreading By',
                               'Proofreading Start Date', 'Proofreading Start Time', 'Proofreading End Date',
                               'Proofreading End Time', 'Formating Complete', 'Formating By', 'Formating Start Date',
                               'Formating Start Time', 'Formating End Date', 'Formating End Time']].fillna('Pending')

    return filtered_df



####################################################################################################
################-----------  Writing & Proofreading complete in this Month ----------##############
####################################################################################################

def proofreading_complete(data,selected_year,selected_month):
    proofreading_complete = data[
    (data['Proofreading End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (data['Proofreading End Date'].dt.strftime('%B') == str(selected_month))
]
    proofreading_complete = proofreading_complete[proofreading_complete['Proofreading Complete'] == 'TRUE']
    proofreading_complete = proofreading_complete[['Book ID', 'Book Title','No of Author', 'Date','Since Enrolled',
                                                   'Writing By', 'Writing Start Date', 'Writing Start Time', 'Writing End Date', 'Writing End Time',
                                                   'Proofreading By', 'Proofreading Start Date', 'Proofreading Start Time', 'Proofreading End Date',
                                                   'Proofreading End Time']]
    
    count = proofreading_complete['Book ID'].nunique()

    date_columns = [col for col in proofreading_complete.columns if 'Date' in col]
    for col in date_columns:
        proofreading_complete[col] = proofreading_complete[col].dt.strftime('%d %B %Y')

    return proofreading_complete, count

def writing_complete(data,selected_year,selected_month):
    writing_complete = data[
    (data['Writing End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (data['Writing End Date'].dt.strftime('%B') == str(selected_month))
]
    writing_complete = writing_complete[writing_complete['Writing Complete'] == 'TRUE']
    writing_complete = writing_complete[['Book ID', 'Book Title','No of Author', 'Date','Since Enrolled',
                                                   'Writing By', 'Writing Start Date', 'Writing Start Time', 'Writing End Date', 'Writing End Time']]
    
    count = writing_complete['Book ID'].nunique()

    date_columns = [col for col in writing_complete.columns if 'Date' in col]
    for col in date_columns:
        writing_complete[col] = writing_complete[col].dt.strftime('%d %B %Y')
    
    return writing_complete, count


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

####################################################################################################
#####################-----------  Line Chart Monthly Books & Authors ----------######################
###################################################################################################

#More robust version with your original code integrated:
def get_monthly_book_author_counts(df,month_order):
    """Calculates and combines monthly book and author counts into a single DataFrame."""
    if df.empty:
        return pd.DataFrame(columns=['Month', 'Total Books', 'Total Authors']) # Return empty DataFrame if input is empty
    try:
        monthly_book_counts = df[df['Book ID'] != ''].groupby('Month')['Book ID'].nunique().reset_index()
        monthly_book_counts.columns = ['Month', 'Total Books']

        monthly_author_counts = df.groupby('Month')['No of Author'].sum().reset_index()
        monthly_author_counts.columns = ['Month', 'Total Authors']

        monthly_data = pd.merge(monthly_book_counts, monthly_author_counts, on='Month', how='outer')
        monthly_data['Month'] = pd.Categorical(monthly_data['Month'], categories=month_order, ordered=True)
        return monthly_data
    except KeyError as e:
        print(f"Error: Column '{e}' not found in DataFrame.")
        return pd.DataFrame(columns=['Month', 'Total Books', 'Total Authors']) # Return empty DataFrame if error
    except AttributeError as e:
        print(f"Error: Likely a problem with the 'Date' column format. Ensure it's datetime. Details: {e}")
        return pd.DataFrame(columns=['Month', 'Total Books', 'Total Authors']) # Return empty DataFrame if error
    

####################################################################################################
#####################-----------  Operation Durations ----------######################
###################################################################################################


def parse_datetime(date_obj, time_str):
    """
    Combines a datetime date (date_obj) with a time string (time_str) into a full datetime object.
    Handles missing (NA) values and unexpected formats safely.
    
    Parameters:
        date_obj (datetime): A datetime object representing the date.
        time_str (str or pd.NA): A string representing the time, e.g., "11:07".
    
    Returns:
        datetime or pd.NaT: The combined datetime object or NaT if time_str is missing or invalid.
    """
    if pd.isna(time_str) or not isinstance(time_str, str):
        return pd.NaT  # Handle missing or non-string values
    
    # Ensure the time is in the expected "HH:MM" format
    if not time_str.strip().replace(":", "").isdigit() or ":" not in time_str:
        #print(f"Skipping invalid time: {time_str}")  # Debugging statement
        return pd.NaT  # Return NaT for invalid values
    
    try:
        # Split the time string into hours and minutes
        hour, minute = map(int, time_str.split(':'))
        
        # Apply conversion rules based on office hours (9:30 AM - 6:00 PM)
        if hour in [9, 10, 11]:
            pass  # AM (unchanged)
        elif hour == 12:
            pass  # Noon (unchanged)
        elif 1 <= hour <= 6:
            hour += 12  # Convert to PM
        else:
            #print(f"Skipping out-of-range time: {time_str}")  # Debugging statement
            return pd.NaT  # Handle out-of-range values

        # Combine the date with the adjusted time
        return date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    except ValueError as e:
        #print(f"Skipping invalid time format '{time_str}': {e}")  # Debugging statement
        return pd.NaT  # Handle unexpected errors gracefully
    
def format_duration(td):
    total_seconds = td.total_seconds()
    days = int(total_seconds // (24 * 3600))
    hours = int((total_seconds % (24 * 3600)) // 3600)
    return f"{days} days {hours} hours"

# Function to remove outliers using IQR
def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)  # First quartile (25%)
    Q3 = df[column].quantile(0.75)  # Third quartile (75%)
    IQR = Q3 - Q1  # Interquartile range
    
    # Define the lower and upper bounds
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter the data
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]