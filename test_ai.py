from modules.sheets_connector import connect_to_sheets
from modules.ai_engine import process_query

print("Connecting to sheets...")
spreadsheet = connect_to_sheets()

if spreadsheet:
    print("Connected! Testing AI...\n")

    # Test 1 - Morning briefing
    print("=" * 50)
    print("Test 1 - What should I focus on today?")
    print("=" * 50)

    response = process_query(
        "What should I focus on today?",
        spreadsheet
    )
    print(response)

else:
    print("Connection failed - check credentials.json")
