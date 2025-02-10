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
from datetime import datetime
warnings.simplefilter('ignore')

# Set page configuration
st.set_page_config(
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="collapsed",
    page_icon="chart_with_upwards_trend",  
     page_title="IJISEM Dashboard",
)

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key') 

def validate_token():
    # Store token in session_state if it is found in URL parameters
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

if user_role != "Admin":    
    st.error("Access Denied: Admin Role Required")
    st.stop()

# Initialize session state for new visitors
if "visited" not in st.session_state:
    st.session_state.visited = False

# Check if the user is new
if not st.session_state.visited:
    st.toast("Please Wait New Data is being fetched...", icon="ℹ️")  # Notify user
    st.cache_data.clear()  # Clear cache for new visitors
    st.session_state.visited = True  # Mark as visited

sheets = read_sheets_from_json()

with st.spinner('Loading Data...'):
    ijisem_sheet_data = sheet_to_df(sheets['IJISEM'])
    ijisem_sheet_data_preprocess = ijisem_preprocess(ijisem_sheet_data)
    time.sleep(1)


month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]


unique_year = ijisem_sheet_data_preprocess['Year'].unique()[~np.isnan(ijisem_sheet_data_preprocess['Year'].unique())]
unique_year = unique_year.astype(int)

col1, col2 = st.columns([2, 8])  # Adjust column widths as needed

with col1:
    selected_year = st.pills("2024", unique_year, selection_mode="single", 
                            default =unique_year[-1],label_visibility ='collapsed')

ijisem_sheet_data_preprocess_year = ijisem_sheet_data_preprocess[ijisem_sheet_data_preprocess['Year']== selected_year]
unique_months = ijisem_sheet_data_preprocess_year['Month'].unique()
unique_months_sorted = sorted(unique_months, key=lambda x: datetime.strptime(x, "%B"))

with col2:
    selected_month = st.pills("2024", unique_months_sorted, selection_mode="single", 
                            default =unique_months_sorted[-1],label_visibility ='collapsed')

ijisem_sheet_data_preprocess_filter = ijisem_sheet_data_preprocess[
    (ijisem_sheet_data_preprocess['Receiving Date'].dt.year == selected_year) & 
    (ijisem_sheet_data_preprocess['Receiving Date'].dt.strftime('%B') == selected_month)
]

ijisem_sheet_data_preprocess_filter_year = ijisem_sheet_data_preprocess[ijisem_sheet_data_preprocess['Receiving Date'].dt.year == selected_year]

st.subheader(f"Metrics of {selected_month} {selected_year}")

total_papers_year = ijisem_sheet_data_preprocess_filter_year['Paper ID'].nunique()
total_papers_month = ijisem_sheet_data_preprocess_filter['Paper ID'].nunique()
paper_upload = ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Paper Upload'] == 'TRUE']['Paper ID'].nunique()
review_process = ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Review Process'] == 'TRUE']['Paper ID'].nunique()
acceptence = ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Acceptance'] == 'TRUE']['Paper ID'].nunique()
formating = ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Formatting'] == 'TRUE']['Paper ID'].nunique()
ijisem_sheet_data_preprocess_filter['Pyment_status']  = ijisem_sheet_data_preprocess_filter["Payment"].apply(lambda x: check_number_or_string(x) if pd.notnull(x) else False)
payment_status = ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Pyment_status'] == True]['Paper ID'].nunique()
unique_volume = ijisem_sheet_data_preprocess_filter['Volume'].unique()
unique_issue = ijisem_sheet_data_preprocess_filter['Issue'].unique()

with st.container():
    # Display metrics with TRUE counts in value and FALSE counts in delta
    col1, col2, col3, col4, col5, col6 = st.columns(6,border=True)
    #col1.metric(f"Total Papers in {selected_year}", total_papers_year)
    col1.metric(f"Papers in {selected_month}", total_papers_month, delta=f"{total_papers_year} Papers in {selected_year}")
    col2.metric("Published", paper_upload, delta=f"-{total_papers_month - paper_upload} Remaining")
    col3.metric("Review Done", review_process, delta=f"-{total_papers_month - review_process} Remaining")
    col4.metric("Paper Accepted", acceptence, delta=f"-{total_papers_month - acceptence} Remaining")
    col5.metric("Formatting", formating, delta=f"-{total_papers_month - formating} not complete")
    col6.metric("Pyment Received", payment_status, delta=f"-{total_papers_month - payment_status} not received")


with st.expander("View papers", expanded=False,icon='🔍'):
    tab1, tab2 = st.tabs([f"{total_papers_month} Papers in {selected_month}", f"{paper_upload} Papers Published in {selected_month}"])
    
    with tab1:
        st.dataframe(ijisem_sheet_data_preprocess_filter, use_container_width=True, hide_index=True)
    
    with tab2:
        st.dataframe(ijisem_sheet_data_preprocess_filter[ijisem_sheet_data_preprocess_filter['Paper Upload'] == 'TRUE'], use_container_width=True, hide_index=True)

####################################################################################################
#####################-----------  Search Papers ----------######################
###################################################################################################

# Remove null values from unique options
unique_volume = ijisem_sheet_data_preprocess['Volume'].dropna().unique()
unique_issue = ijisem_sheet_data_preprocess['Issue'].dropna().unique()

st.subheader("Search Paper")
with st.container():

    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        query_1 = st.selectbox("Select Volume", unique_volume, index=None, placeholder='Select Volume')

    with col2:
        query_2 = st.selectbox("Select Issue", unique_issue, index=None, placeholder='Select Issue')

if query_1 is not None and query_2 is not None:
    # Perform filtering
    search_result = ijisem_sheet_data_preprocess[
        (ijisem_sheet_data_preprocess['Volume'] == int(query_1)) &
        (
            (ijisem_sheet_data_preprocess['Issue'] == str(query_2)) |
            (ijisem_sheet_data_preprocess['Issue'] == int(query_2) if isinstance(query_2, int) else False)
        )
    ]

    if not search_result.empty:
        st.success(f"Found {search_result['Paper ID'].nunique()} Papers")
        st.dataframe(search_result, use_container_width=False, hide_index=True)
    else:
        st.warning("No results found. Please try different inputs.")
else:
    st.info("Please fill in both fields to search.")

####################################################################################################
#####################-----------  Line Chart Monthly Books & Authors ----------#####################
###################################################################################################


monthly_counts = ijisem_sheet_data_preprocess_year.groupby(ijisem_sheet_data_preprocess_year['Receiving Date'].dt.month).agg({
    'Paper ID': 'nunique',
}).reset_index()

# Rename columns for clarity
monthly_counts['Month'] = monthly_counts['Receiving Date'].apply(lambda x: pd.to_datetime(f"2024-{x}-01").strftime('%B'))

monthly_counts = monthly_counts.rename(columns={'Paper ID': 'Total Paper'})

line_chart = alt.Chart(monthly_counts).mark_line(point=True).encode(
    x=alt.X('Month', title='Month', sort = month_order),
    y=alt.Y('Total Paper', title='Total Count'),
    color=alt.value("#5499de")  # Color for Total Books line
).properties(
    width=600,
    height=400
)

# Add text labels on data points
total_papers_charts = line_chart.mark_text(
    align='center',
    baseline='bottom',
    dy=-10
).encode(
    text='Total Paper:Q'
)

st.subheader(f"Total Papers in {selected_year}")
st.caption("Total Papers each month")
st.altair_chart((line_chart + total_papers_charts), use_container_width=True)



    