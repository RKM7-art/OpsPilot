from datetime import datetime, timedelta
from collections import Counter
from modules.event_logger import(
    get_recent_events,
    get_events_by_type,
    get_events_by_entity
)

def analyze_machine_patterns(spreadsheet):
    """
    Analyzes machine breakdown history.
    Finds: breakdown frequency per machine
    Predicts: when next breakdown likely
    Alerts: if machine due for maintenance
    Returns: list of pattern dictionaries
    """

    patterns = []

    try:
        # Get all machine breakdown events
        breakdowns = get_events_by_type(
            spreadsheet,
            "Machine_Breakdown"
        )

        if not breakdowns:
            return []
        
        # Group breakdowns by machine
        machine_breakdowns = {}
        for event in breakdowns:
            machine_id = event.get("Entity_ID")
            if machine_id not in machine_breakdowns:
                machine_breakdowns[machine_id] = []
            machine_breakdowns[machine_id].append(event)

        # Analyze each machine
        for machine_id, events in machine_breakdowns.items():
            machine_name = events[0].get("Entity_Name")
            breakdown_count = len(events)

            # Calculate days between breakdowns
            # Only possible if machine broke more than once
            avg_days_between = None
            days_since_last = None
            due_soon = None

            if breakdown_count >= 2:
                # Parse timestamps to calculate gaps
                timestamps = []
                for event in events:
                    try:
                        ts = datetime.strptime(
                            str(event.get("Timestamp")),
                            "%d-%b-%Y %H:%M"
                        )
                        timestamps.append(ts)
                    except ValueError:
                        continue

                if len(timestamps) >= 2:
                    timestamps.sort()
                    gaps = []
                    for i in range(1, len(timestamps)):
                        gap = (timestamps[i] - timestamps[i-1]).days
                        gaps.append(gap)

                    avg_days_between = sum(gaps) / len(gaps)

                    # Days since last breakdown
                    days_since_last = (
                        datetime.now() - timestamps[-1]
                    ).days

                    # Flag if approaching average breakdown cycle
                    if days_since_last >= (avg_days_between * 0.75):
                        due_soon = True

            patterns.append({
                "machine_id": machine_id,
                "machine_name": machine_name,
                "breakdown_counts": breakdown_count,
                "avg_days_between_breakdown": round(
                    avg_days_between, 1
                ) if avg_days_between else "Insufficient data",
                "days_since_last_breakdown": days_since_last,
                "maintenance_due_soon": due_soon,
                "message": (
                    f"{machine_name} has broken down "
                    f"{breakdown_count} time(s). "
                    f"Last breakdown: {days_since_last} days ago. "
                    f"{'⚠️ Maintenance recommended soon.' if due_soon else '✅ Within normal range.'}"
                )
            })

    except Exception as e:
        print(f"❌ Machine pattern analysis failed: {e}")

    return patterns

def analyze_vendor_patterns(spreadsheet):
    """
    Analyzes vendor delivery history.
    Finds: which vendors delay consistently
    Calculates: reliability score per vendor
    Alerts: consistently unreliable vendors
    Returns: list of pattern dictionaries
    """

    patterns = []

    try:
        # Get all vendor delay events
        delays = get_events_by_type(spreadsheet, "Vendor_Delay")
        deliveries = get_events_by_type(
            spreadsheet,
            "Vendor_Delivered"
        )

        if not delays and not deliveries:
            return []

        # Count delays per vendor
        delay_counts = Counter()
        vendor_names = {}

        for event in delays:
            vendor_id = event.get("Entity_ID")
            delay_counts[vendor_id] += 1
            vendor_names[vendor_id] = event.get("Entity_Name")

        # Count successful deliveries per vendor
        delivery_counts = Counter()
        for event in deliveries:
            vendor_id = event.get("Entity_ID")
            delivery_counts[vendor_id] += 1
            vendor_names[vendor_id] = event.get("Entity_Name")

        # Analyze each vendor
        all_vendor_ids = set(
            list(delay_counts.keys()) +
            list(delivery_counts.keys())
        )

        for vendor_id in all_vendor_ids:
            vendor_name = vendor_names.get(vendor_id, vendor_id)
            total_delays = delay_counts.get(vendor_id, 0)
            total_deliveries = delivery_counts.get(vendor_id, 0)
            total_orders = total_delays + total_deliveries

            # Calculate reliability percentage
            if total_orders > 0:
                reliability = round(
                    (total_deliveries / total_orders) * 100, 1
                )
            else:
                reliability = 0

            # Flag unreliable vendors
            unreliable = total_delays >= 2 or reliability < 70

            patterns.append({
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "total_delays": total_delays,
                "total_on_time": total_deliveries,
                "reliability_percentage": reliability,
                "flagged_unreliable": unreliable,
                "message": (
                    f"{vendor_name}: {total_delays} delay(s), "
                    f"{total_deliveries} on-time delivery(s). "
                    f"Reliability: {reliability}%. "
                    f"{'❌ Unreliable — consider alternate vendor.' if unreliable else '✅ Acceptable reliability.'}"
                )
            })

    except Exception as e:
        print(f"❌ Vendor pattern analysis failed: {e}")

    return patterns

