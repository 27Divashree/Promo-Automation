import streamlit as st
import json
import glob
import importlib
import os
from excel_handler import ExcelManager

st.set_page_config(page_title="Promo Analysis Gen", layout="wide")

def load_configs():
    configs = {}
    for filepath in glob.glob("configs/*.json"):
        with open(filepath, 'r') as f:
            data = json.load(f)
            configs[data['display_name']] = data
    return configs

if 'step' not in st.session_state:
    st.session_state.step = 0
if 'configs' not in st.session_state:
    st.session_state.configs = load_configs()

st.title("Promotion Analysis Generator")

# ==========================================
# APP LEVEL: Setup & Config Selection
# ==========================================
if st.session_state.step == 0:
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
            
            # LOOK IN THE 'templates/' FOLDER
            excel_path = os.path.join("templates", config['template_file'])
            
            try:
                module = importlib.import_module(f"handlers.{handler_name}")
                st.session_state.template_handler = module.Handler() 
                st.session_state.excel_mgr = ExcelManager(excel_path)
                st.session_state.step = 1
                st.rerun()
            except ModuleNotFoundError:
                st.error(f"Could not find handler file: 'handlers/{handler_name}.py'")
            except FileNotFoundError:
                st.error(f"Could not find Excel template: '{excel_path}'. Did you put it in the templates folder?")
        else:
            st.error("Please provide a promotion name.")

# ==========================================
# APP LEVEL: Base Sheet Selection
# ==========================================
elif st.session_state.step == 1:
    st.header("Step 2: Base Sheet")
    mgr = st.session_state.excel_mgr
    config = st.session_state.configs[st.session_state.template_choice]
    
    default_base = config['sheets']['base_analysis']
    sheets = mgr.get_sheet_names()
    default_idx = sheets.index(default_base) if default_base in sheets else 0
    
    st.session_state.base_sheet = st.selectbox("Choose Base Sheet", sheets, index=default_idx)
    
    if st.button("Proceed to Inputs"):
        st.session_state.step = 1.5
        st.rerun()

# ==========================================
# HANDLER LEVEL: Delegated to handlers/*.py
# ==========================================
elif st.session_state.step == 1.5:
    st.session_state.template_handler.render_step_3(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

elif st.session_state.step == 2:
    st.session_state.template_handler.render_step_4(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

elif st.session_state.step == 3:
    st.session_state.template_handler.render_step_5(st.session_state.excel_mgr, st.session_state.configs[st.session_state.template_choice])

# ==========================================
# APP LEVEL: Actions & Download
# ==========================================
elif st.session_state.step == 4:
    st.success(f"Sheet '{st.session_state.current_tab}' completed successfully!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add More Tabs (Another Base Sheet)"):
            st.session_state.step = 1
            st.rerun()
            
    with col2:
        output_bytes = st.session_state.excel_mgr.get_download_bytes()
        file_name = f"{st.session_state.promo_name}_Analysis.xlsx"
        
        st.download_button("Generate & Download Workbook", data=output_bytes, file_name=file_name,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           on_click=lambda: st.session_state.update(step=5))

# ==========================================
# APP LEVEL: Reset
# ==========================================
elif st.session_state.step == 5:
    st.success("Workbook generated successfully!")
    st.balloons()
    
    if st.button("Start New Promotion completely"):
        st.session_state.clear() 
        st.rerun()