import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# Simple in-memory cache for get_all_data(). Avoids re-reading all 7 sheets
# on every dashboard poll / chat message / update check, which is what
# blows through Sheets API's 60-reads-per-minute-per-user quota.
_CACHE = {"data": None, "timestamp": 0}
_CACHE_TTL_SECONDS = 20

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
    
def get_all_data(spreadsheet, force_refresh=False):
    """
    Reads all 7 sheets and packs them together.
    Returns a dictionary with one key per sheet.

    Cached for _CACHE_TTL_SECONDS to avoid burning through the Sheets API
    read quota (60/min/user) when the dashboard is polling every 30s while
    chat messages and updates are also firing. Pass force_refresh=True
    right after a write (e.g. in update_by_id) so the next read reflects it.
    """
    now = time.time()
    if not force_refresh and _CACHE["data"] is not None and (now - _CACHE["timestamp"]) < _CACHE_TTL_SECONDS:
        return _CACHE["data"]

    data = {
        "material_ledger": get_sheet_data(spreadsheet, "Material_Ledger"),
        "production_jobs": get_sheet_data(spreadsheet, "Production_Jobs"),
        "machines": get_sheet_data(spreadsheet, "Machines"),
        "vendors": get_sheet_data(spreadsheet, "Vendors"),
        "quality_log": get_sheet_data(spreadsheet, "Quality_Log"),
        "event_log": get_sheet_data(spreadsheet, "Event_Log"),
        "gearbox_assembly": get_sheet_data(spreadsheet, "Gearbox_Assembly")
    }
    _CACHE["data"] = data
    _CACHE["timestamp"] = now
    return data

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
    Finds all idle machines and accurately reports why,
    by checking their specific assigned job ID.
    """
    alerts = []

    for machine in machines:
        if machine.get("Current_Status") == "Idle":
            reason = "No job currently assigned."
            current_job = str(machine.get("Current_Job_ID", "")).strip()
            
            # Check if the machine is actually assigned to a specific job (and not 'None')
            if current_job and current_job.lower() != "none":
                # Find that exact job in the production list
                job_details = next((j for j in production_jobs if j.get("Job_ID") == current_job), None)
                
                if job_details and job_details.get("Status") == "Delayed":
                    reason = f"Waiting on assigned Job {current_job} ({job_details.get('Part_Name')}) which is delayed."
                else:
                    reason = f"Assigned to {current_job}, but sitting idle."

            alerts.append({
                "machine_id": machine.get("Machine_ID"),
                "machine_name": machine.get("Machine_Name"),
                "operator": machine.get("Operator_Name"),
                "idle_hours": machine.get("Idle_Hours"),
                "reason": reason,
                "message": f"{machine.get('Machine_Name')} is idle ({machine.get('Idle_Hours')} hrs today). {reason}"
            })
    
    return alerts

def get_gearbox_assembly(spreadsheet):
    """
    Reads Gearbox_Assembly tab.
    Returns list of gearbox dictionaries.
    """
    return get_sheet_data(spreadsheet, "Gearbox_Assembly")

def update_by_id(spreadsheet, sheet_name, id_column, id_value, update_column, new_value):
    """
    Finds a row by its ID and updates a specific column.
    Example: update Vendor V002's Expected_Delivery to 15-Jul-2026
    
    sheet_name: which tab (Vendors, Production_Jobs, Machines, Material_Ledger)
    id_column: the column that identifies the row (Vendor_ID, Job_ID, Machine_ID, Batch_ID)
    id_value: the ID to search for (V002, J001, M003, B001)
    update_column: which column to update
    new_value: the new value to write
    Returns True if successful, False if not.
    """
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        all_records = worksheet.get_all_records()
        headers = worksheet.row_values(1)

        if id_column not in headers:
            print(f"ID column {id_column} not found in {sheet_name}")
            return False

        if update_column not in headers:
            print(f"Update column {update_column} not found in {sheet_name}")
            return False

        id_col_idx = headers.index(id_column)
        update_col_idx = headers.index(update_column) + 1

        for i, row in enumerate(all_records):
            if str(row.get(id_column, '')).strip() == str(id_value).strip():
                row_number = i + 2  # +1 for header, +1 for 1-based index
                worksheet.update_cell(row_number, update_col_idx, new_value)
                print(f"✅ Updated {sheet_name} row {row_number}: {update_column} = {new_value}")
                _CACHE["data"] = None  # force next get_all_data() to re-read, not serve stale cache
                return True

        print(f"❌ ID {id_value} not found in {sheet_name}")
        return False

    except Exception as e:
        print(f"Update failed: {e}")
        return False