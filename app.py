import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import pandas as pd
from datetime import datetime
import time
import requests
import numpy as np
from preprocessing import *
import datetime
import seaborn as sns
from dotenv import load_dotenv
import base64
import json
import hashlib
import hmac
import time

# Set page configuration
st.set_page_config(
    menu_items={
        'About': "AGPH",
        'Get Help': None,
        'Report a bug': None,   
    },
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="collapsed",
    page_icon="chart_with_upwards_trend",  
    page_title="AGPH Dashboard",
)

# Inject CSS to remove the menu (optional)
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Define API URL and secure API key
MASTERSHEET_API_URL = "https://agkitdatabase.agvolumes.com/redirect_to_adsearch"

load_dotenv()
# Use the same secret key as MasterSheet3
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key') 

def validate_token():
    # Extract the token from query parameters
    params = st.query_params  # st.query_params for earlier versions
    if 'token' not in params:
        st.error("Access Denied: Login Required")
        st.stop()

    token = params['token']
    try:
        # Split the JWT into header, payload, and signature
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        # Decode header and payload
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8'))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8'))

        # Verify signature
        signature = base64.urlsafe_b64decode(parts[2] + '==')
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{parts[0]}.{parts[1]}".encode(),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        # Check expiration (if present)
        if 'exp' in payload and payload['exp'] < time.time():
            raise ValueError("Token has expired")

    except ValueError as e:
        st.error(f"Access Denied: {e}")
        st.stop()

# Validate token before running the app
validate_token()

# Initialize session state for new visitors
if "visited" not in st.session_state:
    st.session_state.visited = False

# Check if the session state variable 'first_visit' is set, indicating the first visit
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True 

# Check if the user is new
if not st.session_state.visited:
    st.toast("New Data is being fetched..", icon="ℹ️")  # Notify user
    st.cache_data.clear()  # Clear cache for new visitors
    st.session_state.visited = True  # Mark as visited

# Prepare user details for token generation
user_details = {
    "user": "Admin",  
    "role": "Admin"
}

headers = {
    "Authorization": SECRET_KEY,
    "Content-Type": "application/json"
}

# Generate URL
adsearch_url = None
try:
    # Send POST request to Mastersheet app
    response = requests.post(MASTERSHEET_API_URL, json=user_details, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        adsearch_url = response_data.get("url")
    else:
        st.error(f"Failed to generate AdSearch URL. Status Code: {response.status_code}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")

sheets = read_sheets_from_json()

# # Create a placeholder for the status
status_placeholder = st.empty()

with status_placeholder.container():
    with st.status("Loading Data", expanded=True) as status:
        st.write("Calling Google Sheet API...")
        operations_sheet_data = sheet_to_df(sheets['Operations'])
        st.write("Processing Data..")
        operations_sheet_data_preprocess = operations_preprocess(operations_sheet_data)
        status.update(
            label="Data Loaded!", state="complete", expanded=False)

status_placeholder.empty()

######################################################################################
###########################----------- Data Loader & Spinner ----------#############################
######################################################################################


unique_year = operations_sheet_data_preprocess['Year'].unique()[~np.isnan(operations_sheet_data_preprocess['Year'].unique())]
# unique_months_sorted = sorted(unique_months, key=lambda x: datetime.strptime(x, "%B")) # Get unique month names

# Map month numbers to month names and set the order
month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]

from datetime import datetime, timedelta
today = datetime.today().date()
current_year = datetime.now().year
current_month = datetime.now().strftime("%B")
num_book_today = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Date'] == pd.Timestamp(today)]

# Show the toast and balloons only on the first visit
if st.session_state.first_visit:
    if len(num_book_today) > 0:
        st.toast(f"{len(num_book_today)} New Book{'s' if len(num_book_today) > 1 else ''} Enrolled Today!", icon="🎉")
        st.balloons()  # Trigger the balloons animation
    else:
        st.toast("No New Books Enrolled Today!", icon="😔")
        time.sleep(2)
    
    st.session_state.first_visit = False

col1, col2, col3 = st.columns([2,14, 2])  # Adjust column widths as needed

with col1:
    selected_year = st.pills("2024", unique_year, selection_mode="single", 
                            default =unique_year[-1],label_visibility ='collapsed')
    
operations_sheet_data_preprocess_year = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Year']== selected_year]
unique_months_selected_year = operations_sheet_data_preprocess_year['Month'].unique() 


with col2:
        selected_month = st.pills("2024", unique_months_selected_year, selection_mode="single", 
                              default =unique_months_selected_year[-1],label_visibility ='collapsed')

        
