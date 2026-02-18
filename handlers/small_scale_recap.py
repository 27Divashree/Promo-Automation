import streamlit as st
import pandas as pd
import re
# Import our new reusable components!
from components import render_date_inputs, render_article_upload, render_persistent_header

class Handler:
    """Handles the UI and logic for the Small Scale Recap Template"""

    def render_step_3(self, mgr, config):
        render_persistent_header()
        st.header("Step 3: Configuration & Inputs")
        st.divider()
        
        # 1. Call Reusable Date Component
        dates = render_date_inputs()
        st.divider()
        
        # 2. Call Reusable Upload Component
        uploaded_file, selected_article_sheet = render_article_upload()
        st.divider()
        
        # 3. Handler-Specific Inputs (Amounts might vary per template, so we keep them here)
        st.subheader("Qualification/Redemption Amounts")
        p4_val = st.number_input("Qualification Amount (P4)", value=0.0)
        q4_val = st.number_input("Redemption Amount (Q4)", value=0.0)
        st.divider()
        
        if st.button("Generate SQL & Create Tab", type="primary"):
            
            # Format dates to mm/dd/yyyy and save to session state
            fmt = '%m/%d/%Y'
            st.session_state.update({
                "ty_q_start": dates['ty_q_start'].strftime(fmt), 
                "ty_q_end": dates['ty_q_end'].strftime(fmt),
                "ty_r_start": dates['ty_r_start'].strftime(fmt), 
                "ty_r_end": dates['ty_r_end'].strftime(fmt),
                "ly_q_start": dates['ly_q_start'].strftime(fmt), 
                "ly_q_end": dates['ly_q_end'].strftime(fmt),
                "ly_r_start": dates['ly_r_start'].strftime(fmt), 
                "ly_r_end": dates['ly_r_end'].strftime(fmt),
                "p4_val": p4_val,
                "q4_val": q4_val,
                "sql_article_tuple": "()" # Default fallback
            })
            
            # Handle Article List processing
            if uploaded_file:
                uploaded_file.seek(0) 
                
                if uploaded_file.name.endswith('csv'):
                    df = pd.read_csv(uploaded_file, header=None)
                else:
                    df = pd.read_excel(uploaded_file, sheet_name=selected_article_sheet, header=None)
                
                if df.shape[1] >= 6:
                    f1_raw = df.iloc[0, 5]
                    if pd.notna(f1_raw):
                        st.session_state.sql_article_tuple = str(f1_raw)

                mgr.overwrite_item_list(config['sheets']['item_list'], df)

            # Create Tab & Write Data
            base_sheet = st.session_state.get('base_sheet', config['sheets'].get('recap_base', 'Base'))
            mgr.create_promo_tab(base_sheet, st.session_state.current_tab)
            
            mappings = config['mappings']
            mgr.write_to_cell(st.session_state.current_tab, mappings['ty_qualify_dates'], f"{st.session_state.ty_q_start} - {st.session_state.ty_q_end}")
            mgr.write_to_cell(st.session_state.current_tab, mappings['ty_redeem_dates'], f"{st.session_state.ty_r_start} - {st.session_state.ty_r_end}")
            mgr.write_to_cell(st.session_state.current_tab, mappings['ly_qualify_dates'], f"{st.session_state.ly_q_start} - {st.session_state.ly_q_end}")
            mgr.write_to_cell(st.session_state.current_tab, mappings['ly_redeem_dates'], f"{st.session_state.ly_r_start} - {st.session_state.ly_r_end}")
            mgr.write_to_cell(st.session_state.current_tab, mappings['p4_qualify_amt'], p4_val)
            mgr.write_to_cell(st.session_state.current_tab, mappings['q4_redeem_amt'], q4_val)
            
            st.session_state.step = 4
            st.rerun()

    def render_step_4(self, mgr, config):
        render_persistent_header()
        st.header("Step 4: Execute SQL")
        
        sql_sheet = config['sheets']['sql_output']
        sql_col = config['mappings']['sql_code_col']
        raw_sql = mgr.read_column(sql_sheet, sql_col)
        
        if raw_sql and raw_sql.strip():
            injected_sql = str(raw_sql)
            replacements = {
                r"WbVarDef\s+qualify_start\s*=\s*''": f"WbVarDef qualify_start='{st.session_state.ty_q_start}'",
                r"WbVarDef\s+qualify_end\s*=\s*''": f"WbVarDef qualify_end='{st.session_state.ty_q_end}'",
                r"WbVarDef\s+ly_qualify_start\s*=\s*''": f"WbVarDef ly_qualify_start='{st.session_state.ly_q_start}'",
                r"WbVarDef\s+ly_qualify_end\s*=\s*''": f"WbVarDef ly_qualify_end='{st.session_state.ly_q_end}'",
                r"articl_list\s*=\s*\(\)": f"articl_list={st.session_state.get('sql_article_tuple', '()')}",
                r"article_list\s*=\s*\(\)": f"article_list={st.session_state.get('sql_article_tuple', '()')}" 
            }
            for pattern, new_str in replacements.items():
                injected_sql = re.sub(pattern, new_str, injected_sql, flags=re.IGNORECASE)
        else:
            injected_sql = "-- Error: No SQL code found in designated column."

        st.code(injected_sql, language="sql")
        st.caption("Hover over the top right of the code block above to copy it. Run it externally.")
        
        if st.button("Enter SQL Output"):
            st.session_state.step = 5
            st.rerun()

    def render_step_5(self, mgr, config):
        render_persistent_header()
        st.header("Step 5: Paste SQL Output")
        st.caption("Paste your output row below (tabs or spaces are fine):")
        sql_output_str = st.text_area("SQL Output")
        
        if st.button("Complete Analysis", type="primary"):
            if sql_output_str:
                parsed_data = [item.strip() for item in re.split(r'\s+', sql_output_str.strip()) if item]
                mgr.write_vertical_array(st.session_state.current_tab, config['mappings']['sql_output_start'], parsed_data)
                
                st.success(f"Analysis complete for {st.session_state.current_tab}!")
                st.session_state.step = 6 
                st.rerun()
            else:
                st.warning("Please paste the SQL output first.")