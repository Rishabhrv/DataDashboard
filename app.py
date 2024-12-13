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
import jwt
from dotenv import load_dotenv
import webbrowser

start_time = time.time()

# Set page configuration
st.set_page_config(
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="auto",  # Automatically collapse the sidebar
     page_title="Data Dashboard",
)

load_dotenv()
# Use the same secret key as MasterSheet3
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key') 

def validate_token():
    # Extract the token from query parameters
    params = st.query_params
    if 'token' not in params:
        st.error("Access Denied: Login Required")
        st.stop()

    token = params['token']
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        #st.success(f"Welcome {decoded_token['user']}! Role: {decoded_token['role']}")
    except jwt.ExpiredSignatureError:
        st.error("Access Denied: Token has expired.")
        st.stop()
    except jwt.InvalidTokenError:
        st.error("Access Denied: Invalid token.")
        st.stop()

# Validate token before running the app
validate_token()

sheets = read_sheets_from_json()

# Load data and preprocess
operations_sheet_data = sheet_to_df(sheets['Operations'])
mastersheet_data = sheet_to_df(sheets['Mastersheet'])

operations_sheet_data_preprocess = operations_preprocess(operations_sheet_data)
mastersheet_data_preprocess = mastersheet_preprocess(mastersheet_data)

unique_months = operations_sheet_data_preprocess['Month'].unique() 
from datetime import datetime
unique_months_sorted = sorted(unique_months, key=lambda x: datetime.strptime(x, "%B")) # Get unique month names

# Map month numbers to month names and set the order
month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]

# Example layout
col1, col2 = st.columns([14, 2])  # Adjust column widths as needed

with col1:
    selected_month = st.pills("2024", unique_months_sorted, selection_mode="single", 
                              default =unique_months_sorted[-1],label_visibility ='collapsed')

with col2:
    adsearch_clicked = st.button("Search Books", icon = "🔍",type = "secondary")


# Define API URL and secure API key
MASTERSHEET_API_URL = "https://agkitdatabase.agvolumes.com/redirect_to_adsearch"

