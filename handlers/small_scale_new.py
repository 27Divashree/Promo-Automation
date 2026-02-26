import streamlit as st
import pandas as pd
import datetime
import re
import importlib
from components import render_persistent_header

class Handler:
    def render_step_3(self, mgr, config):
        render_persistent_header()
        
        # 1. Sequence State Management
        if 'lly_sub_step' not in st.session_state:
            st.session_state.lly_sub_step = "LY"

        # Map display titles and target bases to the sequence
        # Uses sheet names defined in JSON: "LY", "TY", "Lift Analysis"
        sequence = {
            "LY": {"base": config['sheets']['ly_base'], "title": "Phase 1: Last Year (LY)"},
            "TY": {"base": config['sheets']['ty_base'], "title": "Phase 2: This Year (TY)"},
            "LIFT": {"base": config['sheets']['lift_base'], "title": "Phase 3: Lift Analysis"}
        }
        
        current_phase = st.session_state.lly_sub_step
        st.header(sequence[current_phase]["title"])
        st.info(f"Progress: Currently configuring the **{current_phase}** tab.")

        ext = st.session_state.get('extracted', {})
        today = datetime.date.today()

        with st.form(f"form_{current_phase}"):
            # --- DATE SECTION ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("TY Dates")
                ty_qs = st.date_input("TY Qualify Start", value=ext.get("ty_q_start", today))
                ty_qe = st.date_input("TY Qualify End",   value=ext.get("ty_q_end", today + datetime.timedelta(days=14)))
                ty_rs = st.date_input("TY Redeem Start",  value=ext.get("ty_r_start", today + datetime.timedelta(days=15)))
                ty_re = st.date_input("TY Redeem End",    value=ext.get("ty_r_end", today + datetime.timedelta(days=29)))
            with col2:
                st.subheader("LY Dates")
                ly_qs = st.date_input("LY Qualify Start", value=ext.get("ly_q_start", ty_qs - datetime.timedelta(days=364)))
                ly_qe = st.date_input("LY Qualify End",   value=ext.get("ly_q_end", ty_qe - datetime.timedelta(days=364)))
                ly_rs = st.date_input("LY Redeem Start",  value=ext.get("ly_r_start", ty_rs - datetime.timedelta(days=364)))
                ly_re = st.date_input("LY Redeem End",    value=ext.get("ly_r_end", ty_re - datetime.timedelta(days=364)))
            with col3:
                st.subheader("LLY Dates (LY + 1 Day)")
                lly_qs, lly_qe = ly_qs + datetime.timedelta(days=1), ly_qe + datetime.timedelta(days=1)
                lly_rs, lly_re = ly_rs + datetime.timedelta(days=1), ly_re + datetime.timedelta(days=1)
                st.date_input("LLY Qualify Start", value=lly_qs, disabled=True)
                st.date_input("LLY Qualify End",   value=lly_qe, disabled=True)
                st.date_input("LLY Redeem Start",  value=lly_rs, disabled=True)
                st.date_input("LLY Redeem End",    value=lly_re, disabled=True)

            # --- ARTICLE SECTION ---
            st.divider()
            st.subheader("Article List Uploads")
            u_ty = st.file_uploader("Upload TY Article List", type=['xlsx', 'csv'], key=f"ty_up_{current_phase}")
            u_ly = st.file_uploader("Upload LY Article List", type=['xlsx', 'csv'], key=f"ly_up_{current_phase}")
            u_lly = st.file_uploader("Upload LLY Article List", type=['xlsx', 'csv'], key=f"lly_up_{current_phase}")

            # --- AMOUNTS & TAB NAME ---
            st.divider()
            a1, a2, a3 = st.columns(3)
            with a1: p4_val = st.number_input("P4 Amount", value=float(ext.get("q_amt", 0.0)))
            with a2: q4_val = st.number_input("Q4 Amount", value=float(ext.get("r_amt", 0.0)))
            with a3: 
                new_tab_name = st.text_input("New Tab Name:", value=f"{st.session_state.promo_name}_{current_phase}")

            submit = st.form_submit_button(f"Generate {current_phase} & Proceed", type="primary")

        if submit:
            if not all([u_ty, u_ly, u_lly]):
                st.error("Please upload all three article lists (TY, LY, and LLY) to proceed.")
                return

            fmt = '%m/%d/%Y'
            st.session_state.selected_base = sequence[current_phase]["base"]
            
            # DATE SHIFT LOGIC: In LY phase, Excel "TY" cells get "LY" data.
            if current_phase == "LY":
                f_ty_qs, f_ty_qe, f_ty_rs, f_ty_re = ly_qs, ly_qe, ly_rs, ly_re
                f_ly_qs, f_ly_qe, f_ly_rs, f_ly_re = lly_qs, lly_qe, lly_rs, lly_re
            else:
                f_ty_qs, f_ty_qe, f_ty_rs, f_ty_re = ty_qs, ty_qe, ty_rs, ty_re
                f_ly_qs, f_ly_qe, f_ly_rs, f_ly_re = ly_qs, ly_qe, ly_rs, ly_re

            # Update Session State for SQL step
            st.session_state.update({
                "ty_q_start": f_ty_qs.strftime(fmt), "ty_q_end": f_ty_qe.strftime(fmt),
                "ty_r_start": f_ty_rs.strftime(fmt), "ty_r_end": f_ty_re.strftime(fmt),
                "ly_q_start": f_ly_qs.strftime(fmt), "ly_q_end": f_ly_qe.strftime(fmt),
                "ly_r_start": f_ly_rs.strftime(fmt), "ly_r_end": f_ly_re.strftime(fmt),
                "current_tab": new_tab_name,
                "p4_val": p4_val,
                "q4_val": q4_val
            })

            # Process Articles & SQL Tuple extraction
            art_files = {"TY": u_ty, "LY": u_ly, "LLY": u_lly}
            for label, fobj in art_files.items():
                fobj.seek(0)
                df = pd.read_excel(fobj, header=None) if fobj.name.endswith('xlsx') else pd.read_csv(fobj, header=None)
                if label == "TY" and df.shape[1] >= 6:
                    st.session_state.sql_article_tuple = str(df.iloc[0, 5])
                # Save each article list to a raw sheet in the workbook
                mgr.add_raw_sheet(f"{label}_Items_{new_tab_name}"[:31], df)

            # Create Tab & Write Header Data
            mgr.create_promo_tab(st.session_state.selected_base, new_tab_name)
            m = config['mappings']
            mgr.write_to_cell(new_tab_name, m['ty_qualify_dates'], f"{st.session_state.ty_q_start} - {st.session_state.ty_q_end}")
            mgr.write_to_cell(new_tab_name, m['ly_qualify_dates'], f"{st.session_state.ly_q_start} - {st.session_state.ly_q_end}")
            mgr.write_to_cell(new_tab_name, m['p4_qualify_amt'], p4_val)
            mgr.write_to_cell(new_tab_name, m['q4_redeem_amt'], q4_val)
            
            st.session_state.step = 4
            st.rerun()

    def render_step_4(self, mgr, config):
        render_persistent_header()
        st.header(f"Step 4: SQL Injection ({st.session_state.lly_sub_step})")
        
        # Lift Analysis uses Column C, others use Column A
        sql_col = "C" if st.session_state.selected_base == config['sheets']['lift_base'] else "A"
        raw_sql = mgr.read_column(config['sheets']['sql_output'], sql_col)
        
        # Regular expression injection
        injected = re.sub(r"qualify_start\s*=\s*''", f"qualify_start='{st.session_state.ty_q_start}'", str(raw_sql), flags=re.I)
        injected = re.sub(r"article_list\s*=\s*\(\)", f"article_list={st.session_state.sql_article_tuple}", injected, flags=re.I)
        
        st.code(injected, language="sql")
        if st.button("Proceed to Data Paste"):
            st.session_state.step = 5
            st.rerun()

    def render_step_5(self, mgr, config):
        render_persistent_header()
        st.header(f"Step 5: Paste {st.session_state.lly_sub_step} Results")
        st.info("Paste SQL output as space-separated 'Key Value' pairs (e.g. MetricA 100 MetricB 200)")
        
        raw_input = st.text_area("SQL Output Data", height=200)
        
        if st.button("Save Data & Continue", type="primary"):
            if not raw_input:
                st.warning("Please paste data to continue.")
                return

            # Parse input string into Key-Value Dictionary
            tokens = re.split(r'\s+', raw_input.strip())
            if len(tokens) % 2 != 0:
                st.error("Data mismatch: Every Key must have a Value.")
                return
            
            pasted_dict = {tokens[i]: tokens[i+1] for i in range(0, len(tokens), 2)}
            
            # Use the reusable Manager function for K-V writing
            mgr.write_kv_pairs(
                sheet_name=st.session_state.current_tab,
                data_dict=pasted_dict,
                mapping_dict=config.get('sql_mappings', {})
            )

            # Logic to handle the sequence loop
            if st.session_state.lly_sub_step == "LY":
                st.session_state.lly_sub_step = "TY"
                st.session_state.step = 3 # Loop back to Step 3 for TY
            elif st.session_state.lly_sub_step == "TY":
                st.session_state.lly_sub_step = "LIFT"
                st.session_state.step = 3 # Loop back to Step 3 for Lift
            else:
                # Finished Lift Analysis
                del st.session_state.lly_sub_step
                st.success("All phases (LY, TY, Lift) completed successfully!")
                st.session_state.step = 2 # Reset to template selection/export
            st.rerun()