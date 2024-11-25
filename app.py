import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import pandas as pd
from datetime import datetime
import time
import numpy as np
from preprocessing import *
import datetime

# Set page configuration
st.set_page_config(
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="auto",  # Automatically collapse the sidebar
     page_title="Data Dashboard",
)

sheets = read_sheets_from_json()

# Load data and preprocess
track_sheet_data = fetch_track_sheet_data(sheets['Track Sheet'])
writing_sheet_data = fetch_writing_sheet_data(sheets['Writing'])
operations_sheet_data = sheet_to_df(sheets['Operations'])
df = sheet_to_df(sheets['Mastersheet'])


track_sheet_data_bystart = track_writing_sheet_preproces(track_sheet_data)
track_sheet_data_byend = track_writing_sheet_preproces(track_sheet_data, by_col = 'Writing Date')
writing_sheet_data = track_writing_sheet_preproces(writing_sheet_data)
formatting_data = track_writing_sheet_preproces(track_sheet_data, by_col = 'Formatting Date')
proofreading_data = track_writing_sheet_preproces(track_sheet_data, by_col = 'Proofreading Date')

cols = ['Date','Book ID', 'Writing', 'Apply ISBN', 'ISBN', 'Cover Page', 'Back Page Update', 'Ready to Print','Print',
        'Amazon Link', 'AGPH Link', 'Google Link', 'Flipkart Link','Final Mail', 'Deliver', 'Google Review' ]

for i in cols:
    df[i] = df[i].shift(-1)

df['Date'] = pd.to_datetime(df['Date'],  format= "%d/%m/%Y")
df['Book ID'] = pd.to_numeric(df['Book ID'], errors='coerce')
df['Date'] = df['Date'].ffill()
df['Book ID'] = df['Book ID'].ffill()
df = df[df['Date'].dt.year == 2024]

# Month selector based on available months in the dataset
df['Month'] = df['Date'].dt.strftime('%B')  # Format to full month names
unique_months = df['Month'].unique() 
from datetime import datetime
unique_months_sorted = sorted(unique_months, key=lambda x: datetime.strptime(x, "%B")) # Get unique month names

# Map month numbers to month names and set the order
month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]
selected_month = st.pills("2024", unique_months_sorted, selection_mode="single", default =unique_months_sorted[-1],label_visibility ='collapsed')

######################################################################################
#####################----------- Metrics of September ----------######################
######################################################################################

# Filter DataFrame based on selected month
filtered_df = df[df['Date'].dt.strftime('%B') == selected_month]
filtered_track_sheet_data_bystart = track_sheet_data_bystart[track_sheet_data_bystart['Date'].dt.strftime('%B') == selected_month]
filtered_track_sheet_data_byend = track_sheet_data_byend[track_sheet_data_byend['Writing Date'].dt.strftime('%B') == selected_month]
filtered_writing_sheet_data = writing_sheet_data[writing_sheet_data['Date'].dt.strftime('%B') == selected_month]
filtered_proofreading_data = proofreading_data[proofreading_data['Proofreading Date'].dt.strftime('%B') == selected_month]
filtered_formatting_data = formatting_data[formatting_data['Formatting Date'].dt.strftime('%B') == selected_month]

# Calculate metrics based on both TRUE and FALSE values in the filtered DataFrame
total_books= len(np.array(filtered_df['Book ID'].unique())[np.array(filtered_df['Book ID'].unique()) !=''])
total_authors = len(np.array(filtered_df['Author Id'].unique())[np.array(filtered_df['Author Id'].unique()) !=''])
books_written_true = filtered_writing_sheet_data[filtered_writing_sheet_data['Writing Complete'] == 'TRUE']['Book ID'].nunique()
books_written_false = filtered_writing_sheet_data[filtered_writing_sheet_data['Writing Complete'] == 'FALSE']['Book ID'].nunique()
books_proofread_true = filtered_track_sheet_data_bystart[filtered_track_sheet_data_bystart['Proofreading Status'] == 'TRUE']['Book ID'].nunique()
books_proofread_false = filtered_track_sheet_data_bystart[filtered_track_sheet_data_bystart['Proofreading Status'] == 'FALSE']['Book ID'].nunique()
books_formatted_true = filtered_track_sheet_data_bystart[filtered_track_sheet_data_bystart['Formatting Status'] == 'TRUE']['Book ID'].nunique()
books_formatted_false = filtered_track_sheet_data_bystart[filtered_track_sheet_data_bystart['Formatting Status'] == 'FALSE']['Book ID'].nunique()
books_in_written_true = filtered_df[filtered_df['Writing'] == 'TRUE']['Book ID'].nunique()
books_in_written_false = filtered_df[filtered_df['Writing'] == 'FALSE']['Book ID'].nunique()
books_apply_isbn_true = filtered_df[filtered_df['Apply ISBN'] == 'TRUE']['Book ID'].nunique()
books_apply_isbn_false = filtered_df[filtered_df['Apply ISBN'] == 'FALSE']['Book ID'].nunique()
books_printed_true = filtered_df[filtered_df['Print'] == 'TRUE']['Book ID'].nunique()
books_printed_false = filtered_df[filtered_df['Print'] == 'FALSE']['Book ID'].nunique()
books_delivered_true = filtered_df[filtered_df['Deliver'] == 'TRUE']['Book ID'].nunique()
books_delivered_false = filtered_df[filtered_df['Deliver'] == 'FALSE']['Book ID'].nunique()

