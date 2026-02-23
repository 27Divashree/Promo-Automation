# Promo Recap & SQL Generator

A Streamlit-based web application designed to automate the generation of promotional recap reports. This tool takes user inputs (dates, qualification/redemption amounts), processes article lists (CSV/Excel), dynamically injects variables into a base SQL template, and compiles the final output into a neatly formatted Excel workbook.

## ✨ Features

* **Dynamic Excel Tab Management:** Copies a base template sheet and automatically routes user inputs to the correct mapping cells (via JSON configuration).
* **Article List Processing:** Upload Excel or CSV files containing article/item lists. The app automatically extracts the necessary article IDs into a tuple for SQL injection and saves the raw list to a dedicated `item_List_<tab_name>` sheet.
* **Smart SQL Injection:** Reads a raw SQL template from the Excel file and uses Regex to inject User Dates and Article Tuples directly into the code.
* **SQL Audit Trail:** Automatically creates an `sql_<tab_name>` sheet for every analysis, cascading the exact executed SQL code line-by-line down Column K for reference.
* **Modular Architecture:** UI components, Excel handling operations, and Promo-specific handlers are separated for clean, maintainable code.

## 📂 Project Structure

```text
├── app.py                         # Main Streamlit application entry point
├── components.py                  # Reusable UI components (Date inputs, file uploaders)
├── excel_handler.py               # ExcelManager class handling openpyxl operations
├── Small_Scale_Template.xlsx      # Base Excel template with formatting and raw SQL
├── configs/
│   └── small_scale.json           # JSON config mapping UI inputs to Excel cell coordinates
└── handlers/
    └── small_scale_recap.py       # Step-by-step logic (Step 3 to 5) for this specific recap

```

## ⚙️ Prerequisites & Setup

1. **Python 3.8+** is recommended.
2. Install the required Python packages:

```bash
pip install streamlit pandas openpyxl

```

3. **Run the application:**

```bash
streamlit run app.py

```

## 🚀 How to Use (The Workflow)

### Step 1 & 2: Initialization (Handled in `app.py`)

* Enter the Promotion Name and select the analysis type/tab name you are generating.
* The application loads the `small_scale.json` configuration and initializes the `ExcelManager` with the base template.

### Step 3: Configuration & Inputs

* **Dates:** Select TY (This Year) and LY (Last Year) Qualification and Redemption dates.
* **Amounts:** Enter the P4 (Qualification) and Q4 (Redemption) monetary values.
* **Articles:** Upload your list of promotional articles. The app extracts the article list for the SQL query and saves the file to a dynamically named `item_List_<tab_name>` sheet.

### Step 4: Execute SQL

* The application reads the raw SQL from the base template and injects your exact dates and article tuples into the code.
* Copy the generated SQL from the Streamlit UI and run it in your external database tool (e.g., DBeaver, Snowflake, SSMS).

### Step 5: Paste SQL Output

* Paste the resulting rows from your SQL query back into the Streamlit app.
* The application parses the data and writes it vertically into the main Excel tab.
* A new `sql_<tab_name>` sheet is generated, and the injected SQL code from Step 4 is written line-by-line into Column K for auditing purposes.

### Final Step: Download

* Once all tabs are completed, click finalize to download the fully assembled `.xlsx` workbook.

## 🛠️ Configuration (`small_scale.json`)

To change where data is written in the Excel file, update the `"mappings"` section in the JSON file. You do not need to change the Python code to move cell targets.

Example:

```json
"mappings": {
    "p4_qualify_amt": "B5",
    "q4_redeem_amt": "B6",
    "sql_output_start": "P2",
    "sql_code_col": "A"
}

```

