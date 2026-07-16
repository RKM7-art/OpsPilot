import streamlit as st
import time

# --- IMPORT YOUR BACKEND MODULES ---
from modules import sheets_connector
from modules import ai_engine

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OpsPilot | Sudarshan Gears",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (SaaS UI Styling) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            border: 1px solid #E4E7EC;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease-in-out;
        }
        
        div[data-testid="metric-container"]:hover {
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            border-color: #F97316;
        }
        
        .status-pill {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }
        .status-running { background-color: #DCFCE7; color: #166534; }
        .status-idle { background-color: #FEF3C7; color: #92400E; }
        .status-down { background-color: #FEE2E2; color: #991B1B; }
        
        .alert-badge {
            background-color: #DC2626;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            vertical-align: middle;
            margin-left: 10px;
        }

        .stChatMessage {
            border-radius: 10px;
            padding: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA FETCHING & CACHING (The Brains) ---
@st.cache_data(ttl=60)
def fetch_live_operations_data():
    try:
        # 1. Connect and fetch ALL data in one go
        spreadsheet = sheets_connector.connect_to_sheets()
        if not spreadsheet:
            return None
            
        all_data = sheets_connector.get_all_data(spreadsheet)
        
        # 2. Pass the correct extracted tabs into your check functions
        reorder_alerts = sheets_connector.check_reorder_alerts(all_data["material_ledger"])
        vendor_delays = sheets_connector.check_vendor_delays(all_data["vendors"])
        idle_machines = sheets_connector.check_idle_machines(all_data["machines"], all_data["production_jobs"])
        
        # 3. Calculate dynamic live metrics
        machines_running = sum(1 for m in all_data["machines"] if m.get("Current_Status") == "Running")
        total_machines = len(all_data["machines"]) if all_data["machines"] else 15
        
        # Negative filtering applied here
        active_jobs = sum(1 for j in all_data["production_jobs"] if j.get("Status") not in ["Completed", "Delivered", "Finished"])
        open_defects = len([q for q in all_data["quality_log"] if q.get("Decision") == "Pending"])
        
        total_alerts = len(reorder_alerts) + len(vendor_delays) + len(idle_machines)
        
        return {
            "all_data": all_data,
            "reorder_alerts": reorder_alerts,
            "vendor_delays": vendor_delays,
            "idle_machines": idle_machines,
            "metrics": {
                "machines_running": f"{machines_running}/{total_machines}",
                "active_jobs": str(active_jobs),
                "stock_alerts": str(len(reorder_alerts)),
                "open_defects": str(open_defects),
                "total_alerts": str(total_alerts)
            }
        }
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# Load the live data
live_data = fetch_live_operations_data()

# Fallback gracefully if Google Sheets fails
if not live_data:
    live_data = {
        "all_data": {"production_jobs": [], "machines": []},
        "reorder_alerts": [], "vendor_delays": [], "idle_machines": [],
        "metrics": {"machines_running": "0/15", "active_jobs": "0", "stock_alerts": "0", "open_defects": "0", "total_alerts": "0"}
    }

# --- 4. SESSION STATE FOR CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to OpsPilot. I am synced with Sudarshan Gears' live data. What do you need to check today?"}
    ]

# --- 5. MAIN LAYOUT ---
# Dynamic Header
st.markdown(f"<h2 style='font-weight: 700;'>⚙️ OpsPilot <span class='alert-badge'>{live_data['metrics']['total_alerts']} Alerts</span></h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; margin-top: -10px; font-size: 16px;'>AI Operations Assistant for Sudarshan Gears</p>", unsafe_allow_html=True)
st.divider()

col_dash, col_chat = st.columns([1.3, 1], gap="large")

with col_dash:
    st.markdown("<h3 style='font-weight: 600; margin-bottom: 20px;'>📊 Live Operations</h3>", unsafe_allow_html=True)
    
    # Live Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric(label="Machines Running", value=live_data["metrics"]["machines_running"])
    with m2: st.metric(label="Active Jobs", value=live_data["metrics"]["active_jobs"])
    with m3: st.metric(label="Stock Alerts", value=live_data["metrics"]["stock_alerts"])
    with m4: st.metric(label="Open Defects", value=live_data["metrics"]["open_defects"])
    
    st.write("")
    
    # Live Alerts 
    with st.expander("🚨 Active Alerts & Patterns", expanded=True):
        if live_data["reorder_alerts"] or live_data["vendor_delays"] or live_data["idle_machines"]:
            for alert in live_data["reorder_alerts"]:
                st.error(f"**Stock Critical:** {alert['message']}")
            for delay in live_data["vendor_delays"]:
                st.warning(f"**Vendor Delay:** {delay['message']}")
            for idle in live_data["idle_machines"]:
                st.error(f"**Idle Machine:** {idle['message']}")
        else:
            st.success("No active alerts at this time. Production is running smoothly.")
        
    with st.expander("🏭 Machine Status Floor", expanded=True):
        if live_data["all_data"]["machines"]:
            for machine in live_data["all_data"]["machines"]:
                status = machine.get('Current_Status', 'Unknown')
                badge_class = "status-running" if status == "Running" else "status-idle" if status == "Idle" else "status-down"
                st.markdown(f"- **{machine.get('Machine_ID')} ({machine.get('Machine_Name')}):** <span class='status-pill {badge_class}'>{status}</span> — Operator: {machine.get('Operator_Name')}", unsafe_allow_html=True)
        else:
            st.write("No machine data available.")
        
    with st.expander("📦 Active Job Progress"):
        # Dynamically draw progress bars based on sheet data
        # Negative filtering applied here too
        active_jobs_list = [j for j in live_data["all_data"]["production_jobs"] if j.get("Status") not in ["Completed", "Delivered", "Finished"]]
        if active_jobs_list:
            for job in active_jobs_list[:3]: # Show top 3 jobs
                st.write(f"**Job {job.get('Job_ID')} ({job.get('Part_Name')})**")
                # Estimate progress: Assuming Stage 1 to 5 mapping
                stage_str = str(job.get('Current_Stage', 'Stage 1'))
                stage_num = int(stage_str.split(' ')[1]) if 'Stage' in stage_str and len(stage_str.split(' ')) > 1 else 1
                progress_pct = min(stage_num * 20, 100)
                st.progress(progress_pct, text=f"{stage_str} ({progress_pct}% Complete) — Assigned to {job.get('Assigned_To')}")
        else:
            st.write("No active jobs currently in progress.")

with col_chat:
    st.markdown("<h3 style='font-weight: 600; margin-bottom: 20px;'>💬 Ops Assistant</h3>", unsafe_allow_html=True)
    
    chat_container = st.container(height=600, border=True)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    # Chat Input 
    if prompt := st.chat_input("Ask about jobs, machines, or materials..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Analyzing operations data..."):
                    try:
                        # Grab fresh connection specifically for the AI engine
                        ai_spreadsheet = sheets_connector.connect_to_sheets()
                        
                        # Pass BOTH required arguments perfectly
                        response = ai_engine.process_query(prompt, ai_spreadsheet)
                        st.markdown(response)
                    except Exception as e:
                        response = f"I encountered an error connecting to my brain: {e}"
                        st.error(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()