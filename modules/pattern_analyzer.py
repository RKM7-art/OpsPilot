from collections import Counter
from modules.event_logger import get_recent_events


def get_all_patterns(spreadsheet):
    """
    Master function — reads Event_Log ONCE,
    filters in Python to avoid API quota errors.
    Returns combined pattern summary for AI.
    """

    try:
        # Read Event_Log only ONE time — no extra API calls
        all_events = get_recent_events(spreadsheet, limit=50)

        if not all_events:
            return {
                "summary": (
                    "No events logged yet. "
                    "Patterns will emerge as events are recorded."
                )
            }

        # Filter by type locally in Python
        machine_events = [
            e for e in all_events
            if e.get("Event_Type") == "Machine_Breakdown"
        ]
        vendor_events = [
            e for e in all_events
            if e.get("Event_Type") in ["Vendor_Delay", "Vendor_Delivered"]
        ]
        quality_events = [
            e for e in all_events
            if e.get("Event_Type") == "Quality_Defect"
        ]
        material_events = [
            e for e in all_events
            if e.get("Event_Type") == "Material_Low"
        ]

        summary = []

        # Machine patterns
        if machine_events:
            machine_counts = Counter(
                e.get("Entity_Name") for e in machine_events
            )
            summary.append("=== MACHINE PATTERNS ===")
            for name, count in machine_counts.items():
                flag = (
                    "⚠️ Repeat breakdown — check maintenance schedule."
                    if count >= 2 else
                    "✅ Single occurrence."
                )
                summary.append(
                    f"  {name} broke down {count} time(s). {flag}"
                )

        # Vendor patterns
        if vendor_events:
            delay_counts = Counter(
                e.get("Entity_Name") for e in vendor_events
                if e.get("Event_Type") == "Vendor_Delay"
            )
            if delay_counts:
                summary.append("\n=== VENDOR PATTERNS ===")
                for name, count in delay_counts.items():
                    flag = (
                        "❌ Consistently unreliable — consider alternate vendor."
                        if count >= 2 else
                        "⚠️ Single delay recorded."
                    )
                    summary.append(
                        f"  {name} delayed {count} time(s). {flag}"
                    )

        # Quality patterns
        if quality_events:
            part_counts = Counter(
                e.get("Entity_Name") for e in quality_events
            )
            summary.append("\n=== QUALITY PATTERNS ===")
            for name, count in part_counts.items():
                flag = (
                    "⚠️ REPEAT DEFECT — possible process issue. "
                    "Recommend QC inspection."
                    if count >= 2 else
                    "✅ Single occurrence."
                )
                summary.append(
                    f"  {name} has {count} defect(s) logged. {flag}"
                )

        # Material patterns
        if material_events:
            material_counts = Counter(
                e.get("Entity_Name") for e in material_events
            )
            summary.append("\n=== MATERIAL PATTERNS ===")
            for name, count in material_counts.items():
                flag = (
                    "⚠️ Frequent shortage — increase reorder quantity."
                    if count >= 2 else
                    "✅ Occasional shortage."
                )
                summary.append(
                    f"  {name} ran low {count} time(s). {flag}"
                )

        if not summary:
            summary.append(
                "No patterns detected yet. "
                "Patterns will emerge as more events are logged."
            )

        return {
            "summary": "\n".join(summary)
        }

    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        return {
            "summary": "Pattern analysis unavailable."
        }