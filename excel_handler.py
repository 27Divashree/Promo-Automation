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
    
    def read_column(self, sheet_name, col_letter):
        """Reads an entire column and joins the text (useful for multi-line SQL)"""
        sheet = self.wb[sheet_name]
        data = []
        # Loop through every row in the column up to the max row
        for row in range(1, sheet.max_row + 1):
            val = sheet[f"{col_letter}{row}"].value
            # Append the value, or a blank string if the cell is empty (preserves spacing)
            data.append(str(val) if val is not None else "")
        
        # Join it all together with line breaks
        return "\n".join(data)
