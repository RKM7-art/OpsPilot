from modules.sheets_connector import connect_to_sheets, get_all_data

print("Attempting to connect...")
spreadsheet = connect_to_sheets()

if spreadsheet:
    print("Connected successfully!")
    print(f"Spreadsheet title: {spreadsheet.title}")

    print("\nFetching all data...")
    data = get_all_data(spreadsheet)

    for sheet_name, rows in data.items():
        print(f"\n{sheet_name}: {len(rows)} rows")
        if rows:
            print(f"First row: {rows[0]}")
else:
    print("Connection failed - check credentials.json and sheet sharing")