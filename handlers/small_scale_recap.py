import streamlit as st
import pandas as pd
import datetime
import re

class Handler:
    """Handles the UI and logic for the Small Scale Recap Template (Steps 3, 4, 5)"""

    def render_step_3(self, mgr, config):
        st.header("Step 3: Configuration & Inputs")
        
        st.divider()
        st.subheader("3.1 Dates")
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

        st.divider()
        st.subheader("3.2 Article List Upload")
        uploaded_file = st.file_uploader("Upload Article CSV/Excel", type=['csv', 'xlsx'])
        
        st.divider()
        st.subheader("3.3 Qualification/Redemption Amounts")
        p4_val = st.number_input("Qualification Amount (P4)", value=0.0)
        q4_val = st.number_input("Redemption Amount (Q4)", value=0.0)
        
        if st.button("Generate SQL & Create Tab", type="primary"):
            
            # Format dates to mm/dd/yyyy strictly for both SQL and Excel
            fmt = '%m/%d/%Y'
            st.session_state.update({
                "ty_q_start": ty_q_start.strftime(fmt), 
                "ty_q_end": ty_q_end.strftime(fmt),
                "ty_r_start": ty_r_start.strftime(fmt), 
                "ty_r_end": ty_r_end.strftime(fmt),
                "ly_q_start": ly_q_start.strftime(fmt), 
                "ly_q_end": ly_q_end.strftime(fmt),
                "ly_r_start": ly_r_start.strftime(fmt), 
                "ly_r_end": ly_r_end.strftime(fmt),
                "p4_val": p4_val,
                "q4_val": q4_val,
                "sql_article_tuple": "()" # Default empty tuple
            })
            
            # 1. Handle Article Append & SQL List Extraction
            if uploaded_file:
                # Read the file
                if uploaded_file.name.endswith('csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Extract the articles from the first column (Column A)
                articles = df.iloc[:, 0].dropna().astype(str).tolist()
                
                # Format into SQL Tuple: ('123', '456', '789')
                if articles:
                    st.session_state.sql_article_tuple = "(" + ", ".join([f"'{art}'" for art in articles]) + ")"

                # A) Append the raw data (first 4 columns: A-D) to the Excel tab
                mgr.append_dataframe(config['sheets']['item_list'], df.iloc[:, :4])
                
                # B) Write the formatted tuple string directly into cell F1 of the item_list tab
                mgr.write_to_cell(config['sheets']['item_list'], 'F1', st.session_state.sql_article_tuple)

            # 2. Create Tab using the DYNAMICALLY selected base sheet
            tab_name = f"{st.session_state.promo_name} Qual"
            st.session_state.current_tab = tab_name
            mgr.create_promo_tab(st.session_state.base_sheet, tab_name)
            
            # 3. Write data to the newly created tab using the mm/dd/yyyy formatted dates
            mappings = config['mappings']
            mgr.write_to_cell(tab_name, mappings['ty_qualify_dates'], f"{st.session_state.ty_q_start} - {st.session_state.ty_q_end}")
            mgr.write_to_cell(tab_name, mappings['ty_redeem_dates'], f"{st.session_state.ty_r_start} - {st.session_state.ty_r_end}")
            mgr.write_to_cell(tab_name, mappings['ly_qualify_dates'], f"{st.session_state.ly_q_start} - {st.session_state.ly_q_end}")
            mgr.write_to_cell(tab_name, mappings['ly_redeem_dates'], f"{st.session_state.ly_r_start} - {st.session_state.ly_r_end}")
            mgr.write_to_cell(tab_name, mappings['p4_qualify_amt'], p4_val)
            mgr.write_to_cell(tab_name, mappings['q4_redeem_amt'], q4_val)
            
            st.session_state.step = 2
            st.rerun()

    def render_step_4(self, mgr, config):
        st.header("Step 4: Execute SQL")
        
        sql_sheet = config['sheets']['sql_output']
        sql_col = config['mappings']['sql_code_col']
        
        raw_sql = mgr.read_column(sql_sheet, sql_col)
        
        if raw_sql and raw_sql.strip():
            injected_sql = str(raw_sql)
            
            # Using Regex for robust replacement (handles missing spaces around the '=' sign)
            replacements = {
                r"WbVarDef\s+qualify_start\s*=\s*''": f"WbVarDef qualify_start='{st.session_state.ty_q_start}'",
                r"WbVarDef\s+qualify_end\s*=\s*''": f"WbVarDef qualify_end='{st.session_state.ty_q_end}'",
                r"WbVarDef\s+ly_qualify_start\s*=\s*''": f"WbVarDef ly_qualify_start='{st.session_state.ly_q_start}'",
                r"WbVarDef\s+ly_qualify_end\s*=\s*''": f"WbVarDef ly_qualify_end='{st.session_state.ly_q_end}'",
                r"articl_list\s*=\s*\(\)": f"articl_list={st.session_state.sql_article_tuple}",
                r"article_list\s*=\s*\(\)": f"article_list={st.session_state.sql_article_tuple}" # Backup spelling
            }
            
            # Apply all regex replacements
            for pattern, new_str in replacements.items():
                injected_sql = re.sub(pattern, new_str, injected_sql, flags=re.IGNORECASE)
                
        else:
            injected_sql = "-- Error: No SQL code found in designated column."

        st.code(injected_sql, language="sql")
        st.info("Hover over the top right of the code block above to copy it. Run it externally.")
        
        if st.button("Enter SQL Output"):
            st.session_state.step = 3
            st.rerun()

    def render_step_5(self, mgr, config):
        st.header("Step 5: Paste SQL Output")
        st.info("Paste your output row below (tabs or spaces are fine):")
        sql_output_str = st.text_area("SQL Output")
        
        if st.button("Complete Analysis", type="primary"):
            if sql_output_str:
                # Splits safely by any amount of whitespace (spaces, tabs, newlines)
                parsed_data = [item.strip() for item in re.split(r'\s+', sql_output_str.strip()) if item]
                
                mgr.write_vertical_array(
                    st.session_state.current_tab, 
                    config['mappings']['sql_output_start'], 
                    parsed_data
                )
                
                st.session_state.step = 4
                st.rerun()
            else:
                st.warning("Please paste the SQL output first.")