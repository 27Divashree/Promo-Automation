# Promo Recap Automator

A Streamlit application that automates the creation of promotional recap reports. It takes user inputs (dates, qualification amounts, and item lists), generates the necessary SQL queries, and automatically formats the results into a ready-to-download Excel workbook.

## 🚀 Quick Start

**1. Install Dependencies**
Make sure you have Python installed, then install the required packages:

```bash
pip install streamlit pandas openpyxl

```

**2. Run the App**
Start the Streamlit server locally:

```bash
streamlit run app.py

```

## 📂 Project Structure

* **`app.py`**: The main application and UI launcher.
* **`components.py`**: Reusable UI blocks (date pickers, file uploaders).
* **`excel_handler.py`**: The backend engine that safely edits and copies Excel tabs.
* **`handlers/`**: Contains the step-by-step logic for specific promotion types.
* **`configs/`**: JSON files that map the UI inputs to the exact cell locations in Excel.
* **`Small_Scale_Template.xlsx`**: The base Excel file used to generate the final reports.

*(Detailed usage instructions and configuration guides will be provided in a separate document.)*

---
