import streamlit as st
import pandas as pd
from preprocessing import *
import time
import warnings
import time
from dotenv import load_dotenv
import base64
import json
import hashlib
import hmac
import time
import numpy as np  
from preprocessing import *
from datetime import datetime
warnings.simplefilter('ignore')

logo = "logo/logo_black.png"
fevicon = "logo/favicon_black.ico"
small_logo = "logo/favicon_white.ico"

st.logo(logo,
size = "large",
icon_image = small_logo
)

# Set page configuration
st.set_page_config(
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="collapsed",
    page_icon="chart_with_upwards_trend",  
     page_title="Content Dashboard",
)

# Inject CSS to remove the menu (optional)
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""

hide_sidebar_style = """
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
"""
hide_navigation_link_style = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """

st.markdown(hide_menu_style, unsafe_allow_html=True)



load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key') 

def validate_token():
    if 'token' not in st.session_state:
        params = st.query_params
        if 'token' in params:
            st.session_state.token = params['token']
        else:
            st.error("Access Denied: Login Required")
            st.stop()

    token = st.session_state.token

    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8'))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8'))

        signature = base64.urlsafe_b64decode(parts[2] + '==')
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{parts[0]}.{parts[1]}".encode(),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        if 'exp' in payload and payload['exp'] < time.time():
            raise ValueError("Token has expired")

        # Store validated user info in session_state
        st.session_state.user = payload['user']
        st.session_state.role = payload['role']

    except ValueError as e:
        st.error(f"Access Denied: {e}")
        st.stop()

validate_token()

user_role = st.session_state.get("role", "Guest")

if user_role in ['Content Writer', 'Proofreader']:
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    st.markdown(hide_navigation_link_style, unsafe_allow_html=True)


# Initialize session state for new visitors
if "visited" not in st.session_state:
    st.session_state.visited = False

# Check if the session state variable 'first_visit' is set, indicating the first visit
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True 

# Check if the user is new
if not st.session_state.visited: 
    st.cache_data.clear()  # Clear cache for new visitors
    st.session_state.visited = True  # Mark as visited

sheets = read_sheets_from_json()

######################################################################################
###########################----------- Data Loader & Spinner ----------#############################
######################################################################################

# # Create a placeholder for the status
status_placeholder = st.empty()

with status_placeholder.container():
    with st.status("Fetching Data", expanded=True) as status:
        st.write("Downloading AGPH Data...")
        operations_sheet_data = sheet_to_df(sheets['Operations'])
        st.write("Processing Data..")
        operations_sheet_data_preprocess = operations_preprocess(operations_sheet_data)
        status.update(
            label="Data Loaded!", state="complete", expanded=False)

status_placeholder.empty()
from datetime import datetime, timedelta

current_year = datetime.now().year
# Get the current month name
current_month = datetime.now().strftime("%B")
# Get the previous month name
previous_month = (datetime.now() - timedelta(days=datetime.now().day)).strftime("%B")

# Map month numbers to month names and set the order
month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
] # Adjust column widths as needed
  
operations_sheet_data_preprocess_year = operations_sheet_data_preprocess[operations_sheet_data_preprocess['Year']== current_year]
unique_months_selected_year = operations_sheet_data_preprocess_year['Month'].unique() 


selected_month = st.pills("2024", [previous_month,current_month], selection_mode="single", 
                        default =unique_months_selected_year[-1],label_visibility ='collapsed')

user_role = st.session_state.get("role", "Guest")

# Filter DataFrame based on selected month
operations_sheet_data_preprocess_month = operations_sheet_data_preprocess_year[operations_sheet_data_preprocess_year['Month']== selected_month]

# Calculate metrics based on both TRUE and FALSE values in the filtered DataFrame
total_books= len(np.array(operations_sheet_data_preprocess_month['Book ID'].unique())[np.array(operations_sheet_data_preprocess_month['Book ID'].unique()) !=''])
books_complete = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Book Complete'] == 'TRUE']['Book ID'].nunique()
books_written_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Writing Complete'] == 'TRUE']['Book ID'].nunique()


##################################################################################################################################
                #####################----------- Writing Department ----------######################
##################################################################################################################################


if user_role == 'Content Writer':
    st.caption(f"Welcome, {st.session_state.user}!")
    

    ######################################################################################
    #####################----------- Metrics of Selected Month ----------######################
    ######################################################################################


    st.subheader(f"Metrics of {selected_month}")

    with st.container():
        # Display metrics with TRUE counts in value and FALSE counts in delta
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        col1.metric("Total Books", total_books)
        col2.metric("Written", books_written_true)
        col3.metric("Remaining", total_books - books_written_true)


    ######################################################################################
    ####################----------- Current Working status dataframe -------------########
    ######################################################################################

    writing_by = operations_sheet_data_preprocess['Writing By'].unique()[pd.notna(operations_sheet_data_preprocess['Writing By'].unique())]


    # Define conditions in a dictionary, including columns to select for each case
    conditions = {
        'Writing': {
            'by': writing_by,
            'status': 'Writing Complete',
            'columns': ['Book ID', 'Book Title','Date','Since Enrolled','Writing By','Writing Start Date', 'Writing Start Time']
        }
    }

    # Extract information based on conditions, including specified columns
    results = {}
    for key, cond in conditions.items():
        # Filter the data and select columns, creating a copy to avoid modifying the original DataFrame
        current_data = operations_sheet_data_preprocess[(operations_sheet_data_preprocess[f'{key} By'].isin(cond['by'])) & 
                                                        (operations_sheet_data_preprocess[cond['status']] == 'FALSE')
                                                        ][cond['columns']].copy()
        
        # Format 'Date' columns in the copy to remove the time part
        date_columns = [col for col in current_data.columns if 'Date' in col]
        for date_col in date_columns:
            current_data[date_col] = pd.to_datetime(current_data[date_col]).dt.strftime('%d %B %Y')
        
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
        {"emoji": "✍️", "label": "Writing", "count": len(results['Writing']), "data": results['Writing']}
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
    ###############----------- Work done Books on Previous day & Today -------------################
    ######################################################################################

    work_done_status = work_done_status(operations_sheet_data_preprocess)

    work_done_status = work_done_status[['Book ID', 'Book Title', 'Date','Writing By',
                                    'Writing Start Date', 'Writing Start Time',
                                'Writing End Date', 'Writing End Time', 'Writing Complete', 'Work Done']]

    work_done_status = work_done_status[work_done_status['Work Done'] == 'Writing']
    # Display the last 45 days data section with count, emoji, and title
    st.markdown(
        f"<h5>✅ Work done on {work_done_status['Book ID'].nunique()} Books on Previous day & Today"
        f"<span class='status-badge'>Status: Done!</span></h5>", 
        unsafe_allow_html=True)

    st.dataframe(work_done_status, use_container_width=True, hide_index=True, column_config = {
            "Writing Complete": st.column_config.CheckboxColumn(
                "Writing Complete",
                default=False,
            )
        })


    ######################################################################################
    ###############----------- Work Remaining status dataframe -------------################
    ######################################################################################


    def writing_remaining(data):

        data['Writing By'] = data['Writing By'].fillna('Pending')
        data = data[data['Writing Complete'].isin(['FALSE', pd.NA])][['Book ID', 'Book Title', 
                                                                    'Date','Since Enrolled','Writing By']]
        writing_remaining = data['Book ID'].nunique() - len(results['Writing'])

        date_columns = [col for col in data.columns if 'Date' in col]
        for col in date_columns:
            data[col] = data[col].dt.strftime('%d %B %Y')

        return data,writing_remaining


    writing_remaining_data,writing_remaining_count = writing_remaining(operations_sheet_data_preprocess)

    st.markdown(
        f"<h5>✍️ {writing_remaining_count} Books Writing Remaining "
        f"<span class='status-badge-red'>Status: Remaining</span></h4>", 
        unsafe_allow_html=True
    )
    st.dataframe(writing_remaining_data, use_container_width=True, hide_index=True)



    ####################################################################################################
    ################-----------  Writing complete in this Month ----------##############
    ####################################################################################################


    writing_complete_data_by_month, writing_complete_data_by_month_count = writing_complete(operations_sheet_data_preprocess,current_year,
                                                                                            selected_month)
    
    writing_complete_data_by_month = writing_complete_data_by_month[['Book ID', 'Book Title','Date','Since Enrolled',
                                                   'Writing By', 'Writing Start Date', 'Writing Start Time', 'Writing End Date', 'Writing End Time']]
    # Monthly data for a specific month
    operations_sheet_data_preprocess_writng_month = operations_sheet_data_preprocess[
        (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(current_year)) & 
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


    #######################################################################################################
    ###################------------- Horizonrtal bar graph Employee Performance----------##################
    #######################################################################################################

    # Monthly data for a specific month
    operations_sheet_data_preprocess_writng_month = operations_sheet_data_preprocess[
        (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(current_year)) & 
        (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%B') == str(selected_month))
    ]
    employee_monthly = operations_sheet_data_preprocess_writng_month.groupby('Writing By').count()['Book ID'].reset_index().sort_values(by='Book ID', ascending=True)

    # Full year data
    operations_sheet_data_preprocess_writng_year = operations_sheet_data_preprocess[
        (operations_sheet_data_preprocess['Writing End Date'].dt.strftime('%Y') == str(current_year))
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
        title=f'Books Written by Content Team in {selected_month} {current_year}',
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
        title=f'Total Books Written by Content Team in {current_year}',
        width=300,
        height=400
    )

    # Display charts side by side in Streamlit
    st.subheader(f"📝 Content Team Performance in {current_year}")
    #st.caption("Content Team performance in each month and in 2024")
    col1, col2 = st.columns(2)

    with col1:
        st.altair_chart(monthly_chart, use_container_width=True)

    with col2:
        st.altair_chart(yearly_chart, use_container_width=True)
    
    if st.session_state.first_visit:
        st.balloons()
        st.session_state.first_visit = False




##################################################################################################################################
                #####################----------- Proofreading Department ----------######################
##################################################################################################################################




if user_role == 'Proofreader':
    st.caption(f"Welcome, {st.session_state.user}!")

    st.subheader(f"Metrics of {selected_month}")

    books_proofread_true = operations_sheet_data_preprocess_month[operations_sheet_data_preprocess_month['Proofreading Complete'] == 'TRUE']['Book ID'].nunique()
    

    with st.container():
        # Display metrics with TRUE counts in value and FALSE counts in delta
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        col1.metric("Total Books", total_books)
        col2.metric("Written", books_written_true)
        col3.metric("Written Remaining", total_books - books_written_true)
        col4.metric("Proofread", books_proofread_true)
        col5.metric("Proofread Remaining", books_written_true - books_proofread_true)



    ######################################################################################
    ####################----------- Current Working status dataframe -------------########
    ######################################################################################

    proofreading_by = operations_sheet_data_preprocess['Proofreading By'].unique()[pd.notna(operations_sheet_data_preprocess['Proofreading By'].unique())]


    # Define conditions in a dictionary, including columns to select for each case
    conditions = {
       
        'Proofreading': {
            'by': proofreading_by,
            'status': 'Proofreading Complete',
            'columns': ['Book ID', 'Book Title','Date','Since Enrolled', 'Proofreading By','Proofreading Start Date', 
                        'Proofreading Start Time', 'Writing By','Writing End Date','Writing End Time']
        }
    }
       

    # Extract information based on conditions, including specified columns
    results = {}
    for key, cond in conditions.items():
        # Filter the data and select columns, creating a copy to avoid modifying the original DataFrame
        current_data = operations_sheet_data_preprocess[(operations_sheet_data_preprocess[f'{key} By'].isin(cond['by'])) & 
                                                        (operations_sheet_data_preprocess[cond['status']] == 'FALSE')
                                                        ][cond['columns']].copy()
        
        # Format 'Date' columns in the copy to remove the time part
        date_columns = [col for col in current_data.columns if 'Date' in col]
        for date_col in date_columns:
            current_data[date_col] = pd.to_datetime(current_data[date_col]).dt.strftime('%d %B %Y')
        
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
        {"emoji": "📖", "label": "Proofreading", "count": len(results['Proofreading']), "data": results['Proofreading']},
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
    ###############----------- Work done Books on Previous day & Today -------------################
    ######################################################################################

    work_done_status = work_done_status(operations_sheet_data_preprocess)

    work_done_status = work_done_status[['Book ID', 'Book Title', 'Date','Proofreading By',
                               'Proofreading Start Date', 'Proofreading Start Time', 'Proofreading End Date',
                               'Proofreading End Time','Proofreading Complete','Work Done']]
    
    work_done_status = work_done_status[work_done_status['Work Done'] == 'Proofreading']

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


    def proofread_remaining(data):

        data['Proofreading By'] = data['Proofreading By'].fillna('Pending')
        data = data[(data['Writing Complete'] == 'TRUE') & (data['Proofreading Complete'] == 'FALSE')][['Book ID', 'Book Title', 
                                                                                                        'Date','Since Enrolled',
                                                                                                        'Writing By', 
                                                                                                        'Writing End Date',
                                                                                                        'Writing End Time','Proofreading By']]
        proof_remaining = data['Book ID'].nunique() - len(results['Proofreading'])

        date_columns = [col for col in data.columns if 'Date' in col]
        for col in date_columns:
            data[col] = data[col].dt.strftime('%d %B %Y')

        return data,proof_remaining

    proofread_remaining_data,proofread_remaining_count = proofread_remaining(operations_sheet_data_preprocess)


    st.markdown(
        f"<h5>📖 {proofread_remaining_count} Books Proofreading Remaining "
        f"<span class='status-badge-red'>Status: Remaining</span></h5>", 
        unsafe_allow_html=True
    )
    st.dataframe(proofread_remaining_data, use_container_width=True, hide_index=True)


    ####################################################################################################
    ################-----------  Proofreading complete in this Month ----------##############
    ####################################################################################################

    proofreading_complete_data_by_month, proofreading_complete_data_by_month_count = proofreading_complete(operations_sheet_data_preprocess,current_year, 
                                                                                                        selected_month)
    
    proofreading_complete_data_by_month  = proofreading_complete_data_by_month[['Book ID', 'Book Title','Date',
                                                   'Writing By', 'Proofreading By', 'Proofreading Start Date', 'Proofreading Start Time', 'Proofreading End Date',
                                                   'Proofreading End Time']]


    operations_sheet_data_preprocess_proof_month = operations_sheet_data_preprocess[
        (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%Y') == str(current_year)) & 
        (operations_sheet_data_preprocess['Proofreading End Date'].dt.strftime('%B') == str(selected_month))
    ]
    proofreading_num = operations_sheet_data_preprocess_proof_month.groupby('Proofreading By')['Book ID'].count().reset_index().sort_values(by='Book ID', ascending=False)
    proofreading_num.columns = ['Proofreader', 'Book Count']
    cleaned_proofreading_num = proofreading_num[['Proofreader', 'Book Count']]

    # Create the horizontal bar chart for Proofreading
    proofreading_bar = alt.Chart(proofreading_num).mark_bar().encode(
        y=alt.Y('Proofreader', sort='-x', title='Proofreader'),  # Change x to y for horizontal bars
        x=alt.X('Book Count', title='Book Count'),  # Change y to x for horizontal bars
        color=alt.Color('Proofreader', scale=alt.Scale(scheme='darkgreen'), legend=None),
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

    if st.session_state.first_visit:
        st.balloons()
        st.session_state.first_visit = False