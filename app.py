import streamlit as st
import json
import glob
import importlib
import os
from excel_handler import ExcelManager

st.set_page_config(page_title="Promo Analysis Gen", layout="wide")

# ==========================================
# OPTIMIZATION: Cache Data
# ==========================================
@st.cache_data
def load_configs():
    """Reads JSON configs from disk ONCE and caches them in memory."""
    configs = {}
    # Ensure you have a folder named 'configs' in the same directory as this script
    for filepath in glob.glob("configs/*.json"):
        with open(filepath, 'r') as f:
            data = json.load(f)
            configs[data['display_name']] = data
    return configs

# Initialize session state variables
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'configs' not in st.session_state:
    st.session_state.configs = load_configs()

# ==========================================
# Step 1: Promotion Setup
# ==========================================
if st.session_state.step == 1:
    st.header("Step 1: Promotion Setup")
    
    # Check if configs loaded properly
    if not st.session_state.configs:
        st.error("No configuration files found! Please ensure you have a 'configs/' folder with your JSON files.")
        st.stop()
        
    promo_name = st.text_input("Enter Promotion Name:")
    template_choice = st.selectbox("Select Template:", list(st.session_state.configs.keys()))
    
    if st.button("Proceed to Setup", type="primary"):
        if not promo_name:
            st.warning("Please enter a promotion name first.")
        else:
            try:
                # 1. Save basics
                st.session_state.promo_name = promo_name
                st.session_state.template_choice = template_choice
                config = st.session_state.configs[template_choice]
                
                # 2. Initialize Excel Manager
                template_path = config['template_file'] 
                st.session_state.excel_mgr = ExcelManager(template_path)
                
                # 3. Dynamically load the handler
                # Make sure your JSON has a "handler" key (e.g., "handler": "small_scale_recap")
                handler_module_name = config.get('handler', 'small_scale_recap') 
                module = importlib.import_module(f"handlers.{handler_module_name}")
                st.session_state.template_handler = module.Handler()
                
                # 4. Move to Step 2
                st.session_state.step = 1.5
                st.rerun()
                
            except FileNotFoundError:
                st.error(f"❌ Could not find the Excel template file: '{config.get('template_file')}'")
                st.info("Make sure the file name in your JSON exactly matches the actual Excel file in your folder.")
            except ImportError as e:
                st.error(f"❌ Could not find the handler file: {e}")
                st.info(f"Make sure you have a file named 'handlers/{config.get('handler', 'small_scale_recap')}.py'")
            except SyntaxError as e:
                st.error(f"❌ There is a syntax error in your python files: {e}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {e}")

# ==========================================
# Step 1.5: Select Request Form data if available
# ==========================================
elif st.session_state.step == 1.5:
    st.header("Step 1.5: Data Input Preference")
    method = st.radio(
        "Do you have a Request Form for this promotion?",
        ["Yes - Upload and Auto-extract", "No - I will enter details manually"]
    )
    
    if method == "Yes - Upload and Auto-extract":
        req_file = st.file_uploader("Upload Excel Request Form", type=['xlsx'])
        if req_file:
            if st.button("Process & Continue"):
                import openpyxl
                import pandas as pd
                # Extract from C13, C14, etc.
                rb = openpyxl.load_workbook(req_file, data_only=True)
                rs = rb.active
                
                def get_val(cell):
                    val = rs[cell].value
                    return val.date() if hasattr(val, 'date') else val

                st.session_state.extracted = {
                    "ty_qs": get_val("C13"), "ty_qe": get_val("C14"),
                    "ty_rs": get_val("C19"), "ty_re": get_val("C20"),
                    "ly_qs": get_val("C19"), "ly_qe": get_val("C20"), # Per your instruction ly is mapped from these
                    "ly_rs": get_val("C26"), "ly_re": get_val("C27"),
                    "q_amt": rs["C21"].value,
                    "r_amt": rs["C22"].value
                }
                # Save the Request Form to a new tab named "Request Form"
                df_req = pd.read_excel(req_file)
                st.session_state.excel_mgr.add_raw_sheet("Request Form", df_req)
                
                st.session_state.step = 2
                st.rerun()
    else:
        if st.button("Continue to Manual Entry"):
            st.session_state.extracted = {} # Clear extracted data
            st.session_state.step = 2
            st.rerun()