import time

st.subheader(f"Metrics of {selected_month}")

# Create a placeholder for the status
status_placeholder = st.empty()

with status_placeholder.container():
    with st.status("Fetching Data", expanded=True) as status:
        time.sleep(1)
        st.write("Calling Google Sheet API..")
        time.sleep(2)
        st.write("Processing Data..")
        time.sleep(2)
        st.write("Plotting Graphs..")
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
    col6.metric("Book Complete", books_in_written_true, delta=f"-{total_books - books_in_written_true} not complete")
    col7.metric("ISBN Received", books_apply_isbn_true, delta=f"-{total_books - books_apply_isbn_true} not received")
    col8.metric("Printed", books_printed_true, delta=f"-{total_books - books_printed_true} not printed")
    col9.metric("Delivered", books_delivered_true, delta=f"-{total_books - books_delivered_true} not delivered")


######################################################################################
###########################----------- Spinner ----------#############################
######################################################################################


# with st.spinner('Loading Data...'):
#     time.sleep(4)



######################################################################################
####################----------- Dataframe current status -------------###################
######################################################################################

# Define conditions in a dictionary, including columns to select for each case
conditions = {
    'Formatting': {
        'by': ['Akash', 'Anush', 'Surendra', 'Rahul'],
        'status': 'Formatting Status',
        'columns': ['Book ID', 'Book Title', 'Month', 'Formatting By', 'Formatting Date', 'Writing By', 'Writing Date', 'Proofreading By', 'Proofreading Date']
    },
    'Proofreading': {
        'by': ['Umer', 'Publish Only', 'Barnali', 'Sheetal', 'Rakesh', 'Aman', 'Minakshi', 'Vaibhavi'],
        'status': 'Proofreading Status',
        'columns': ['Book ID', 'Book Title', 'Month', 'Proofreading By', 'Writing By', 'Writing Date']
    },
    'Writing': {
        'by': ['Vaibhavi', 'Vaibhav', 'Rakesh', 'Sheetal', 'Urvashi', 'Shravani', 
               'Publish Only', 'Minakshi', 'Preeti', 'Muskan', 'Bhavana', 'Aman', 
               'Sachin', 'muskan'],
        'status': 'Writing Status',
        'columns': ['Book ID', 'Book Title', 'Month', 'Writing By']
    }
}


# Extract information based on conditions, including specified columns
results = {}
for key, cond in conditions.items():
    # Filter the data and select columns, creating a copy to avoid modifying the original DataFrame
    current_data = track_sheet_data_bystart[(track_sheet_data_bystart[f'{key} By'].isin(cond['by'])) & (track_sheet_data_bystart[cond['status']] == 'FALSE')][cond['columns']].copy()
    
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
    {"emoji": "🖋️", "label": "Formatting", "count": len(results['Formatting']), "data": results['Formatting']}
]