def analyze_quality_patterns(spreadsheet):
    """
    Analyzes quality defect history.
    Finds: which defects repeat most
    Identifies: which stage has most defects
    Alerts: repeat defects on same part
    Returns: list of pattern dictionaries
    """

    patterns = []

    try:
        defects = get_events_by_type(
            spreadsheet,
            "Quality_Defect"
        )

        if not defects:
            return []

        # Count defects per part
        part_defects = Counter()
        defect_types = Counter()
        stage_defects = Counter()
        part_names = {}

        for event in defects:
            entity_id = event.get("Entity_ID")
            part_defects[entity_id] += 1
            part_names[entity_id] = event.get("Entity_Name")

            # Extract defect type from details
            details = event.get("Details", "")
            defect_types[details] += 1

        # Flag parts with repeat defects
        for part_id, count in part_defects.items():
            part_name = part_names.get(part_id, part_id)
            repeat = count >= 2

            patterns.append({
                "part_id": part_id,
                "part_name": part_name,
                "defect_count": count,
                "repeat_defect": repeat,
                "message": (
                    f"{part_name} has {count} defect(s) logged. "
                    f"{'⚠️ REPEAT DEFECT — possible process issue. Recommend QC inspection.' if repeat else '✅ Single occurrence.'}"
                )
            })

        # Most common defect types
        if defect_types:
            most_common = defect_types.most_common(3)
            patterns.append({
                "type": "common_defects",
                "data": most_common,
                "message": (
                    f"Most common defects: "
                    f"{', '.join([f'{d[0]} ({d[1]}x)' for d in most_common])}"
                )
            })

    except Exception as e:
        print(f"❌ Quality pattern analysis failed: {e}")

    return patterns

def analyze_material_patterns(spreadsheet):
    """
    Analyzes material consumption history.
    Finds: how fast each material is consumed
    Predicts: when reorder needed
    Alerts: materials running low based on trend
    Returns: list of pattern dictionaries
    """

    patterns = []

    try:
        low_events = get_events_by_type(
            spreadsheet,
            "Material_Low"
        )

        if not low_events:
            return []

        # Count how many times each material ran low
        material_counts = Counter()
        material_names = {}

        for event in low_events:
            entity_id = event.get("Entity_ID")
            material_counts[entity_id] += 1
            material_names[entity_id] = event.get("Entity_Name")

        for material_id, count in material_counts.items():
            material_name = material_names.get(
                material_id,
                material_id
            )
            frequent = count >= 2

            patterns.append({
                "material_id": material_id,
                "material_name": material_name,
                "low_stock_count": count,
                "frequent_shortage": frequent,
                "message": (
                    f"{material_name} has run low {count} time(s). "
                    f"{'⚠️ Frequent shortage — increase reorder quantity or frequency.' if frequent else '✅ Occasional shortage.'}"
                )
            })

    except Exception as e:
        print(f"❌ Material pattern analysis failed: {e}")

    return patterns


def get_all_patterns(spreadsheet):
    """
    Master function — runs all 4 analyzers.
    Returns combined pattern report for AI to use.
    """

    try:
        machine_patterns = analyze_machine_patterns(spreadsheet)
        vendor_patterns = analyze_vendor_patterns(spreadsheet)
        quality_patterns = analyze_quality_patterns(spreadsheet)
        material_patterns = analyze_material_patterns(spreadsheet)

        # Build summary for AI context
        summary = []

        if machine_patterns:
            summary.append("=== MACHINE PATTERNS ===")
            for p in machine_patterns:
                summary.append(f"  {p['message']}")

        if vendor_patterns:
            summary.append("\n=== VENDOR PATTERNS ===")
            for p in vendor_patterns:
                summary.append(f"  {p['message']}")

        if quality_patterns:
            summary.append("\n=== QUALITY PATTERNS ===")
            for p in quality_patterns:
                summary.append(f"  {p['message']}")

        if material_patterns:
            summary.append("\n=== MATERIAL PATTERNS ===")
            for p in material_patterns:
                summary.append(f"  {p['message']}")

        if not summary:
            summary.append(
                "No patterns detected yet. "
                "Patterns will emerge as more events are logged."
            )

        return {
            "machine_patterns": machine_patterns,
            "vendor_patterns": vendor_patterns,
            "quality_patterns": quality_patterns,
            "material_patterns": material_patterns,
            "summary": "\n".join(summary)
        }

    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        return {
            "machine_patterns": [],
            "vendor_patterns": [],
            "quality_patterns": [],
            "material_patterns": [],
            "summary": "Pattern analysis unavailable."
        }    