if adsearch_clicked:
    # Prepare user details for token generation
    user_details = {
        "user": "Admin User",  # Replace with actual user details
        "role": "Admin"
    }

    headers = {
        "Authorization": SECRET_KEY
    }

    try:
        # Send POST request to Mastersheet app
        response = requests.post(MASTERSHEET_API_URL, json=user_details, headers=headers)
        if response.status_code == 200:
            adsearch_url = response.json().get("url")
            webbrowser.open(adsearch_url)  # Open Adsearch in the default browser
        else:
            st.error("Failed to generate AdSearch URL. Please try again.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

######################################################################################
#####################----------- Metrics of Selected Month ----------######################
######################################################################################

# Filter DataFrame based on selected month
mastersheet_data_preprocess_month = mastersheet_data_preprocess[mastersheet_data_preprocess['Date'].dt.strftime('%B') == selected_month]
operations_sheet_data_preprocess_month = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Month']== selected_month]

# Calculate metrics based on both TRUE and FALSE values in the filtered DataFrame

total_authors = len(np.array(mastersheet_data_preprocess_month['Author Id'].unique())[np.array(mastersheet_data_preprocess_month['Author Id'].unique()) !=''])

total_books= len(np.array(operations_sheet_data_preprocess_month['Book ID'].unique())[np.array(operations_sheet_data_preprocess_month['Book ID'].unique()) !=''])
#total_authors = len(np.array(operations_sheet_data_preprocess_month['Author Id'].unique())[np.array(operations_sheet_data_preprocess_month['Author Id'].unique()) !=''])

books_written_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Writing Complete'] == 'TRUE']['Book ID'].nunique()
books_proofread_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Proofreading Complete'] == 'TRUE']['Book ID'].nunique()
books_formatted_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Formating Complete'] == 'TRUE']['Book ID'].nunique()


books_complete = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Book Complete'] == 'TRUE']['Book ID'].nunique()
#books_apply_isbn_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Apply ISBN'] == 'TRUE']['Book ID'].nunique()
books_printed_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Print'] == 'TRUE']['Book ID'].nunique()
books_delivered_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Deliver'] == 'TRUE']['Book ID'].nunique()
books_apply_isbn_true = mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Apply ISBN'] == 'TRUE']['Book ID'].nunique()

import time

st.subheader(f"Metrics of {selected_month}")

# Create a placeholder for the status
status_placeholder = st.empty()

with status_placeholder.container():
    with st.status(f"Loading {selected_month} Data", expanded=False) as status:
        time.sleep(1)
        st.text("Calling Google Sheet API..")
        time.sleep(1)
        st.text("Processing Data..")
        time.sleep(1)
        st.text("Plotting Graphs..")
        time.sleep(1)
        status.update(
            label="Data Loaded!", state="complete", expanded=False)

# Replace the status element with an empty container to "hide" it
status_placeholder.empty()

with st.container():
    # Display metrics with TRUE counts in value and FALSE counts in delta
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    col1.metric("Total Books", total_books)
    col2.metric("Total Authors", total_authors)
    col3.metric("Written", books_written_true, delta=f"-{total_books - books_written_true} Remaining")
    col4.metric("Proofread", books_proofread_true, delta=f"-{books_written_true - books_proofread_true} Remaining")
    col5.metric("Formatting", books_formatted_true, delta=f"-{books_proofread_true - books_formatted_true} Remaining")
    col6.metric("Book Complete", books_complete, delta=f"-{total_books - books_complete} not complete")
    col7.metric("ISBN Received", books_apply_isbn_true, delta=f"-{total_books - books_apply_isbn_true} not received")
    col8.metric("Printed", books_printed_true, delta=f"-{total_books - books_printed_true} not printed")
    col9.metric("Delivered", books_delivered_true, delta=f"-{total_books - books_delivered_true} not delivered")


######################################################################################
###########################----------- Spinner ----------#############################
######################################################################################


# with st.spinner('Loading Data...'):
#     time.sleep(4)


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

# Define the icon and message for each status
status_messages = [
    {"emoji": "✍️", "label": "Writing", "count": len(results['Writing']), "data": results['Writing']},
    {"emoji": "📖", "label": "Proofreading", "count": len(results['Proofreading']), "data": results['Proofreading']},
    {"emoji": "🖋️", "label": "Formatting", "count": len(results['Formating']), "data": results['Formating']}
]

# Display each status section with count, emoji, and data
for status in status_messages:
    st.markdown(
        f"<h4>{status['emoji']} {status['count']} Books in {status['label']} Today "
        f"<span class='status-badge'>Status: Running</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(status['data'], use_container_width=True, hide_index=True)


######################################################################################
###############----------- Current day status dataframe -------------################
######################################################################################

work_done_status = work_done_status(operations_sheet_data_preprocess)

# Display the last 45 days data section with count, emoji, and title
st.markdown(
    f"<h4>✅ Work done on {work_done_status['Book ID'].nunique()} Books on Previous day & Today"
    f"<span class='status-badge'>Status: Done!</span></h4>", 
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
    h4 {
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# Define two columns to display dataframes side by side
col1, col2 = st.columns(2)

# Display writing remaining data in the first column
with col1:
    st.markdown(
        f"<h4>✍️ {writing_remaining_count} Books in Writing Remaining "
        f"<span class='status-badge'>Status: Remaining</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(writing_remaining_data, use_container_width=False, hide_index=True)

# Display proofreading remaining data in the second column
with col2:
    st.markdown(
        f"<h4>📖 {proofread_remaining_count} Books in Proofreading Remaining "
        f"<span class='status-badge'>Status: Remaining</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(proofread_remaining_data, use_container_width=False, hide_index=True)


####################################################################################################
################-----------  Writing & Proofreading complete in this Month ----------##############
####################################################################################################


writing_complete_data_by_month, writing_complete_data_by_month_count = writing_complete(operations_sheet_data_preprocess, 
                                                                                        selected_month)
proofreading_complete_data_by_month, proofreading_complete_data_by_month_count = proofreading_complete(operations_sheet_data_preprocess, 
                                                                                                       selected_month)


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
    h4 {
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# Define two columns to display dataframes side by side
col1, col2 = st.columns(2)

# Display writing remaining data in the first column
with col1:
    st.markdown(
        f"<h4>✍️ {writing_complete_data_by_month_count} Books Written in {selected_month}"
        f"<span class='status-badge'>Status: Done!</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(writing_complete_data_by_month, use_container_width=False, hide_index=True)

# Display proofreading remaining data in the second column
with col2:
    st.markdown(
        f"<h4>📖 {proofreading_complete_data_by_month_count} Books Proofreaded in {selected_month} "
        f"<span class='status-badge'>Status: Done!</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(proofreading_complete_data_by_month, use_container_width=False, hide_index=True)


######################################################################################
######################------------- 40 days data-------------#########################
######################################################################################

import datetime

# Calculate today and 45 days ago as datetime.date objects
today = datetime.date.today()
forty_five_days_ago = pd.Timestamp(today - datetime.timedelta(days=40))  # Convert to pandas Timestamp

# Filter the DataFrame
fortifiveday = operations_sheet_data_preprocess[
    operations_sheet_data_preprocess['Date'] <= forty_five_days_ago
]

# Further filter the DataFrame based on the 'Deliver' column
fortifiveday_status = fortifiveday[fortifiveday['Deliver'] == 'FALSE']


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
fortifiveday_status['Reason For Hold'] = fortifiveday_status.apply(find_stuck_stage, axis=1)

fortifiveday_status = fortifiveday_status[['Book ID', 'Book Title','Date','Month','Since Enrolled','No of Author',
                                           'Reason For Hold','Writing End Date','Proofreading End Date',
                                           'Formating End Date','Send Cover Page and Agreement', 'Agreement Received',
                                             'Digital Prof','Confirmation', 'Ready to Print','Print']].fillna("Pending")


# Display the last 45 days data section with count, emoji, and title
st.markdown(
    f"<h4>📅 {fortifiveday_status['Book ID'].nunique()} Books on hold older than 40 days"
    f"<span class='status-badge'>Status: On Hold</span></h4>", 
    unsafe_allow_html=True
)

# Prepare the reason counts data
reason_counts = fortifiveday_status['Reason For Hold'].value_counts().reset_index()
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
unique_reasons = fortifiveday_status['Reason For Hold'].unique()

# Generate a color palette using Streamlit's theme
color_palette = sns.color_palette("Set2", len(unique_reasons)).as_hex()

# Create a mapping from reason to color
color_map = {reason: f'background-color: {color}' for reason, color in zip(unique_reasons, color_palette)}

# Apply color to 'Since Enrolled' column
styled_df = fortifiveday_status.style.applymap(
   number_to_color,
    subset=['Since Enrolled']
)

styled_df = styled_df.applymap(
    lambda x: reason_to_color(x, color_map),
    subset=['Reason For Hold']
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
    st.markdown("#### 📋 Data")
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
    st.markdown("#### 📊 Pie Chart")
    st.plotly_chart(pie_chart, use_container_width=True)



####################################################################################################
#####################-----------  Line Chart Monthly Books & Authors ----------######################
###################################################################################################


# Group by month and count unique 'Book ID's and 'Author ID's
monthly_counts = mastersheet_data_preprocess.groupby(mastersheet_data_preprocess['Date'].dt.month).agg({
    'Book ID': 'nunique',
    'Author Id': 'nunique'
}).reset_index()

# Rename columns for clarity
monthly_counts['Month'] = monthly_counts['Date'].apply(lambda x: pd.to_datetime(f"2024-{x}-01").strftime('%B'))
monthly_counts = monthly_counts.rename(columns={'Book ID': 'Total Books', 'Author Id': 'Total Authors'})

monthly_counts['Month'] = pd.Categorical(monthly_counts['Month'], categories=month_order, ordered=True)

# Sort by the ordered month column
monthly_counts = monthly_counts.sort_values('Month')

# Melt the data for easier line plotting with color distinction
monthly_counts_melted = monthly_counts.melt(id_vars='Month', value_vars=['Total Books', 'Total Authors'], 
                                            var_name='Status', value_name='Count')

st.subheader("Books & Authors in 2024")
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
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Writing'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Apply ISBN'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Cover Page'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Back Page Update'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Ready to Print'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Print'] == 'TRUE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Deliver'] == 'TRUE']['Book ID'].nunique()
    ],
    "FALSE": [
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Writing'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Apply ISBN'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Cover Page'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Back Page Update'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Ready to Print'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Print'] == 'FALSE']['Book ID'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Deliver'] == 'FALSE']['Book ID'].nunique()
    ]
}

bar_data_df = pd.DataFrame(counts).melt(id_vars="Category", var_name="Status", value_name="Count")

######################################################################################################
#####################-----------  Bar chart Number of Authors in Month ----------######################
######################################################################################################


# Count both TRUE and FALSE values for each relevant column (Authors Data)
author_counts = {
    "Category": [
        "Welcome Mail / Confirmation", "Author Detail", "Photo", "ID Proof",
        "Send Cover Page and Agreement", "Agreement Received", "Digital Prof", "Confirmation"
    ],
    "TRUE": [
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Welcome Mail / Confirmation'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Author Detail'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Photo'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['ID Proof'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Send Cover Page and Agreement'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Agreement Received'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Digital Prof'] == 'TRUE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Confirmation'] == 'TRUE']['Author Id'].nunique()
    ],
    "FALSE": [
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Welcome Mail / Confirmation'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Author Detail'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Photo'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['ID Proof'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Send Cover Page and Agreement'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Agreement Received'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Digital Prof'] == 'FALSE']['Author Id'].nunique(),
        mastersheet_data_preprocess_month[mastersheet_data_preprocess_month['Confirmation'] == 'FALSE']['Author Id'].nunique()
    ]
}

