import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO


class ExcelManager:
    def __init__(self, template_path):
        self.wb = openpyxl.load_workbook(template_path)

    def get_sheet_names(self):
        return self.wb.sheetnames

    def create_promo_tab(self, base_sheet_name, new_tab_name):
        base_sheet = self.wb[base_sheet_name]
        new_sheet = self.wb.copy_worksheet(base_sheet)
        new_sheet.title = new_tab_name
        return new_sheet

    def write_to_cell(self, sheet_name, cell_ref, value):
        self.wb[sheet_name][cell_ref] = value

    def read_cell(self, sheet_name, cell_ref):
        return self.wb[sheet_name][cell_ref].value

    def append_dataframe(self, sheet_name, df):
        sheet = self.wb[sheet_name]
        max_row = sheet.max_row

        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            if max_row > 1 and r_idx == 1:
                continue
            for c_idx, value in enumerate(row, 1):
                sheet.cell(row=max_row + r_idx - 1, column=c_idx, value=value)

    def write_vertical_array(self, sheet_name, start_cell, data_list):
        sheet = self.wb[sheet_name]
        col = start_cell[0]
        start_row = int(start_cell[1:])
        for i, val in enumerate(data_list):
            try:
                val_to_write = float(val)
            except ValueError:
                val_to_write = val
            sheet[f"{col}{start_row + i}"] = val_to_write

    def get_download_bytes(self):
        output = BytesIO()
        self.wb.save(output)
        output.seek(0)
        return output
    
    def overwrite_item_list(self, sheet_name, df):
        import pandas as pd
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        # This guarantees we only touch the specific sheet (item-List)
        sheet = self.wb[sheet_name]
        
        # 1. Wipe ONLY this specific sheet clean
        sheet.delete_rows(1, sheet.max_row)
        
        # 2. Paste the uploaded data exactly as-is, starting at A1
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 1):
            for c_idx, value in enumerate(row, 1):
                # Skip blank cells so we don't paste "NaN"
                if pd.notna(value):
                    sheet.cell(row=r_idx, column=c_idx, value=value)