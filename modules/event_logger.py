from datetime import datetime

# Valid event types OpsPilot can log
EVENT_TYPES = [
    "Machine_Breakdown",
    "Machine_Restored",
    "Vendor_Delay",
    "Vendor_Delivered",
    "Quality_Defect",
    "Material_Low",
    "Material_Restocked",
    "Job_Delayed",
    "Job_Completed",
    "Stage_Updated"
]

def create_event_id(worksheet):
    """
    Auto generates next Event ID.
    Reads existing rows and increments.
    EV001, EV002, EV011, EV012...
    """

    try:
        existing = worksheet.get_all_records()
        next_number = len(existing) + 1
        return f"EV{str(next_number).zfill(3)}"
    except Exception as e:
        print(f"Couldn't generate Event ID: {e}")
        return None
    
def log_event(
        spreadsheet,
        event_type,
        entity_id,
        entity_name,
        details,
        reported_by,
        shift,
        action_taken = "Pending",
        resolution_time = "Pending"
):
    """
    Logs an event directly to Event_Log sheet.
    No confirmation needed - Logging automatic.

    event_type: must be one of EVENT_TYPES
    entity_id: ID of affected entity (M003, V002)
    entity_name: Human readable name (Lathe-1)
    details: Full description of what happened
    reported_by: Who reported this
    shift: morning or night
    action_taken: What was done (default pending)
    resolution_time: How long it took (default pending)
    Returns: Event_ID if successful, None if failed.
    """

    try:
        # Validate event type
        if event_type not in EVENT_TYPES:
            print(f"❌ Invalid event type: {event_type}")
            print(f"Valid types: {EVENT_TYPES}")
            return None
        
        # Open Event_Log sheet
        worksheet = spreadsheet.worksheet("Event_Log")

        # Generate Event_ID and Timestamp
        event_id = create_event_id(worksheet)
        if not event_id:
            return None
        
        timestamp = datetime.now().strftime("%d-%b-%Y %H:%M")

        # Build row in exact column order matching our sheet
        new_row = [
            event_id,       # Event_ID
            timestamp,      # Timestamp
            event_type,     # Event_Type
            entity_id,      # Entity_ID
            entity_name,    # Entity_Name
            details,        # Details
            reported_by,    # Reported_By
            shift,          # Shift
            action_taken,   # Action_Taken
            resolution_time # Resolution_Time
        ]

        # Write directly to sheet - no confirmation needed
        worksheet.append_row(new_row)
        print(f"✅ Event logged: {event_id} — {event_type} — {entity_name}")
        return event_id
    
    except Exception as e:
        print(f"❌ Failed to log event: {e}")
        return None
    
def get_recent_events(spreadsheet, limit = 20):
    """
    Reads most recent events from Event_Log.
    Used by pattern_analyzer to find patterns.

    limit: how many recent events to return (default 20)
    Returns: list of event dictionaries
    """

    try:
        worksheet = spreadsheet.worksheet("Event_Log")
        all_events = worksheet.get_all_records()

        # Events stored oldest first - return most recent
        recent = (
            all_events[-limit:]
            if len(all_events) > limit
            else all_events
        )
        return recent
    
    except Exception as e:
        print(f"❌ Failed to get recent events: {e}")
        return []
    
def get_events_by_type(spreadsheet, event_type):
    """
    Gets all events of a specific type.
    Example: all Machine_Breakdown events

    event_type: one of EVENT_TYPES
    Returns: list of matching event dictionaries
    """

    try:
        worksheet = spreadsheet.worksheet("Event_Log")
        all_events = worksheet.get_all_records()

        filtered = [
            event for event in all_events
            if event.get("Event_Type") == event_type
        ]
        return filtered
    
    except Exception as e:
        print(f"❌ Failed to get events by type: {e}")
        return []
    
def get_events_by_entity(spreadsheet, entity_id):
    """
    Get all events related to a specific entity.
    Example: all events for machine M005

    entity_id: ID to search (M005, V002, SG-G-001)
    Returns: list of matching event dictionaries
    """

    try:
        worksheet = spreadsheet.worksheet("Event_Log")
        all_events = worksheet.get_all_records()
        
        filtered = [
            event for event in all_events
            if event.get("Entity_ID") == entity_id
        ]
        return filtered
    
    except Exception as e:
        print(f"❌ Failed to get events by entity: {e}")
        return []