# Convert to DataFrame
author_bar_data_df = pd.DataFrame(author_counts).melt(id_vars="Category", var_name="Status", value_name="Count")

# Generate the grouped bar charts
book_bar_chart = create_grouped_bar_chart(bar_data_df, f"Books in {selected_month}", color_scheme=["#E14F47", "#7DDA58"])
author_bar_chart = create_grouped_bar_chart(author_bar_data_df, f"Authors in {selected_month}", color_scheme=["#E14F47", "#7DDA58"])

# Display the charts in Streamlit
st.subheader(f"Books & Authors in {selected_month}")
with st.container():
    _, col1, col2, _ = st.columns([0.009, 1, 1, 0.009])
    with col1:
        st.altair_chart(book_bar_chart, use_container_width=True)
    with col2:
        st.altair_chart(author_bar_chart, use_container_width=True)

#######################################################################################################
###################------------- Horizonrtal bar graph Employee Performance----------##################
#######################################################################################################

# Monthly data for a specific month
operations_sheet_data_preprocess_writng_month = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%B') == selected_month]
employee_monthly = operations_sheet_data_preprocess_writng_month.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

# Full year data
employee_yearly = operations_sheet_data_preprocess.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

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
    title=f'Books Written by Content Team in {selected_month}',
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
    title='Total Books Written by Content Team in 2024',
    width=300,
    height=400
)