with col3:
        if adsearch_url:
            adsearch_clicked = st.markdown(
            f"""
            <a href="{adsearch_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    background-color: #ffffff;
                    color: black;
                    border:  0.2px solid;
                    border-color: #b3abab;
                    padding: 6px 10px;
                    text-align: center;
                    font-size: 13.5px;
                    cursor: pointer;
                    border-radius: 55px;">
                    Search Books 🔍
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    
######################################################################################
#####################----------- Metrics of Selected Month ----------######################
######################################################################################

# Filter DataFrame based on selected month
operations_sheet_data_preprocess_month = operations_sheet_data_preprocess_year[operations_sheet_data_preprocess_year['Month']== selected_month]

# Calculate metrics based on both TRUE and FALSE values in the filtered DataFrame

total_authors = operations_sheet_data_preprocess_month['No of Author'].sum()
total_books= len(np.array(operations_sheet_data_preprocess_month['Book ID'].unique())[np.array(operations_sheet_data_preprocess_month['Book ID'].unique()) !=''])
today_num_books = len(num_book_today)
today_num_authors = num_book_today['No of Author'].sum()

# Check if the user has selected the current year and month
if selected_year == current_year and selected_month == current_month:
    delta_books = f"-{abs(today_num_books)} added today" if today_num_books < 1 else str(today_num_books) + " added today"
    delta_authors = f"-{abs(today_num_authors)} added today" if today_num_authors < 1 else str(today_num_authors) + " added today"
else:
    delta_books = None
    delta_authors = None

books_written_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Writing Complete'] == 'TRUE']['Book ID'].nunique()
books_proofread_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Proofreading Complete'] == 'TRUE']['Book ID'].nunique()
books_formatted_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Formating Complete'] == 'TRUE']['Book ID'].nunique()


books_complete = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Book Complete'] == 'TRUE']['Book ID'].nunique()
books_apply_isbn_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Apply ISBN'] == 'TRUE']['Book ID'].nunique()
books_printed_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Print'] == 'TRUE']['Book ID'].nunique()
books_delivered_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Deliver'] == 'TRUE']['Book ID'].nunique()

import time

st.subheader(f"Metrics of {selected_month}")

with st.container():
    # Display metrics with TRUE counts in value and FALSE counts in delta
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    col1.metric("Total Books", total_books,delta=delta_books)
    col2.metric("Total Authors", total_authors, delta=delta_authors)
    col3.metric("Written", books_written_true, delta=f"-{total_books - books_written_true} Remaining")
    col4.metric("Proofread", books_proofread_true, delta=f"-{books_written_true - books_proofread_true} Remaining")
    col5.metric("Formatting", books_formatted_true, delta=f"-{books_proofread_true - books_formatted_true} Remaining")
    col6.metric("Book Complete", books_complete, delta=f"-{total_books - books_complete} not complete")
    col7.metric("ISBN Received", books_apply_isbn_true, delta=f"-{total_books - books_apply_isbn_true} not received")
    col8.metric("Printed", books_printed_true, delta=f"-{total_books - books_printed_true} not printed")
    col9.metric("Delivered", books_delivered_true, delta=f"-{total_books - books_delivered_true} not delivered")


######################################################################################
####################----------- Current Working status dataframe -------------########
######################################################################################

# Define conditions in a dictionary, including columns to select for each case
conditions = {
    'Formating': {
        'by': ['Akash', 'Anush', 'Surendra', 'Rahul'],
        'status': 'Formating Complete',
        'columns': ['Book ID', 'Book Title', 'Date','Month','Since Enrolled','No of Author', 'Formating By', 'Formating Start Date', 'Formating Start Time',
      'Proofreading By','Proofreading Start Date', 'Proofreading Start Time', 'Proofreading End Date', 'Proofreading End Time',
      'Writing By','Writing Start Date', 'Writing Start Time', 'Writing End Date', 'Writing End Time']
    },
    'Proofreading': {
        'by': ['Umer', 'Publish Only', 'Barnali', 'Sheetal', 'Rakesh', 'Aman', 'Minakshi', 'Vaibhavi'],
        'status': 'Proofreading Complete',
        'columns': ['Book ID', 'Book Title','Date', 'Month','Since Enrolled','No of Author', 'Proofreading By','Proofreading Start Date', 
                    'Proofreading Start Time', 'Writing By','Writing Start Date', 'Writing Start Time', 'Writing End Date',
       'Writing End Time']
    },
    'Writing': {
        'by': ['Vaibhavi', 'Vaibhav', 'Rakesh', 'Sheetal', 'Urvashi', 'Shravani', 
               'Publish Only', 'Minakshi', 'Preeti', 'Muskan', 'Bhavana', 'Aman', 
               'Sachin', 'muskan'],
        'status': 'Writing Complete',
        'columns': ['Book ID', 'Book Title','Date', 'Month', 'Since Enrolled','No of Author','Writing By','Writing Start Date', 'Writing Start Time']
    }
}


# Extract information based on conditions, including specified columns
results = {}
for key, cond in conditions.items():
    # Filter the data and select columns, creating a copy to avoid modifying the original DataFrame
    current_data = operations_sheet_data_preprocess[(operations_sheet_data_preprocess[f'{key} By'].isin(cond['by'])) & (operations_sheet_data_preprocess[cond['status']] == 'FALSE')][cond['columns']].copy()
    
    # Format 'Date' columns in the copy to remove the time part
    date_columns = [col for col in current_data.columns if 'Date' in col]
    for date_col in date_columns:
        current_data[date_col] = pd.to_datetime(current_data[date_col]).dt.strftime('%Y-%m-%d')
    
    # Save the cleaned DataFrame in results
    results[key] = current_data

# CSS for the "Status" badge style
st.markdown("""
    <style>
    .status-badge {
        background-color: #e6e6e6;
        color: #4CAF50;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.9em;
        font-weight: bold;
        display: inline-block;
        margin-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# CSS for the "Status" badge style
st.markdown("""
    <style>
    .status-badge-red {
        background-color: #e6e6e6;
        color:rgb(252, 84, 84);
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.9em;
        font-weight: bold;
        display: inline-block;
        margin-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# Define the icon and message for each status
status_messages = [
    {"emoji": "✍️", "label": "Writing", "count": len(results['Writing']), "data": results['Writing']},
    {"emoji": "📖", "label": "Proofreading", "count": len(results['Proofreading']), "data": results['Proofreading']},
    {"emoji": "🖋️", "label": "Formatting", "count": len(results['Formating']), "data": results['Formating']}
]

# Display each status section with count, emoji, and data
for status in status_messages:
    st.markdown(
        f"<h5>{status['emoji']} {status['count']} Books in {status['label']} Today "
        f"<span class='status-badge'>Status: Running</span></h5>", 
        unsafe_allow_html=True
    )
    st.dataframe(status['data'], use_container_width=True, hide_index=True)


######################################################################################
###############----------- Current day status dataframe -------------################
######################################################################################

work_done_status = work_done_status(operations_sheet_data_preprocess)

# Display the last 45 days data section with count, emoji, and title
st.markdown(
    f"<h5>✅ Work done on {work_done_status['Book ID'].nunique()} Books on Previous day & Today"
    f"<span class='status-badge'>Status: Done!</span></h5>", 
    unsafe_allow_html=True)

st.dataframe(work_done_status, use_container_width=False, hide_index=True, column_config = {
        "Writing Complete": st.column_config.CheckboxColumn(
            "Writing Complete",
            default=False,
        ),
                "Proofreading Complete": st.column_config.CheckboxColumn(
            "Proofreading Complete",
            default=False,
        ),
                        "Formating Complete": st.column_config.CheckboxColumn(
            "Formating Complete",
            default=False,
        )
    })

######################################################################################
###############----------- Work Remaining status dataframe -------------################
######################################################################################


def writing_remaining(data):

    data['Writing By'] = data['Writing By'].fillna('Pending')
    data = data[data['Writing Complete'].isin(['FALSE', pd.NA])][['Book ID', 'Book Title', 'Date','Month','Since Enrolled','No of Author','Writing By']]
    writing_remaining = data['Book ID'].nunique() - len(results['Writing'])

    return data,writing_remaining

def proofread_remaining(data):

    data['Proofreading By'] = data['Proofreading By'].fillna('Pending')
    data = data[(data['Writing Complete'] == 'TRUE') & (data['Proofreading Complete'] == 'FALSE')][['Book ID', 'Book Title', 'Date','Month','Since Enrolled','No of Author','Writing By',
                                                                                                    'Writing Start Date', 'Writing Start Time', 'Writing End Date',
                                                                                                    'Writing End Time','Proofreading By']]
    proof_remaining = data['Book ID'].nunique() - len(results['Proofreading'])

    return data,proof_remaining


writing_remaining_data,writing_remaining_count = writing_remaining(operations_sheet_data_preprocess)
proofread_remaining_data,proofread_remaining_count = proofread_remaining(operations_sheet_data_preprocess)


# Define two columns to display dataframes side by side
col1, col2 = st.columns(2)

# Display writing remaining data in the first column
with col1:
    st.markdown(
        f"<h5>✍️ {writing_remaining_count} Books Writing Remaining "
        f"<span class='status-badge-red'>Status: Remaining</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(writing_remaining_data, use_container_width=False, hide_index=True)

# Display proofreading remaining data in the second column
with col2:
    st.markdown(
        f"<h5>📖 {proofread_remaining_count} Books Proofreading Remaining "
        f"<span class='status-badge-red'>Status: Remaining</span></h5>", 
        unsafe_allow_html=True
    )
    st.dataframe(proofread_remaining_data, use_container_width=False, hide_index=True)


####################################################################################################
################-----------  Writing complete in this Month ----------##############
####################################################################################################


writing_complete_data_by_month, writing_complete_data_by_month_count = writing_complete(operations_sheet_data_preprocess,selected_year,
                                                                                        selected_month)
# Monthly data for a specific month
operations_sheet_data_preprocess_writng_month = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%B') == str(selected_month))
]
employee_monthly = operations_sheet_data_preprocess_writng_month.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)


# Altair chart for monthly data with layering of bars and text
monthly_bars = alt.Chart(employee_monthly).mark_bar().encode(
    x=alt.X('Book ID:Q', title='Number of Books'),
    y=alt.Y('Writing By:N', title='Employee', sort='-x'),
    color=alt.Color('Book ID:Q', scale=alt.Scale(scheme='blues'), legend=None),
)

# Add text labels to the monthly bars
monthly_text = monthly_bars.mark_text(
    align='left',
    dx=5 
).encode(
    text='Book ID:Q'
)

# Layer bar and text for monthly chart
monthly_chart = (monthly_bars + monthly_text).properties(
    #title=f'Books Written by Content Team in {selected_month} {selected_year}',
    width=300,
    height=390
)

# Define two columns to display dataframes side by side
col1, col2 = st.columns([1.4,1])

# Display writing remaining data in the first column
with col1:
    st.markdown(
        f"<h5>✍️ {writing_complete_data_by_month_count} Books Written in {selected_month}"
        f"<span class='status-badge'>Status: Done!</span></h5>", 
        unsafe_allow_html=True
    )
    st.dataframe(writing_complete_data_by_month, use_container_width=False, hide_index=True)

with col2:
    st.markdown(
        f"<h5>   ✍️ Book count by Team"
        f"<span class='status-badge'>Status: Done!</span></h5>", 
        unsafe_allow_html=True
    )
    st.altair_chart(monthly_chart, use_container_width=True)



####################################################################################################
################-----------  Proofreading complete in this Month ----------##############
####################################################################################################

proofreading_complete_data_by_month, proofreading_complete_data_by_month_count = proofreading_complete(operations_sheet_data_preprocess,selected_year, 
                                                                                                       selected_month)
operations_sheet_data_preprocess_proof_month = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%B') == str(selected_month))
]
proofreading_num = operations_sheet_data_preprocess_proof_month.groupby('Proofreading By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
proofreading_num.columns = ['Proofreader', 'Book Count']
cleaned_proofreading_num = proofreading_num[['Proofreader', 'Book Count']]

# Create the horizontal bar chart for Proofreading
proofreading_bar = alt.Chart(proofreading_num).mark_bar().encode(
    y=alt.Y('Proofreader', sort='-x', title='Proofreader'),  # Change x to y for horizontal bars
    x=alt.X('Book Count', title='Book Count'),  # Change y to x for horizontal bars
    color=alt.Color('Proofreader', scale=alt.Scale(scheme='blueorange'), legend=None),
    tooltip=['Proofreader', 'Book Count']
).properties(
    #title=f"Books Proofread in {selected_month} {selected_year}"
)

# Add labels on the right side of the bars for Proofreading
proofreading_text = proofreading_bar.mark_text(
    dx=10,  # Adjusts the position of the text to the right of the bar
    color='black'
).encode(
    text='Book Count:Q'
)

proofreading_chart = (proofreading_bar + proofreading_text).properties(
    #title=f'Books Written by Content Team in {selected_month} {selected_year}',
    width=300,
    height=390
)


col1, col2 = st.columns([1.4,1])

# Display proofreading remaining data in the first column
with col1:
    st.markdown(
        f"<h5>📖 {proofreading_complete_data_by_month_count} Books Proofreaded in {selected_month} "
        f"<span class='status-badge'>Status: Done!</span></h5>", 
        unsafe_allow_html=True
    )
    st.dataframe(proofreading_complete_data_by_month, use_container_width=False, hide_index=True)

# Display heading and chart in the second column with proper layout
with col2:
        st.markdown(
            f"<h5>📖 Book count by Team "
            f"<span class='status-badge'>Status: Done!</span></h5>", 
            unsafe_allow_html=True
        )
        st.altair_chart(proofreading_chart, use_container_width=True)
        #st.plotly_chart(proofreading_donut, use_container_width=True)


######################################################################################
######################------------- 40 days data-------------#########################
######################################################################################

import datetime
forty_five_days_ago = pd.Timestamp(today - datetime.timedelta(days=40))  # Convert to pandas Timestamp

# Filter the DataFrame
fortifiveday = operations_sheet_data_preprocess[
    operations_sheet_data_preprocess['Date'] <= forty_five_days_ago
]

# Further filter the DataFrame based on the 'Deliver' column
fortifiveday_status = fortifiveday[fortifiveday['Deliver'] == 'FALSE']

fortifiveday_status_months = list(fortifiveday_status['Month'].unique())
fortifiveday_status_months.append("Total") 

# Display the last 45 days data section with count, emoji, and title
st.markdown(
    f"<h5>📅 {fortifiveday_status['Book ID'].nunique()} Books on hold older than 40 days"
    f"<span class='status-badge-red'>Status: On Hold</span></h5>", 
    unsafe_allow_html=True
)

fortifiveday_status_selected_month = st.pills("2024", fortifiveday_status_months, selection_mode="single", 
                              default =fortifiveday_status_months[-1],label_visibility ='collapsed')

# Filter based on the selected month, or show all data if "All" is selected
if fortifiveday_status_selected_month == "Total":
    fortifiveday_status_by_month = fortifiveday_status
else:
    fortifiveday_status_by_month = fortifiveday_status[fortifiveday_status['Month'] == fortifiveday_status_selected_month]

# Define the columns in processing order and their readable names
status_columns = {
    'Writing Complete': 'Writing Incomplete',
    'Proofreading Complete': 'Proofreading Incomplete',
    'Formating Complete': 'Formatting Incomplete',
    'Send Cover Page and Agreement': 'Cover/Agreement Pending',
    'Agreement Received': 'Agreement Pending',
    'Digital Prof': 'Digital Proof Pending',
    'Confirmation': 'Confirmation Pending',
}

# Function to find the first stage where the book is stuck
def find_stuck_stage(row):
    for col, stage in status_columns.items():
        if row[col] == "FALSE":  # Check if column value is the string "FALSE"
            return stage
    return 'Not Dispatched'  # Shouldn't occur, as we filtered by Deliver == FALSE

# Apply the function to create a 'Stuck Stage' column
fortifiveday_status_by_month['Reason For Hold'] = fortifiveday_status_by_month.apply(find_stuck_stage, axis=1)

fortifiveday_status_by_month = fortifiveday_status_by_month[['Book ID', 'Book Title','Date','Month','Since Enrolled',
                                           'Reason For Hold','No of Author','Publishing Consultant 1','Writing End Date','Proofreading End Date',
                                           'Formating End Date','Send Cover Page and Agreement', 'Agreement Received',
                                             'Digital Prof','Confirmation', 'Ready to Print','Print']].fillna("Pending")


# Prepare the reason counts data
reason_counts = fortifiveday_status_by_month['Reason For Hold'].value_counts().reset_index()
reason_counts.columns = ['Reason For Hold', 'Count']

def number_to_color(number):
    if 40 <= number <= 45:
        return 'background-color: #FFA500; color: black'  # Light green
    else:
        return 'background-color: #FF6347; color: white' 
    
def reason_to_color(reason, color_map):
    color = color_map.get(reason, 'background-color: #FFFFFF; color: black')  # Default white background
    return f'{color}; color: black'

# Get unique reasons
unique_reasons = fortifiveday_status_by_month['Reason For Hold'].unique()
unique_publishing_consultants = fortifiveday_status_by_month['Publishing Consultant 1'].unique()

# Generate a color palette using Streamlit's theme
color_palette_reason = sns.color_palette("Set2", len(unique_reasons)).as_hex()
color_palette_consultant = sns.color_palette("Set3", len(unique_publishing_consultants)).as_hex()

# Create a mapping from reason to color
color_map_reason = {reason: f'background-color: {color}' for reason, color in zip(unique_reasons, color_palette_reason)}
color_map_consultant = {reason: f'background-color: {color}' for reason, color in zip(unique_publishing_consultants, color_palette_consultant)}

# Apply color to 'Since Enrolled' column
styled_df = fortifiveday_status_by_month.style.applymap(
   number_to_color,
    subset=['Since Enrolled']
)

styled_df = styled_df.applymap(
    lambda x: reason_to_color(x, color_map_reason),
    subset=['Reason For Hold']
)

styled_df = styled_df.applymap(
    lambda x: reason_to_color(x, color_map_consultant),
    subset=['Publishing Consultant 1']
)

# Create a pie chart with Plotly
pie_chart = px.pie(
    reason_counts,
    names='Reason For Hold',
    values='Count',
    title="Reason For Hold - Distribution",
    hole = 0.45,
    color_discrete_sequence=px.colors.sequential.Turbo # Custom color scheme
)

# Customize the layout (optional)
pie_chart.update_traces(textinfo='label+value', insidetextorientation='radial')
pie_chart.update_layout(title_x=0.3, showlegend=False)

# Use columns to display DataFrame and chart side by side
col1, col2 = st.columns([1.5, 1])


# Display DataFrame in the first column
with col1:
    st.markdown(f"##### 📋 {fortifiveday_status_by_month['Book ID'].nunique()} Books on hold in {fortifiveday_status_selected_month}")
    st.dataframe(styled_df, use_container_width=True, hide_index=True,column_config = {
        "Send Cover Page and Agreement": st.column_config.CheckboxColumn(
            "Send Cover Page and Agreement",
            default=False,
        ),
        "Agreement Received": st.column_config.CheckboxColumn(
            "Agreement Received",
            default=False,
        ),
        "Digital Prof": st.column_config.CheckboxColumn(
            "Digital Prof",
            default=False,
        ),
        "Confirmation": st.column_config.CheckboxColumn(
            "Confirmation",
            default=False,
        ),
        "Ready to Print": st.column_config.CheckboxColumn(
            "Ready to Print",
            default=False,
        ),
        "Print": st.column_config.CheckboxColumn(
            "Print",
            default=False,
        )
    })

# Display the pie chart in the second column
with col2:
    st.markdown("##### 📊 Pie Chart")
    st.plotly_chart(pie_chart, use_container_width=True)


###################################################################################################################
#####################----------- Recently added books----------######################
#####################################################################################################################

recent_books_data_columns = ['Book ID', 'Book Title', 'Date', 'No of Author','Publishing Consultant 1',
                                                      'Publishing Consultant 2','Publishing Consultant 3','Publishing Consultant 4',
                                                      'Author Name 1','Author Name 2','Author Name 3','Author Name 4']

recent_books_data = operations_sheet_data_preprocess[recent_books_data_columns]

# Adding "This Month" option
option = st.radio(
    "Select Time Range",
    ["Today", "Yesterday", "Last 10 Days", "This Month"],index =3,
    horizontal=True, label_visibility="hidden"
)


# Filter data based on the selected option
if option == "Today":
    filtered_df = num_book_today[recent_books_data_columns]
    heading = f"New Book Enrolled {today}"
elif option == "Yesterday":
    yesterday = today - timedelta(days=1)
    filtered_df = recent_books_data[recent_books_data['Date'] == pd.Timestamp(yesterday)]
    heading = f"Books Enrolled Yesterday {yesterday}"
elif option == "Last 10 Days":
    last_10_days = today - timedelta(days=10)
    filtered_df = recent_books_data[recent_books_data['Date'] >= pd.Timestamp(last_10_days)]
    heading = f"Books Enrolled in the Last 10 Days (Since {last_10_days})"
else:  # This Month
    filtered_df = operations_sheet_data_preprocess_month[recent_books_data_columns]
    heading = f"Books Enrolled in {selected_month} {selected_year}"

# Display heading with count
book_count = len(filtered_df)
books_per_day = filtered_df.groupby('Date').size().reset_index(name='Books Enrolled')


# Create an Altair line chart
line_chart_number_book = alt.Chart(books_per_day).mark_line().encode(
    x='Date:T',  # T is for temporal encoding (dates)
    y='Books Enrolled:Q',  
    color=alt.value("#4C78A8"),# Q is for quantitative encoding (the count of books)
    tooltip=['Date:T', 'Books Enrolled:Q'],
).properties(
    title="Books Enrolled Per Day"
)

# Add text labels on data points
text_line_chart_number_book = line_chart_number_book.mark_text(
    align='center',
    baseline='bottom',
    dy=-10
).encode(
    text='Books Enrolled:Q'
)

col1, col2 = st.columns([1.1,1])

with col1:
    st.markdown(
    f"<h5>📖 {book_count} {heading}", 
    unsafe_allow_html=True
)
    st.dataframe(filtered_df,hide_index=True, use_container_width=True)

with col2:
    st.altair_chart((line_chart_number_book+text_line_chart_number_book), use_container_width=True,theme="streamlit")




####################################################################################################
#####################-----------  Line Chart Monthly Books & Authors ----------######################
###################################################################################################


# Group by month and count unique 'Book ID's and 'Author ID's
monthly_book_author_counts = get_monthly_book_author_counts(operations_sheet_data_preprocess_year,month_order)
monthly_counts = monthly_book_author_counts.rename(columns={'Book ID': 'Total Books', 'Author Id': 'Total Authors'})

# Sort by the ordered month column
monthly_counts = monthly_counts.sort_values('Month')

st.subheader(f"📚 Books & Authors in {selected_year}")
st.caption("Number of books each month")
# Plot line chart
# Create an Altair line chart with labels on data points
line_chart = alt.Chart(monthly_counts).mark_line(point=True).encode(
    x=alt.X('Month', sort=month_order, title='Month'),
    y=alt.Y('Total Books', title='Total Count'),
    color=alt.value("#4C78A8")  # Color for Total Books line
).properties(
    width=600,
    height=400
)

# Line for Total Authors
line_chart_authors = alt.Chart(monthly_counts).mark_line(point=True).encode(
    x=alt.X('Month', sort=month_order),
    y=alt.Y('Total Authors'),
    color=alt.value("#F3C623")  # Color for Total Authors line
)

# Add text labels on data points
text_books = line_chart.mark_text(
    align='center',
    baseline='bottom',
    dy=-10
).encode(
    text='Total Books:Q'
)

text_authors = line_chart_authors.mark_text(
    align='center',
    baseline='bottom',
    dy=-10
).encode(
    text='Total Authors:Q'
)
st.altair_chart((line_chart + text_books + line_chart_authors + text_authors), use_container_width=True)

#####################################################################################################
#####################-----------  Bar chart Number of Books in Month ----------######################
####################################################################################################


# Count both TRUE and FALSE values for each relevant column
counts = {
    "Category": ["Writing", "Apply ISBN", "Cover Page", "Back Page Update", "Ready to Print", "Print", "Deliver"],
    "TRUE": [
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Writing Complete'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Apply ISBN'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Cover Page'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Back Page Update'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Ready to Print'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Print'] == 'TRUE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Deliver'] == 'TRUE']['Book ID'].nunique()
    ],
    "FALSE": [
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Writing Complete'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Apply ISBN'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Cover Page'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Back Page Update'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Ready to Print'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Print'] == 'FALSE']['Book ID'].nunique(),
        operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Deliver'] == 'FALSE']['Book ID'].nunique()
    ]
}

bar_data_df = pd.DataFrame(counts).melt(id_vars="Category", var_name="Status", value_name="Count")

######################################################################################################
#####################-----------  Bar chart Number of Authors in Month ----------######################
######################################################################################################


# # Count both TRUE and FALSE values for each relevant column (Authors Data)
# author_counts = {
#     "Category": [
#         "Welcome Mail / Confirmation", "Author Detail", "Photo", "ID Proof",
#         "Send Cover Page and Agreement", "Agreement Received", "Digital Prof", "Confirmation"
#     ],
#     "TRUE": [
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Welcome Mail / Confirmation'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Author Detail'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Photo'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['ID Proof'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Send Cover Page and Agreement'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Agreement Received'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Digital Prof'] == 'TRUE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Confirmation'] == 'TRUE']['Author Id'].nunique()
#     ],
#     "FALSE": [
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Welcome Mail / Confirmation'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Author Detail'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Photo'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['ID Proof'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Send Cover Page and Agreement'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Agreement Received'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Digital Prof'] == 'FALSE']['Author Id'].nunique(),
#         operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Confirmation'] == 'FALSE']['Author Id'].nunique()
#     ]
# }

# # Convert to DataFrame
# author_bar_data_df = pd.DataFrame(author_counts).melt(id_vars="Category", var_name="Status", value_name="Count")

# # Generate the grouped bar charts
book_bar_chart = create_grouped_bar_chart(bar_data_df, f"Books in {selected_month}", color_scheme=["#E14F47", "#7DDA58"])
# author_bar_chart = create_grouped_bar_chart(author_bar_data_df, f"Authors in {selected_month}", color_scheme=["#E14F47", "#7DDA58"])

# Display the charts in Streamlit
st.subheader(f"📚 Books & Authors in {selected_month}")
with st.container():
    _, col1, col2, _ = st.columns([0.009, 1, 1, 0.009])
    with col1:
        st.altair_chart(book_bar_chart, use_container_width=True)
    with col2:
        st.write("New Graph comming soon!😊")
        #st.altair_chart(author_bar_chart, use_container_width=True)

#######################################################################################################
###################------------- Horizonrtal bar graph Employee Performance----------##################
#######################################################################################################

# Monthly data for a specific month
operations_sheet_data_preprocess_writng_month = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%B') == str(selected_month))
]
employee_monthly = operations_sheet_data_preprocess_writng_month.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

# Full year data
operations_sheet_data_preprocess_writng_year = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(selected_year))
]
employee_yearly = operations_sheet_data_preprocess_writng_year.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

# Altair chart for monthly data with layering of bars and text
monthly_bars = alt.Chart(employee_monthly).mark_bar(color='#F3C623').encode(
    x=alt.X('Book ID:Q', title='Number of Books'),
    y=alt.Y('Writing By:N', title='Employee', sort='-x'),
)

# Add text labels to the monthly bars
monthly_text = monthly_bars.mark_text(
    align='left',
    dx=5  # Adjust horizontal position of text
).encode(
    text='Book ID:Q'
)

# Layer bar and text for monthly chart
monthly_chart = (monthly_bars + monthly_text).properties(
    title=f'Books Written by Content Team in {selected_month} {selected_year}',
    width=300,
    height=400
)

# Altair chart for yearly data with layering of bars and text
yearly_bars = alt.Chart(employee_yearly).mark_bar(color='#4c78a8').encode(
    x=alt.X('Book ID:Q', title='Number of Books'),
    y=alt.Y('Writing By:N', title='Employee', sort='-x'),
)

# Add text labels to the yearly bars
yearly_text = yearly_bars.mark_text(
    align='left',
    dx=5  # Adjust horizontal position of text
).encode(
    text='Book ID:Q'
)

# Layer bar and text for yearly chart
yearly_chart = (yearly_bars + yearly_text).properties(
    title=f'Total Books Written by Content Team in {selected_year}',
    width=300,
    height=400
)

# Display charts side by side in Streamlit
st.subheader(f"📝 Content Team Performance in {selected_year}")
#st.caption("Content Team performance in each month and in 2024")
col1, col2 = st.columns(2)

with col1:
    st.altair_chart(monthly_chart, use_container_width=True)

with col2:
    st.altair_chart(yearly_chart, use_container_width=True)

######################################################################################
###############------------- Bar Chart Formatting & Proofread -----------############
######################################################################################

operations_sheet_data_preprocess_proof_month = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%B') == str(selected_month))
]
proofreading_num = operations_sheet_data_preprocess_proof_month.groupby('Proofreading By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
proofreading_num.columns = ['Proofreader', 'Book Count']

# Formatting data
operations_sheet_data_preprocess_format_month = operations_sheet_data_preprocess[
    (operations_sheet_data_preprocess['Formating End Date'].dt.strftime('%Y') == str(selected_year)) & 
    (operations_sheet_data_preprocess['Formating End Date'].dt.strftime('%B') == str(selected_month))
]
formatting_num = operations_sheet_data_preprocess_format_month.groupby('Formating By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
formatting_num.columns = ['Formatter', 'Book Count']

# Create the bar chart for Proofreading
proofreading_bar = alt.Chart(proofreading_num).mark_bar().encode(
    x=alt.X('Proofreader', sort='-y', title='Proofreader'),
    y=alt.Y('Book Count', title='Book Count'),
    color=alt.Color('Proofreader', legend=None),
    tooltip=['Proofreader', 'Book Count']
).properties(
    title=f"Books Proofread in {selected_month} {selected_year}"
)

# Add labels on top of the bars for Proofreading
proofreading_text = proofreading_bar.mark_text(
    dy=-10,  # Adjusts the position of the text above the bar
    color='black'
).encode(
    text='Book Count:Q'
)

# Combine bar chart and labels for Proofreading
proofreading_chart = proofreading_bar + proofreading_text

# Create the bar chart for Formatting
formatting_bar = alt.Chart(formatting_num).mark_bar().encode(
    x=alt.X('Formatter', sort='-y', title='Formatter'),
    y=alt.Y('Book Count', title='Book Count'),
    color=alt.Color('Formatter', legend=None),
    tooltip=['Formatter', 'Book Count']
).properties(
    title=f"Books Formatted in {selected_month} {selected_year}"
)

# Add labels on top of the bars for Formatting
formatting_text = formatting_bar.mark_text(
    dy=-10,
    color='black'
).encode(
    text='Book Count:Q'
)

# Combine bar chart and labels for Formatting
formatting_chart = formatting_bar + formatting_text

# Display charts in Streamlit columns
col1, col2 = st.columns(2)

with col1:
    st.altair_chart(proofreading_chart, use_container_width=True)

with col2:
    st.altair_chart(formatting_chart, use_container_width=True)

######################################################################################################################
#####################-----------  Bar chart Number of Monthly Books & Authors in 2024 ----------######################
######################################################################################################################

# Group by month and count unique 'Book ID's
monthly_book_counts =  monthly_book_author_counts[['Month', 'Total Books']]
monthly_book_counts.columns = ['Month', 'Total Books']

# Sort by the ordered month column
monthly_book_counts = monthly_book_counts.sort_values('Month')

# Group by month and count unique 'Book ID's
monthly_author_counts =  monthly_book_author_counts[['Month', 'Total Authors']]
monthly_author_counts.columns = ['Month', 'Total Authors']

# Sort by the ordered month column
monthly_author_counts = monthly_author_counts.sort_values('Month')

# Create an Altair bar chart for "Total Books" with count labels
book_chart = alt.Chart(monthly_book_counts).mark_bar(color="#4c78a8").encode(
    x=alt.X('Month', sort=month_order, title='Month'),
    y=alt.Y('Total Books', title='Total Books')
).properties(
    width=300,
    height=400
)

# Add text labels to "Total Books" bar chart
book_text = book_chart.mark_text(
    align='center',
    baseline='bottom',
    dy=-5
).encode(
    text='Total Books:Q'
)

# Create an Altair bar chart for "Total Authors" with count labels
author_chart = alt.Chart(monthly_author_counts).mark_bar(color="#F3C623").encode(
    x=alt.X('Month', sort=month_order, title='Month'),
    y=alt.Y('Total Authors', title='Total Authors')
).properties(
    width=300,
    height=400
)

# Add text labels to "Total Authors" bar chart
author_text = author_chart.mark_text(
    align='center',
    baseline='bottom',
    dy=-5
).encode(
    text='Total Authors:Q'
)

# Display the two charts side by side in a single row
st.subheader(f"📅 Monthly Books & Authors in {selected_year}")
st.caption("Performance comparison of total books and authors by month")

# Arrange in columns within a container
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(book_chart + book_text, use_container_width=True)
    with col2:
        st.altair_chart(author_chart + author_text, use_container_width=True)


###################################################################################################################
#####################----------- Pie Books and Authors added by Publishing Consultan----------######################
#####################################################################################################################

# Number of authors added by Publishing Consultant
authors_added_yearly = operations_sheet_data_preprocess_year[['Publishing Consultant 1','Publishing Consultant 2',
                                       'Publishing Consultant 3','Publishing Consultant 4',]].apply(pd.Series.value_counts).sum(axis=1).reset_index().rename(columns={'index':'Publishing Consultant',0:'Authors Added'})
authors_added_yearly['Authors Added'] = authors_added_yearly['Authors Added'].astype(int)

# Number of books sold by Publishing Consultant
authors_added_montly = operations_sheet_data_preprocess_month[['Publishing Consultant 1','Publishing Consultant 2',
                                       'Publishing Consultant 3','Publishing Consultant 4',]].apply(pd.Series.value_counts).sum(axis=1).reset_index().rename(columns={'index':'Publishing Consultant',0:'Authors Added'})
authors_added_montly['Authors Added'] = authors_added_montly['Authors Added'].astype(int)


# Plotly Express pie chart for "Books Sold"
fig_authors_added_montly = px.pie(
    authors_added_montly,
    names="Publishing Consultant",
    values="Authors Added",
    title=f"Authors Enrolled in {selected_month} {selected_year}",
    hole = 0.45,
    color_discrete_sequence=['#4C78A8', '#F3C623']  # Custom color scheme
)
fig_authors_added_montly.update_traces(textinfo='label+value', insidetextorientation='radial')

# Plotly Express pie chart for "Authors Added"
fig_authors_added_yearly = px.pie(
    authors_added_yearly,
    names="Publishing Consultant",
    values="Authors Added",
    title=f"Authors Enrolled in {selected_year}",
    hole = 0.45,
    color_discrete_sequence=['#4C78A8', '#F3C623'] # Custom color scheme
)
fig_authors_added_yearly.update_traces(textinfo='label+value', insidetextorientation='radial')

# Display in Streamlit
st.subheader(f"💼 Publishing Consultant Performance in {selected_month} {selected_year}")
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_authors_added_montly, use_container_width=True)

with col2:
    st.plotly_chart(fig_authors_added_yearly, use_container_width=True)



if selected_year == 2024:
    operations_sheet_data_preprocess_year["duration_days"] = (
    operations_sheet_data_preprocess_year["Formating End Date"] - operations_sheet_data_preprocess_year["Writing Start Date"]
    ).dt.days

    # Extract the month name from the Writing Start Date
    operations_sheet_data_preprocess_year["book_start_month"] = operations_sheet_data_preprocess_year["Writing Start Date"].dt.strftime('%B')

    # Calculate Median Duration and Total Books per Month
    average_duration_by_month = operations_sheet_data_preprocess_year.groupby("book_start_month").agg(
        duration_days_median=("duration_days", "median"),
        total_books=("duration_days", "count")
    ).reset_index()

    # Round the median duration days
    average_duration_by_month["duration_days_median"] = average_duration_by_month["duration_days_median"].apply(lambda x: round(x))

    # Streamlit Title
    st.subheader("📈 Average of Books Written Each Month in 2024")

    # Create the line chart for median duration
    line_chart = alt.Chart(average_duration_by_month).mark_line(point=True, color="orange").encode(
        x=alt.X("book_start_month:N", title="Month", sort=month_order),
        y=alt.Y("duration_days_median:Q", title="Median Duration (Days)"),
        tooltip=["book_start_month", "duration_days_median"]
    )

    # Add text annotations on the line chart points
    line_text = line_chart.mark_text(
        align="center",
        baseline="middle",
        dy=-15,  # Position above the point
        color="black"
    ).encode(
        text="duration_days_median:Q"
    )

    combined_chart = alt.layer(
     
        line_chart + line_text  
    ).resolve_scale(
        y="independent" 
    ).properties(
        width=700,  
        height=400  
    )

    st.altair_chart(combined_chart, use_container_width=True)

else:
    st.write("Please Select 2024 year to see the Median Duration and Total Books by Month")