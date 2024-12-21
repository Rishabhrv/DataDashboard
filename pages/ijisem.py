import streamlit as st
import pandas as pd
from preprocessing import *
import time
import warnings
warnings.simplefilter('ignore')

# Set page configuration
st.set_page_config(
    layout="wide",  # Set layout to wide mode
    initial_sidebar_state="collapsed",
    page_icon="chart_with_upwards_trend",  
     page_title="IJISEM Dashboard",
)

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

unique_months = ijisem_sheet_data_preprocess['Month'].unique()
unique_year = ijisem_sheet_data_preprocess['Year'].unique()

from datetime import datetime
unique_months_sorted = sorted(unique_months, key=lambda x: datetime.strptime(x, "%B"))


selected_year = st.pills("2024", unique_year, selection_mode="single", 
                            default =unique_year[-1],label_visibility ='collapsed')
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
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7,border=True)
    col1.metric(f"Total Papers in {selected_year}", total_papers_year)
    col2.metric(f"Papers in {selected_month}", total_papers_month)
    col3.metric("Published", paper_upload, delta=f"-{total_papers_month - paper_upload} Remaining")
    col4.metric("Review Done", review_process, delta=f"-{total_papers_month - review_process} Remaining")
    col5.metric("Paper Accepted", acceptence, delta=f"-{total_papers_month - acceptence} Remaining")
    col6.metric("Formatting", formating, delta=f"-{total_papers_month - formating} not complete")
    col7.metric("Pyment Received", payment_status, delta=f"-{total_papers_month - payment_status} not received")

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





    