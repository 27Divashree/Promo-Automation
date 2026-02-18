import streamlit as st
import json
import glob
import importlib
import os
from excel_handler import ExcelManager

st.set_page_config(page_title="Promo Analysis Gen", layout="wide")
@st.cache_data
def load_configs():
    configs = {}
    for filepath in glob.glob("configs/*.json"):
        with open(filepath, 'r') as f:
            data = json.load(f)
            configs[data['display_name']] = data
    return configs

# Start at Step 1 to keep numbers clean
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'configs' not in st.session_state:
    st.session_state.configs = load_configs()

# ==========================================
# Dynamic App Header
# ==========================================
if st.session_state.step > 1 and st.session_state.get('promo_name'):
    st.title(f"📊 {st.session_state.promo_name} - Promotion Analysis Generator")
else:
    st.title("📊 Promotion Analysis Generator")

# ==========================================
# Step 1: Setup & Config Selection
# ==========================================
if st.session_state.step == 1:
    st.header("Step 1: Setup")
    
    if not st.session_state.configs:
        st.error("No configuration files found in 'configs' folder!")
        st.stop()
        
    template_options = list(st.session_state.configs.keys())
    st.session_state.template_choice = st.selectbox("Choose Excel Template Profile", template_options)
    st.session_state.promo_name = st.text_input("Enter Promotion Name")
    
    if st.button("Proceed", type="primary"):
        if st.session_state.promo_name:
            config = st.session_state.configs[st.session_state.template_choice]
            handler_name = config.get("handler_module")
            
            excel_path = os.path.join("templates", config['template_file'])
            
            try:
                module = importlib.import_module(f"handlers.{handler_name}")
                st.session_state.template_handler = module.Handler() 
                st.session_state.excel_mgr = ExcelManager(excel_path)
                st.session_state.step = 2 # Go to Step 2
                st.rerun()
            except ModuleNotFoundError:
                st.error(f"Could not find handler file: 'handlers/{handler_name}.py'")
            except FileNotFoundError:
                st.error(f"Could not find Excel template: '{excel_path}'. Did you put it in the templates folder?")
        else:
            st.error("Please provide a promotion name.")
    # ==========================================
    # Step 2: Base Sheet & Tab Naming
    # ==========================================
    elif st.session_state.step == 2:
        st.header("Step 2: Base Sheet & Tab Naming")
        mgr = st.session_state.excel_mgr
        config = st.session_state.configs[st.session_state.template_choice]
        
        # --- NEW: Restrict Base Sheet Choices ---
        default_base = config['sheets']['base_analysis']
        actual_sheets = mgr.get_sheet_names()
        
        # Look for allowed sheets in config, fallback to default_base if missing
        allowed_sheets = config['sheets'].get('allowed_base_sheets', [default_base])
        
        # Filter out any allowed sheets that don't actually exist in the workbook
        valid_choices = [s for s in allowed_sheets if s in actual_sheets]
        
        if not valid_choices:
            st.error("Error: None of the allowed base sheets exist in the uploaded template!")
            st.stop()
            
        st.session_state.base_sheet = st.selectbox("Choose Base Sheet", valid_choices)
        
        # --- Tab Naming ---
        st.divider()
        st.subheader("Name Your New Tab")
        
        prefix = f"{st.session_state.promo_name}_small_scale_"
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
            # We put a finalize button here so we don't delete the Base sheet prematurely!
            if st.button("🚀 Finalize & Generate File", type="primary"):
                st.session_state.step = "finalize"
                st.rerun()

    # ==========================================
    # NEW: Finalize Step (Deletes Base Sheets)
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