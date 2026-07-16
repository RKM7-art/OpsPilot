import sys
import os

# STEP 1: Change to project root first
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# STEP 2: Load .env immediately after chdir
from dotenv import load_dotenv
load_dotenv(override=True)

print("OpenAI Key loaded:", "YES" if os.getenv("OPENAI_API_KEY") else "NO")

# STEP 3: Now import modules (they will see the env vars)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from modules.sheets_connector import (
    connect_to_sheets,
    get_all_data,
    check_reorder_alerts,
    check_vendor_delays,
    check_idle_machines
)
from modules.ai_engine import process_query
from modules.event_logger import log_event

app = FastAPI(title="OpsPilot Command Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

print("Initializing Google Sheets connection...")
spreadsheet = connect_to_sheets()
print("System Online.")


class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    gearbox_context: Optional[str] = None
    role: Optional[str] = "manager"
    history: Optional[list[ChatMessage]] = None


class LogEventRequest(BaseModel):
    event_type: str
    entity_id: str
    entity_name: str
    details: str
    reported_by: str
    shift: Optional[str] = "Morning"
    action_taken: Optional[str] = "Pending"

class UpdateSheetRequest(BaseModel):
    sheet_name: str
    id_column: str
    id_value: str
    update_column: str
    new_value: str


@app.get("/api/dashboard")
def get_dashboard():
    try:
        data = get_all_data(spreadsheet)
        alerts = {
            "reorder": check_reorder_alerts(data.get("material_ledger", [])),
            "vendor_delays": check_vendor_delays(data.get("vendors", [])),
            "idle_machines": check_idle_machines(
                data.get("machines", []),
                data.get("production_jobs", [])
            )
        }
        return {
            "machines": data["machines"],
            "production_jobs": data["production_jobs"],
            "material_ledger": data["material_ledger"],
            "vendors": data["vendors"],
            "quality_log": data["quality_log"],
            "gearbox_assembly": data.get("gearbox_assembly", []),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gearboxes")
def get_gearboxes():
    try:
        data = get_all_data(spreadsheet)
        return {"gearboxes": data.get("gearbox_assembly", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gearbox/{gearbox_id}")
def get_gearbox_dashboard(gearbox_id: str):
    try:
        data = get_all_data(spreadsheet)
        gearboxes = data.get("gearbox_assembly", [])

        gearbox = next(
            (g for g in gearboxes if g["Gearbox_ID"] == gearbox_id),
            None
        )
        if not gearbox:
            raise HTTPException(status_code=404, detail="Gearbox not found")

        job_ids = [
            j.strip()
            for j in gearbox.get("Part_Job_IDs", "").split(",")
        ]

        jobs = [
            j for j in data.get("production_jobs", [])
            if j.get("Job_ID") in job_ids
        ]
        machines = [
            m for m in data.get("machines", [])
            if m.get("Current_Job_ID") in job_ids
        ]
        part_codes = [j.get("Part_Code") for j in jobs]
        quality = [
            q for q in data.get("quality_log", [])
            if q.get("Part_Code") in part_codes
        ]

        completed = sum(1 for j in jobs if j.get("Status") == "Completed")
        total = len(jobs)
        completion_pct = round((completed / total * 100) if total > 0 else 0)

        alerts = {
            "reorder": check_reorder_alerts(data.get("material_ledger", [])),
            "vendor_delays": check_vendor_delays(data.get("vendors", [])),
            "idle_machines": check_idle_machines(
                data.get("machines", []),
                data.get("production_jobs", [])
            )
        }

        return {
            "gearbox": gearbox,
            "jobs": jobs,
            "machines": machines,
            "quality": quality,
            "vendors": data.get("vendors", []),
            "material_ledger": data.get("material_ledger", []),
            "alerts": alerts,
            "completion_pct": completion_pct
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        # Convert Pydantic history models into the plain {"role","content"}
        # dicts process_query/get_ai_response expect.
        history = [{"role": h.role, "content": h.content} for h in req.history] if req.history else None

        response = process_query(
            req.message,
            spreadsheet,
            gearbox_context=req.gearbox_context,
            role=req.role,
            history=history
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/log-event")
def log_event_endpoint(req: LogEventRequest):
    try:
        event_id = log_event(
            spreadsheet,
            req.event_type,
            req.entity_id,
            req.entity_name,
            req.details,
            req.reported_by,
            req.shift,
            action_taken=req.action_taken
        )
        if event_id:
            return {"success": True, "event_id": event_id}
        return {"success": False, "error": "Failed to log event"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@app.post("/api/update-sheet")
def update_sheet(req: UpdateSheetRequest):
    try:
        from modules.sheets_connector import update_by_id
        success = update_by_id(
            spreadsheet,
            req.sheet_name,
            req.id_column,
            req.id_value,
            req.update_column,
            req.new_value
        )
        if success:
            return {"success": True, "message": f"Updated {req.update_column} for {req.id_value} in {req.sheet_name}"}
        return {"success": False, "error": f"Could not find {req.id_value} in {req.sheet_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}