# ==========================================
# Step 2: Base Sheet & Tab Naming
# ==========================================
elif st.session_state.step == 2:
    st.header("Step 2: Base Sheet & Tab Naming")
    mgr = st.session_state.excel_mgr
    config = st.session_state.configs[st.session_state.template_choice]
    
    # --- Restrict Base Sheet Choices ---
    default_base = config['sheets']['base_analysis']
    actual_sheets = mgr.get_sheet_names()
    
    # Look for allowed sheets in config, fallback to default_base if missing
    allowed_sheets = config['sheets'].get('allowed_base_sheets', [default_base])
    
    # Filter out any allowed sheets that don't actually exist in the workbook
    valid_choices = [s for s in allowed_sheets if s in actual_sheets]
    
    if not valid_choices:
        st.error("❌ Error: None of the allowed base sheets exist in the uploaded Excel template!")
        st.write(f"Allowed sheets from JSON: {allowed_sheets}")
        st.write(f"Actual sheets in Excel: {actual_sheets}")
        st.stop()
        
    st.session_state.base_sheet = st.selectbox("Choose Base Sheet", valid_choices)
    
    # --- Tab Naming ---
    st.divider()
    st.subheader("Name Your New Tab")
    
    prefix = f"{st.session_state.promo_name}_"
    st.caption(f"**Prefix:** `{prefix}`")
    user_suffix = st.text_input("Enter the rest of the tab name:", value="Qual")
    
    if st.button("Proceed to Inputs"):
        st.session_state.current_tab = f"{prefix}{user_suffix}"
        st.session_state.step = 3 
        st.rerun()

# ==========================================
# Steps 3, 4, 5: Delegated to handlers
# ==========================================
elif st.session_state.step == 3:
    st.session_state.template_handler.render_step_3(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

elif st.session_state.step == 4:
    st.session_state.template_handler.render_step_4(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

elif st.session_state.step == 5:
    st.session_state.template_handler.render_step_5(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

# ==========================================
# Step 6: Loop or Finalize
# ==========================================
elif st.session_state.step == 6:
    st.success(f"Sheet '{st.session_state.get('current_tab', 'Analysis')}' completed successfully!")
    st.info("You can either append another promotion tab to this workbook, or finalize it for download.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Another Tab (Keep going)"):
            st.session_state.step = 2 
            st.rerun()
            
    with col2:
        if st.button("🚀 Finalize & Generate File", type="primary"):
            st.session_state.step = "finalize"
            st.rerun()

# ==========================================
# Finalize Step: Cleanup & Download
# ==========================================
elif st.session_state.step == "finalize":
    config = st.session_state.configs[st.session_state.template_choice]
    
    # 1. Delete the unwanted background sheets
    sheets_to_remove = config['sheets'].get('remove_on_export', [])
    st.session_state.excel_mgr.remove_unwanted_sheets(sheets_to_remove)
    
    # 2. Generate the bytes for the newly cleaned workbook
    output_bytes = st.session_state.excel_mgr.get_download_bytes()
    file_name = f"{st.session_state.promo_name}_Analysis.xlsx"
    
    st.success("✨ Junk sheets removed! Your workbook is clean and ready.")
    
    st.download_button(
        label="⬇️ Download Final Workbook", 
        data=output_bytes, 
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        on_click=lambda: st.session_state.update(step=7)
    )

# ==========================================
# Step 7: Reset
# ==========================================
elif st.session_state.step == 7:
    st.success("Workbook downloaded successfully!")
    st.balloons()
    
    if st.button("Start New Promotion completely"):
        st.session_state.clear() 
        st.rerun()