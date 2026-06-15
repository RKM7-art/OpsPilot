import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# The APIs our app needs permission to use
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

SHEET_NAME = "OpsPilot - Sudarshan Gears"

def connect_to_sheets():
    """
    Connect to Google Sheets using service account credentials.
    Returns the spreadsheet object, or None if connection fails.
    """

    try:
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes = SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        return spreadsheet
    
    except Exception as e:
        print(f"Connection failed: {e}")
        return None
    
def get_sheet_data(spreadsheet, sheet_name):
    """
    Reads all data from a specific sheet tab.
    Returns a list of dictionaries (one per row)
    """

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return data
    
    except Exception as e:
        print(f"Could not read {sheet_name}: {e}")
        return []
    
def get_all_data(spreadsheet):
    """
    Reads all 5 sheets and packs them together.
    Returns a dictionary with one key per sheet.
    """

    return {
        "material_ledger": get_sheet_data(spreadsheet, "Material_Ledger"),
        "production_jobs": get_sheet_data(spreadsheet, "Production_Jobs"),
        "machines": get_sheet_data(spreadsheet, "Machines"),
        "vendors": get_sheet_data(spreadsheet, "Vendors"),
        "quality_log": get_sheet_data(spreadsheet, "Quality_Log"),
        "event_log": get_sheet_data(spreadsheet, "Event_Log")
    }

def update_sheet_data(spreadsheet, sheet_name, row_number, column_name, new_value):
    """
    Updates a single cell in a sheet.
    row_number: the row to update (2 = first data row, since row 1 is headers)
    column_name: the header name of the column to update
    new_value: the new value to write
    Returns True if successful, False if not.
    """

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        headers = worksheet.row_values(1)

        if column_name not in headers:
            print(f"Column {column_name} not found in {sheet_name}")
            return False

        col_number = headers.index(column_name) + 1
        worksheet.update_cell(row_number, col_number, new_value)
        return True

    except Exception as e:
        print(f"Update failed: {e}")
        return False
    
def check_reorder_alerts(material_ledger):
    """
    Checks Material_Ledger data for batches that are on low stock.
    A batch is flagged if the Remaining_Quantity is less than
    10% of the Initial_Quantity.
    Returns a list of alert dictionaries.
    """

    alerts = []

    for row in material_ledger:
        try:
            initial = float(row.get("Initial_Quantity", 0))
            remaining = float(row.get("Remaining_Quantity", 0))

            if initial > 0 and remaining < (initial * 0.10):
                alerts.append({
                    "batch_id": row.get("Batch_ID"),
                    "material_type": row.get("Material_Type"),
                    "remaining": remaining,
                    "initial": initial,
                    "vendor": row.get("Vendor_Name"), 
                    "message": f"Batch {row.get('Batch_ID')} ({row.get('Material_Type')}) "
                               f"is low - only {remaining} of {initial} remaining."
                })
        
        except (ValueError, TypeError):
            continue
    
    return alerts

def check_vendor_delays(vendors):
    """
    Checks Vendors data for deliveries that are overdue.
    A Vendor is flagged if Expected_Delivery date has passed
    and Actual_Delivery delivery is still 'Pending'.
    Returns a list of alert dictionaries.
    """

    alerts = []
    today = datetime.now()
    
    for row in vendors:
        actual = row.get("Actual_Delivery", "")
        expected_str = row.get("Expected_Delivery", "")

        if actual == "Pending" and expected_str:
            try:
                expected_date = datetime.strptime(expected_str, "%d-%b-%Y")

                if expected_date < today: 
                    days_late = (today - expected_date).days
                    alerts.append({
                        "vendor_id": row.get("Vendor_ID"),
                        "vendor_name": row.get("Vendor_Name"),
                        "supply_type": row.get("Supply_Type"),
                        "expected_delivery": expected_str,
                        "days_late": days_late,
                        "message": f"{row.get('Vendor_Name')} delivery of "
                        f"{row.get('Supply_Type')} is {days_late} day(s) late."
                    })
            
            except ValueError:
                continue
    
    return alerts

def check_idle_machines(machines, production_jobs):
    """
    Finds all idle machines and tries to explain why,
    by checking if there is a job waiting on a delayed
    or in-progress earlier stage.
    Returns a list of alert dictionaries.
    """

    alerts = []

    for machine in machines:
        if machine.get("Current_Status") == "Idle":
            reason = "No job currently assigned."
        
        #Check if any job is delayed - could be the cause
            for job in production_jobs:
                if job.get("Status") == "Delayed":
                    reason = (f"Possibly waiting on Job {job.get('Job_ID')} "
                              f"({job.get('Part_Name')}) which is delayed.")
                    break

            alerts.append({
                "machine_id": machine.get("Machine_ID"),
                "machine_name": machine.get("Machine_Name"),
                "operator": machine.get("Operator_Name"),
                "idle_hours": machine.get("Idle_Hours"),
                "reason": reason,
                "message":f"{machine.get('Machine_Name')} is idle "
                          f"({machine.get('Idle_Hours')} hrs today). {reason}"
            })
    
    return alerts