# Display each status section with count, emoji, and data
for status in status_messages:
    st.markdown(
        f"<h4>{status['emoji']} {status['count']} Books in {status['label']} Today "
        f"<span class='status-badge'>Status: Running</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(status['data'], use_container_width=True, hide_index=True)


def writing_remaining(data):

    data['Writing By'] = data['Writing By'].fillna('Pending')
    data = data[data['Writing Status'].isin(['FALSE', pd.NA])][['Book ID', 'Book Title', 'Date','Month','Writing By']]
    writing_remaining = data['Book ID'].nunique() - len(results['Writing'])

    return data,writing_remaining

def proofread_remaining(data):

    data['Proofreading By'] = data['Proofreading By'].fillna('Pending')
    data = data[(data['Writing Status'] == 'TRUE') & (data['Proofreading Status'] == 'FALSE')][['Book ID', 'Book Title', 'Date','Month','Writing Date','Proofreading By']]
    proof_remaining = data['Book ID'].nunique() - len(results['Proofreading'])

    return data,proof_remaining


writing_remaining_data,writing_remaining_count = writing_remaining(track_sheet_data_bystart)
proofread_remaining_data,proofread_remaining_count = proofread_remaining(track_sheet_data_bystart)

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


######################################################################################
######################------------- 40 days data-------------#########################
######################################################################################

operations_sheet_data_pre = process_book_timings(operations_sheet_data, by_col = 'Date')
import datetime
today = datetime.date.today()
forty_five_days_ago = today - datetime.timedelta(days=40)

operations_sheet_data_pre['Date'] = operations_sheet_data_pre['Date'].dt.date

fortifiveday = operations_sheet_data_pre[operations_sheet_data_pre['Date'] <= forty_five_days_ago]
fortifiveday_status = fortifiveday[fortifiveday['Deliver'] == 'FALSE']

# Define the columns in processing order and their readable names
status_columns = {
    'Writing Complete': 'Writing Incomplete',
    'Proofreading Complete': 'Proofreading Incomplete',
    'Formating Complete': 'Formatting Incomplete',
    'Send Cover Page and Agreement': 'Cover/Agreement Pending',
    'Agreement Recieved': 'Agreement Pending',
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

from datetime import datetime
fortifiveday_status['Date'] = pd.to_datetime(fortifiveday_status['Date'], format="%d/%m/%Y", errors='coerce')
fortifiveday_status['Since Enrolled'] = (datetime.now() - fortifiveday_status['Date']).dt.days

fortifiveday_status = fortifiveday_status[['Book ID', 'Book Title','Date','Month','Since Enrolled','Reason For Hold','Writing End Datetime', 'Proofreading End Datetime',
    'Formatting End Datetime','Send Cover Page and Agreement', 'Agreement Recieved', 'Digital Prof','Confirmation', 'Ready to Print']]


# Display the last 45 days data section with count, emoji, and title
st.markdown(
    f"<h4>📅 {fortifiveday_status['Book ID'].nunique()} Books on hold older than 40 days"
    f"<span class='status-badge'>Status: On Hold</span></h4>", 
    unsafe_allow_html=True
)

# Prepare the reason counts data
reason_counts = fortifiveday_status['Reason For Hold'].value_counts().reset_index()
reason_counts.columns = ['Reason For Hold', 'Count']

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
    st.dataframe(fortifiveday_status, use_container_width=True, hide_index=True)

# Display the pie chart in the second column
with col2:
    st.markdown("#### 📊 Pie Chart")
    st.plotly_chart(pie_chart, use_container_width=True)



####################################################################################################
#####################-----------  Line Chart Monthly Books & Authors ----------######################
###################################################################################################


# Group by month and count unique 'Book ID's and 'Author ID's
monthly_counts = df.groupby(df['Date'].dt.month).agg({
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
        filtered_df[filtered_df['Writing'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Apply ISBN'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Cover Page'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Back Page Update'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Ready to Print'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Print'] == 'TRUE']['Book ID'].nunique(),
        filtered_df[filtered_df['Deliver'] == 'TRUE']['Book ID'].nunique()
    ],
    "FALSE": [
        filtered_df[filtered_df['Writing'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Apply ISBN'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Cover Page'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Back Page Update'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Ready to Print'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Print'] == 'FALSE']['Book ID'].nunique(),
        filtered_df[filtered_df['Deliver'] == 'FALSE']['Book ID'].nunique()
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
        filtered_df[filtered_df['Welcome Mail / Confirmation'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Author Detail'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Photo'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['ID Proof'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Send Cover Page and Agreement'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Agreement Recieved'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Digital Prof'] == 'TRUE']['Author Id'].nunique(),
        filtered_df[filtered_df['Confirmation'] == 'TRUE']['Author Id'].nunique()
    ],
    "FALSE": [
        filtered_df[filtered_df['Welcome Mail / Confirmation'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Author Detail'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Photo'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['ID Proof'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Send Cover Page and Agreement'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Agreement Recieved'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Digital Prof'] == 'FALSE']['Author Id'].nunique(),
        filtered_df[filtered_df['Confirmation'] == 'FALSE']['Author Id'].nunique()
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

# Sample data preparation (replace with your actual data)
# Monthly data for a specific month
employee_monthly = filtered_track_sheet_data_byend.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

# Full year data
employee_yearly = track_sheet_data_byend.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

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

proofreading_num = filtered_proofreading_data.groupby('Proofreading By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
proofreading_num.columns = ['Proofreader', 'Book Count']
# Formatting data
formatting_num = filtered_formatting_data.groupby('Formatting By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
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
monthly_book_counts =  df[df['Book ID'] != ''].groupby(df['Date'].dt.month)['Book ID'].nunique().reset_index()
monthly_book_counts.columns = ['Month', 'Total Books']

monthly_book_counts['Month'] = monthly_book_counts['Month'].apply(lambda x: month_order[x - 1])
monthly_book_counts['Month'] = pd.Categorical(monthly_book_counts['Month'], categories=month_order, ordered=True)

# Sort by the ordered month column
monthly_book_counts = monthly_book_counts.sort_values('Month')

# Group by month and count unique 'Book ID's
monthly_author_counts =  df[df['Author Id'] != ''].groupby(df['Date'].dt.month)['Author Id'].nunique().reset_index()
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
books_sold = filtered_df.groupby(['Publishing Consultant'])['Book ID'].nunique().reset_index(name='Books Sold').iloc[1:]

# Number of authors added by Publishing Consultant
authors_added = filtered_df.groupby(['Publishing Consultant'])['Author Id'].nunique().reset_index(name='Authors Added').iloc[1:]

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
    