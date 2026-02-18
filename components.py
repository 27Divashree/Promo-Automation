import streamlit as st
import pandas as pd
import datetime

def render_date_inputs():
    """Renders the standard TY/LY date inputs and returns a dictionary of the selected dates."""
    st.subheader("Dates")
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.date.today()
        ty_q_start = st.date_input("TY Qualify Start", value=today)
        ty_q_end = st.date_input("TY Qualify End", value=today + datetime.timedelta(days=14))
        ty_r_start = st.date_input("TY Redeem Start", value=today + datetime.timedelta(days=15))
        ty_r_end = st.date_input("TY Redeem End", value=today + datetime.timedelta(days=29))
    with col2:
        ly_q_start = st.date_input("LY Qualify Start", value=ty_q_start - datetime.timedelta(days=364))
        ly_q_end = st.date_input("LY Qualify End", value=ty_q_end - datetime.timedelta(days=364))
        ly_r_start = st.date_input("LY Redeem Start", value=ty_r_start - datetime.timedelta(days=364))
        ly_r_end = st.date_input("LY Redeem End", value=ty_r_end - datetime.timedelta(days=364))
        
    return {
        "ty_q_start": ty_q_start, "ty_q_end": ty_q_end,
        "ty_r_start": ty_r_start, "ty_r_end": ty_r_end,
        "ly_q_start": ly_q_start, "ly_q_end": ly_q_end,
        "ly_r_start": ly_r_start, "ly_r_end": ly_r_end
    }

def render_article_upload():
    """Renders the file uploader and dynamic sheet selector. Returns the file and sheet name."""
    st.subheader("Article List Upload")
    uploaded_file = st.file_uploader("Upload Article CSV/Excel", type=['csv', 'xlsx', 'xls'])
    
    selected_article_sheet = 0 # Default fallback
    if uploaded_file and uploaded_file.name.endswith(('xlsx', 'xls')):
        uploaded_file.seek(0)
        xls = pd.ExcelFile(uploaded_file,engine='calamine')
        
        if len(xls.sheet_names) > 1:
            selected_article_sheet = st.radio(
                "📌 Select which tab to use from the uploaded file:", 
                xls.sheet_names
            )
        else:
            selected_article_sheet = xls.sheet_names[0]
            st.success(f"✅ File uploaded! Using the only available tab: `{selected_article_sheet}`")
            
    return uploaded_file, selected_article_sheet

def render_persistent_header():
    """Renders the current working tab at the top of the screen."""
    if 'current_tab' in st.session_state:
        st.info(f"📁 **Currently Working On:** `{st.session_state.current_tab}`")