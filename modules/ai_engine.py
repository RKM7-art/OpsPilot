import ollama
from modules.sheets_connector import (
    get_all_data,
    check_reorder_alerts,
    check_vendor_delays,
    check_idle_machines
)
from modules.system_prompt import SYSTEM_PROMPT


def build_context(data, alerts):
    """
    Convert raw sheet data into readable text for AI.
    Input: all 6 sheets data + alerts dictionary
    Output: one clean text string AI can reason about
    """

    context = []

    # Material Ledger
    context.append("=== MATERIAL LEDGER ===")
    for row in data["material_ledger"]:
        context.append(
            f"- {row['Batch_ID']}: {row['Material_Type']} | "
            f"Vendor: {row['Vendor_Name']} | "
            f"Remaining: {row['Remaining_Quantity']}/{row['Initial_Quantity']} | "
            f"Status: {row['Status']} | "
            f"Reserved: {row['Customer_Reserved']}"
        )

    # Production Jobs
    context.append("\n=== ACTIVE PRODUCTION JOBS ===")
    for row in data["production_jobs"]:
        context.append(
            f"- {row['Job_ID']}: {row['Part_Name']} ({row['Part_Code']}) | "
            f"Stage: {row['Current_Stage']} | "
            f"Assigned: {row['Assigned_To']} | "
            f"Status: {row['Status']} | "
            f"Customer: {row['Customer_Name']} | "
            f"End_Date: {row['End_Date']}"
        )

    # Machines
    context.append("\n=== MACHINES ===")
    for row in data["machines"]:
        context.append(
            f"- {row['Machine_ID']} ({row['Machine_Name']}): "
            f"Status: {row['Current_Status']} | "
            f"Job: {row['Current_Job_ID']} | "
            f"Condition: {row['Condition']} | "
            f"Runtime: {row['Runtime_Hours']}hrs | "
            f"Idle: {row['Idle_Hours']}hrs | "
            f"Operator: {row['Operator_Name']}"
        )

    # Vendors
    context.append("\n=== VENDORS ===")
    for row in data["vendors"]:
        context.append(
            f"- {row['Vendor_ID']} ({row['Vendor_Name']}): "
            f"Supplies: {row['Supply_Type']} | "
            f"Expected: {row['Expected_Delivery']} | "
            f"Actual: {row['Actual_Delivery']} | "
            f"Reliability: {row['Reliability_Score']} | "
            f"Pending Orders: {row['Pending_Orders']}"
        )

    # Quality Log
    context.append("\n=== QUALITY LOG ===")
    for row in data["quality_log"]:
        context.append(
            f"- {row['Log_ID']}: {row['Part_Name']} ({row['Part_Code']}) | "
            f"Defect: {row['Defect_Type']} | "
            f"Stage: {row['Stage_Found']} | "
            f"Action: {row['Action_Taken']} | "
            f"Decision: {row['Decision']} | "
            f"Date: {row['Date']}"
        )

    # Event Log
    context.append("\n=== RECENT EVENTS LOG ===")
    for row in data["event_log"]:
        context.append(
            f"- {row['Event_ID']} | {row['Timestamp']} | "
            f"Type: {row['Event_Type']} | "
            f"Entity: {row['Entity_Name']} ({row['Entity_ID']}) | "
            f"Details: {row['Details']} | "
            f"Action: {row['Action_Taken']} | "
            f"Resolution: {row['Resolution_Time']}"
        )

    # Active Alerts
    context.append("\n=== ACTIVE ALERTS ===")

    if alerts["reorder"]:
        context.append("REORDER ALERTS:")
        for alert in alerts["reorder"]:
            context.append(f"  ⚠️ {alert['message']}")
    else:
        context.append("REORDER ALERTS: None")

    if alerts["vendor_delays"]:
        context.append("VENDOR DELAY ALERTS:")
        for alert in alerts["vendor_delays"]:
            context.append(f"  ❌ {alert['message']}")
    else:
        context.append("VENDOR DELAY ALERTS: None")

    if alerts["idle_machines"]:
        context.append("IDLE MACHINE ALERTS:")
        for alert in alerts["idle_machines"]:
            context.append(f"  🔴 {alert['message']}")
    else:
        context.append("IDLE MACHINE ALERTS: None")

    return "\n".join(context)


def get_ai_response(user_message, context):
    """
    Sends user message + context + system prompt to LLaMA 3.2.
    Input: user message + context string
    Output: AI response text
    """

    try:
        full_message = f"""
Here is the current operational data for Sudarshan Gears:

{context}

Based on this data, please answer the following query:
{user_message}
"""
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_message}
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return f"❌ AI Error: {e}. Please ensure Ollama is running."


def process_query(user_message, spreadsheet):
    """
    Master function - orchestrates everything.
    Input: user_message + spreadsheet connection
    Output: final AI response ready to display
    """

    try:
        # Step 1: Read all 6 sheets
        data = get_all_data(spreadsheet)

        # Step 2: Run all 3 alert checks
        alerts = {
            "reorder": check_reorder_alerts(data["material_ledger"]),
            "vendor_delays": check_vendor_delays(data["vendors"]),
            "idle_machines": check_idle_machines(
                data["machines"],
                data["production_jobs"]
            )
        }

        # Step 3: Build readable context
        context = build_context(data, alerts)

        # Step 4: Add pattern analysis to context
        try:
            from modules.pattern_analyzer import get_all_patterns
            patterns = get_all_patterns(spreadsheet)
            context += f"\n\n=== HISTORICAL PATTERNS & EVENTS ===\n{patterns['summary']}"
        except Exception as pattern_error:
            context += f"\n\n=== HISTORICAL PATTERNS & EVENTS ===\nPattern data unavailable: {pattern_error}"

        # Step 5: Get AI response
        response = get_ai_response(user_message, context)

        return response

    except Exception as e:
        return f"❌ System Error: {e}. Please check your connection."