# Display charts side by side in Streamlit
st.subheader("Content Team Performance")
#st.caption("Content Team performance in each month and in 2024")
col1, col2 = st.columns(2)

with col1:
    st.altair_chart(monthly_chart, use_container_width=True)

with col2:
    st.altair_chart(yearly_chart, use_container_width=True)

######################################################################################
###############------------- Bar Chart Formatting & Proofread -----------############
######################################################################################

operations_sheet_data_preprocess_proof_month = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%B') == selected_month]
proofreading_num = operations_sheet_data_preprocess_proof_month.groupby('Proofreading By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
proofreading_num.columns = ['Proofreader', 'Book Count']
# Formatting data
operations_sheet_data_preprocess_format_month = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Formating End Date'].dt.strftime('%B') == 'November']
formatting_num = operations_sheet_data_preprocess_format_month.groupby('Formating By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
formatting_num.columns = ['Formatter', 'Book Count']

# Create the bar chart for Proofreading
proofreading_bar = alt.Chart(proofreading_num).mark_bar().encode(
    x=alt.X('Proofreader', sort='-y', title='Proofreader'),
    y=alt.Y('Book Count', title='Book Count'),
    color=alt.Color('Proofreader', legend=None),
    tooltip=['Proofreader', 'Book Count']
).properties(
    title=f"Books Proofread in {selected_month}"
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
    title=f"Books Formatted in {selected_month}"
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
monthly_book_counts =  mastersheet_data_preprocess[mastersheet_data_preprocess['Book ID'] != ''].groupby(mastersheet_data_preprocess['Date'].dt.month)['Book ID'].nunique().reset_index()
monthly_book_counts.columns = ['Month', 'Total Books']

monthly_book_counts['Month'] = monthly_book_counts['Month'].apply(lambda x: month_order[x - 1])
monthly_book_counts['Month'] = pd.Categorical(monthly_book_counts['Month'], categories=month_order, ordered=True)

# Sort by the ordered month column
monthly_book_counts = monthly_book_counts.sort_values('Month')

# Group by month and count unique 'Book ID's
monthly_author_counts =  mastersheet_data_preprocess[mastersheet_data_preprocess['Author Id'] != ''].groupby(mastersheet_data_preprocess['Date'].dt.month)['Author Id'].nunique().reset_index()
monthly_author_counts.columns = ['Month', 'Total Authors']

monthly_author_counts['Month'] = monthly_author_counts['Month'].apply(lambda x: month_order[x - 1])
monthly_author_counts['Month'] = pd.Categorical(monthly_author_counts['Month'], categories=month_order, ordered=True)

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
st.subheader("Monthly Books & Authors in 2024")
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

# Number of books sold by Publishing Consultant
books_sold = mastersheet_data_preprocess_month.groupby(['Publishing Consultant'])['Book ID'].nunique().reset_index(name='Books Sold').iloc[1:]

# Number of authors added by Publishing Consultant
authors_added = mastersheet_data_preprocess_month.groupby(['Publishing Consultant'])['Author Id'].nunique().reset_index(name='Authors Added').iloc[1:]

# Plotly Express pie chart for "Books Sold"
fig_books_sold = px.pie(
    books_sold,
    names="Publishing Consultant",
    values="Books Sold",
    title=f"Books Enrolled in {selected_month}",
    hole = 0.45,
    color_discrete_sequence=['#4C78A8', '#F3C623']  # Custom color scheme
)
fig_books_sold.update_traces(textinfo='label+value', insidetextorientation='radial')

# Plotly Express pie chart for "Authors Added"
fig_authors_added = px.pie(
    authors_added,
    names="Publishing Consultant",
    values="Authors Added",
    title=f"Authors Enrolled in {selected_month}",
    hole = 0.45,
    color_discrete_sequence=['#4C78A8', '#F3C623'] # Custom color scheme
)
fig_authors_added.update_traces(textinfo='label+value', insidetextorientation='radial')

# Display in Streamlit
st.subheader(f"Publishing Consultant Performance in {selected_month}")
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_books_sold, use_container_width=True)

with col2:
    st.plotly_chart(fig_authors_added, use_container_width=True)

end_time = time.time()
elapsed_time = end_time - start_time

st.toast(f'{selected_month} Data took {round(elapsed_time,2)} sec to load', icon='📥')
    