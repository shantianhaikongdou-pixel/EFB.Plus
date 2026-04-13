import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import time
from streamlit_drawable_canvas import st_canvas

# --- 1. CHECKLIST DATABASE ---
cl_db = {
    "A350": {
        "COCKPIT PREP": ["PARKING BRAKE - SET", "ALL BATTERY SWITCH - ON", "EXTERNAL POWER - PUSH", "ADIRS (1, 2, 3) - NAV", "CREW SUPPLY - ON", "PACKS - AUTO", "NAV LIGHTS - ON", "LOGO LIGHTS - ON", "APU - MASTER-START", "NO SMOKING - AUTO", "NO MOBILE - AUTO", "EMERGENCY LIGHTS - ARMED", "FLIGHT DIRECTORS - ON", "ALTIMETERS - SET", "MCDU - SETUP", "FLT CTL PAGE - CHECK"],
        "BEFORE START": ["WINDOWS/DOORS - CLOSED", "BEACON - ON", "THRUST LEVERS - IDLE", "FUEL PUMPS - ON", "TRANSPONDER - AS REQ"],
        "AFTER START": ["ENGINE MODE SELECTOR - NORM", "PITCH TRIM - SET", "AUTOBRAKE - MAX", "FLAPS - SET", "GND SPOILERS - ARMED", "APU - OFF", "FLIGHT CONTROLS - CHECKED", "RUDDER TRIM - ZERO", "ANTI-ICE - AS REQ"],
        "TAXI/TAKEOFF": ["GROUND EQUIPMENT - CLEAR", "NOSEWHEEL LIGHTS - TAXI", "BRAKES - CHECK", "AUTO THRUST - BLUE", "TCAS - TA/RA", "PACKS - OFF/ON"],
        "CRUISE": ["ALTIMETERS - STD", "ANTI-ICE - AS REQ", "ECAM MEMO - CHECKED"],
        "DESCENT/APPROACH": ["CABIN CREW - ADVISED", "ND TERRAIN - AS REQ", "APPROACH BUTTON - ARM", "APPR PHASE (MCDU) - ACTIVATE", "LANDING GEAR - DOWN"],
        "LANDING": ["GND SPOILERS - ARM", "ENG MODE SELECTOR - AS REQ", "AUTOBRAKE - AS REQ", "FLAPS - SET LDG", "GO AROUND ALTITUDE - SET", "ECAM MEMO - LDG NO BLUE"],
        "SHUTDOWN/SECURE": ["PARKING BRAKE - SET", "APU - START", "ENG 1 & 2 MASTER - OFF", "BEACON LIGHTS - OFF", "FLIGHT DIRECTORS - OFF", "PASSENGER SIGNS - OFF", "SLIDES - DISARM", "FUEL PUMPS - OFF", "DOORS - OPEN", "ADIRS - OFF", "EMERGENCY LIGHTS - OFF", "NAV/LOGO LIGHTS - OFF", "EXTERNAL POWER - OFF", "BATTERY - OFF"]
    },
    "B787": {
        "ELECTRICAL POWERUP": ["SERVICE INTERPHONE - OFF", "BACKUP WINDOW HEAT - ON", "PRIMARY WINDOW HEAT - ON", "ENGINE PRIMARY PUMP L&R - ON", "C1 & C2 ELEC PUMP - OFF", "L & R DEMAND PUMP - OFF", "SEAT BELT SIGNS - ON", "APU FIRE PANEL - SET", "CARGO FIRE ARM - NORM", "ENGINE EEC MODE - NORM", "FUEL JETTISON - OFF", "WING/ENGINE ANTI-ICE - AUTO"],
        "BEFORE START": ["FLIGHT DECK DOOR - CLOSED/LOCKED", "PASSENGER SIGNS - ON", "MCP - SET", "FMS - COMPLETED", "BEACON - ON"],
        "AFTER START/TAXI": ["FLAPS - SET", "AUTOBRAKE - RTO", "FLIGHT CONTROLS - CHECKED"],
        "CLIMB/CRUISE": ["LANDING GEAR - UP", "FLAPS - UP", "ALTIMETERS - STD", "ANTI-ICE - AS REQ"],
        "DESCENT": ["PRESSURIZATION (LDG ALT) - SET", "RECALL - CHECKED", "AUTOBRAKE - SET", "LANDING DATA (VREF) - VERIFY", "APPROACH BRIEFING - COMPLETE"],
        "APPROACH/LANDING": ["ALTIMETER - RESET TO LOCAL", "SPEED - 250 KIAS (BELOW 10k)", "LANDING LIGHTS - ON", "SEAT BELTS - ON"],
        "SHUTDOWN/POWER DOWN": ["PARKING BRAKE - SET", "APU - VERIFY RUNNING", "FUEL CONTROL SWITCHES - CUTOFF", "SEAT BELT SIGNS - OFF", "FUEL PUMPS - OFF", "BEACON LIGHT - OFF", "IRS SELECTORS - OFF", "FD DOOR POWER - OFF"]
    },
    "A320/321": {
        "COCKPIT PREP": ["GEAR PINS and COVERS - REMOVED", "FUEL QUANTITY - KG CHECK", "SIGNS - ON/AUTO", "ADIRS - NAV", "BARO REF - SET (BOTH)"],
        "BEFORE START": ["PARKING BRAKE - SET", "T.O SPEEDS & THRUST - BOTH SET", "WINDOWS/DOORS - CLOSED", "BEACON - ON"],
        "AFTER START": ["APU - OFF", "Y ELEC PUMP - OFF", "ANTI ICE - AS REQ", "PITCH TRIM - SET", "RUDDER TRIM - ZERO"],
        "APPROACH": ["BARO REF - SET", "SEAT BELTS - ON", "MINIMUM - SET", "ENG MODE SEL - AS REQ"],
        "LANDING": ["G/A ALTITUDE - SET", "CABIN CREW - ADVISED", "ECAM MEMO - LDG NO BLUE", "LDG GEAR - DOWN", "SPLRS - ARM", "FLAPS - SET"],
        "PARKING/SECURE": ["PARKING BRAKE - SET", "ENGINES - OFF", "FUEL PUMPS - OFF", "ADIRS - OFF", "EXT PWR - AS REQ"]
    },
    "B777": {
        "PREFLIGHT": ["ADIRU Switch - ON", "Emergency Exit Lights - ARMED", "Hydraulic Panel - SET", "Electrical Panel - SET", "Packs - ON", "FMC - SETUP"],
        "BEFORE START": ["Flight Deck Door - CLOSED", "Passenger Signs - ON", "MCP - SET", "Takeoff Speeds - SET", "Beacon - ON"],
        "AFTER START/TAXI": ["Anti-ice - AS REQ", "Recall - CHECKED", "Autobrake - RTO", "Flaps - SET", "Flight Controls - CHECKED"],
        "BEFORE TAKEOFF": ["Transponder - TA/RA", "Strobe Lights - ON"],
        "CRUISE": ["Altimeters - STD", "FMC/Fuel - CHECKED"],
        "DESCENT/APPROACH": ["Altimeters - QNH SET", "Landing Data - SET", "Autobrake - SET"],
        "SHUTDOWN": ["Hydraulic Panel - SET", "Fuel Pumps - OFF", "Flaps - UP", "Parking Brake - AS REQ", "Fuel Control Switches - CUTOFF", "Weather Radar - OFF"],
        "SECURING": ["ADIRU Switch - OFF", "Emergency Exit Lights - OFF", "Packs Switches - OFF", "APU - OFF"]
    },
    "B767": {
        "PREFLIGHT": ["Oxygen - TESTED", "IRS - OFF TO NAV", "HYDRAULIC PANEL - SET", "WINDOW HEAT - ON", "THROTTLES - IDLE", "GEAR PIN - REMOVED", "PARKING BRAKE - SET"],
        "BEFORE START": ["FUEL - KGS/PUMPS ON", "WINDOWS - CLOSED/LOCKED", "PASSENGER SIGNS - ON", "DOORS - CLOSED & ARMED"],
        "AFTER START": ["PROBE HEAT - ON", "ANTI-ICE - AS REQ", "ISOLATION VALVE - OFF", "FUEL CTRL - RUN & LOCKED"],
        "BEFORE TAXI": ["RECALL - CHECKED", "FLT CTRLS - CHECKED", "FLAPS - SET", "AUTOBRAKE - RTO"],
        "AFTER TAKEOFF": ["LANDING GEAR - UP & OFF", "FLAPS - UP", "ALTIMETERS - SET STD"],
        "DESCENT/APPROACH": ["LDG ALT - SET", "PASSANGER SIGNS - ON", "RECALL - CHECKED", "AUTOBRAKE - SET", "VREF/MINIMUMS - SET", "ALTIMETERS - QNH SET"],
        "LANDING": ["CABIN - SECURED", "SPEEDBRAKE - ARMED", "LANDING GEAR - DOWN", "FLAPS - SET"],
        "AFTER LANDING": ["ANTI-ICE - AS REQ", "APU - STARTED", "AUTOBRAKE - OFF", "SPEEDBRAKE - DOWN", "FLAPS - UP", "WEATHER RADAR - OFF"]
    },
    "A330": {
        "COCKPIT PREP": ["GEAR PINS & COVERS - REMOVED", "FUEL QUANTITY - CHECK", "SEAT BELTS - ON", "ADIRS - NAV", "BARO REF - BOTH SET"],
        "BEFORE START": ["T.O SPEEDS & THRUST - BOTH SET", "WINDOWS - CLOSED", "BEACON - ON", "PARKING BRAKE - SET"],
        "AFTER START": ["ANTI ICE - AS REQ", "ECAM STATUS - CHECKED", "PITCH TRIM - SET", "RUDDER TRIM - CHECKED"],
        "APPROACH": ["BARO REF - BOTH SET", "SEAT BELTS - ON", "MINIMUM - SET", "AUTO BRAKE - SET", "ENG START SEL - AS REQ"],
        "LANDING": ["ECAM MEMO - LDG NO BLUE", "GEAR - DOWN", "FLAPS - SET"],
        "AFTER LANDING": ["RADAR & PRED W/S - OFF", "SPOILERS - DISARM", "FLAPS - RETRACT", "APU - START"],
        "PARKING": ["PARKING BRAKE/CHOCKS - SET", "ENGINES - OFF", "FUEL PUMPS - OFF"]
    },
    "HondaJet": {
        "CDU SETUP": ["Database Status - CONNECT", "Avionics Settings - AS DESIRED", "Flight Plan - ENTER/VERIFY"],
        "BEFORE START": ["ATC Clearance - OBTAIN", "Transponder - SQUAWK SET", "Alt Select - SET CLEARED ALT", "Parking Brake - SET", "Battery - ON", "External Power - AS REQ"],
        "ENGINE START": ["Doors - CLOSED", "Parking Brake - SET", "CAS Messages - REVIEW", "Elec Volts - MIN 23.5V", "Engine Start Button - PUSH"],
        "AFTER START/TAXI": ["External Power - DISCONNECT", "Lights - AS REQ", "Flaps - TAKE OFF", "Trim - SET (GREEN)"],
        "CRUISE": ["Altimeter - STD", "Ice Protection - AS REQ", "Fuel - MONITOR"],
        "LANDING": ["Landing Gear - DOWN & 3 GREEN", "Flaps - LDG", "Yaw Damper - OFF @50ft", "Throttles - IDLE @Threshold"],
        "SHUTDOWN": ["Parking Brake - SET", "Engines - OFF", "Electrical - OFF"]
    }
}

# --- 2. PAGE STYLES (究極の無機質・業務用) ---
st.set_page_config(page_title="WebAIMS OPERA", layout="wide")

st.markdown("""
    <style>
    /* 全体: コクピット内EFBの質感 */
    html, body, [class*="css"] {
        font-family: 'Courier New', Courier, monospace !important;
        background-color: #1a1a1a !important;
        color: #ddd !important;
        font-size: 13px !important;
    }
    .block-container { padding: 0 !important; }

    /* ステータスバー */
    .opera-header {
        background-color: #00256e; color: white;
        padding: 5px 15px; font-weight: bold;
        border-bottom: 2px solid #000;
        display: flex; justify-content: space-between;
    }

    /* サイドバー: 暗色で無機質に */
    [data-testid="stSidebar"] {
        background-color: #222 !important;
        border-right: 1px solid #444;
    }
    .stButton>button {
        border-radius: 0 !important; border: 1px solid #555 !important;
        background-color: #333 !important; color: #fff !important;
        width: 100%; font-weight: bold; margin-bottom: 5px;
    }
    .stButton>button:hover { border-color: #00256e !important; background-color: #444 !important; }

    /* OFP PAPER: 画像通りの白い紙を再現 */
    .ofp-paper {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 40px 50px;
        margin: 20px auto;
        width: 95%;
        max-width: 850px;
        line-height: 1.2;
        white-space: pre;
        box-shadow: 10px 10px 20px rgba(0,0,0,0.8);
        border: 1px solid #888;
        overflow-x: auto;
    }

    /* ツールエリア */
    .bottom-tools {
        background-color: #111;
        padding: 20px;
        border-top: 2px solid #333;
    }
    .stCheckbox { margin-bottom: -10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC ---
def get_val(data, *keys):
    """辞書から安全にデータを抽出"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, "---")
        else:
            return "---"
    return data if data is not None else "---"

def fetch_simbrief(user_id):
    try:
        res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&json=1")
        return res.json() if res.status_code == 200 else None
    except: return None

def generate_ofp_text(sb):
    now = datetime.utcnow()
    rel_time = now.strftime("%d%H%M %b%y").upper()
    gen_time_raw = get_val(sb, 'params', 'time_generated')
    gen_time = datetime.fromtimestamp(int(gen_time_raw)).strftime("%d%b%y").upper() if gen_time_raw != "---" else "---"
    
    # 燃料・時間計算の安全化
    trip_f = get_val(sb, 'fuel', 'enroute_burn')
    trip_t_sec = get_val(sb, 'times', 'est_time_enroute')
    trip_t = time.strftime('%H%M', time.gmtime(int(trip_t_sec))) if trip_t_sec != "---" else "---"
    
    text = f"""[ OFP ] -----------------------------------------------------------
{get_val(sb, 'atc', 'callsign')}   {gen_time}   {get_val(sb, 'origin', 'icao_code')}-{get_val(sb, 'destination', 'icao_code')}   {get_val(sb, 'aircraft', 'icao_code')} {get_val(sb, 'aircraft', 'reg')}   RELEASE {rel_time}
OFP 0   {get_val(sb, 'origin', 'name').upper()}-{get_val(sb, 'destination', 'name').upper()}
--------------------------------------------------------------------
ATC C/S   {get_val(sb, 'atc', 'callsign')}      {get_val(sb, 'origin', 'icao_code')}/{get_val(sb, 'origin', 'iata_code')}   {get_val(sb, 'destination', 'icao_code')}/{get_val(sb, 'destination', 'iata_code')}      CI {get_val(sb, 'general', 'costindex')}
{gen_time}   {get_val(sb, 'aircraft', 'reg')}         {get_val(sb, 'times', 'est_out')[7:11]}/{get_val(sb, 'times', 'sched_out')[7:11]}  {get_val(sb, 'times', 'est_in')[7:11]}/{get_val(sb, 'times', 'sched_in')[7:11]}
--------------------------------------------------------------------
FUEL            ARPT   FUEL   TIME
---------------------------------
TRIP             {get_val(sb, 'destination', 'iata_code')}  {trip_f}   {trip_t}
CONT {get_val(sb, 'fuel', 'contingency_p')}%             {get_val(sb, 'fuel', 'contingency')}   {time.strftime('%H%M', time.gmtime(int(get_val(sb, 'times', 'contingency_time')))) if get_val(sb, 'times', 'contingency_time') != "---" else "---"}
ALTN             {get_val(sb, 'alternate', 0, 'iata_code')}  {get_val(sb, 'fuel', 'alternate_burn')}   {time.strftime('%H%M', time.gmtime(int(get_val(sb, 'times', 'alternate_time')))) if get_val(sb, 'times', 'alternate_time') != "---" else "---"}
FINRES                {get_val(sb, 'fuel', 'reserve')}   {time.strftime('%H%M', time.gmtime(int(get_val(sb, 'times', 'reserve_time')))) if get_val(sb, 'times', 'reserve_time') != "---" else "---"}
---------------------------------
MINIMUM T/OFF FUEL   {get_val(sb, 'fuel', 'min_takeoff')}
TAXI             {get_val(sb, 'origin', 'iata_code')}  {get_val(sb, 'fuel', 'taxi')}
BLOCK FUEL       {get_val(sb, 'origin', 'iata_code')}  {get_val(sb, 'fuel', 'plan_block')}
--------------------------------------------------------------------
ROUTING:
{get_val(sb, 'origin', 'icao_code')}/{get_val(sb, 'origin', 'plan_rwy')} {get_val(sb, 'general', 'route')} {get_val(sb, 'destination', 'icao_code')}/{get_val(sb, 'destination', 'plan_rwy')}
--------------------------------------------------------------------
DISPATCHER: PATRICIA MITCHELL        PIC: MIKUTO / TAJIMA
--------------------------------------------------------------------"""
    return text

# --- 4. MAIN INTERFACE ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'ofp_text' not in st.session_state: st.session_state['ofp_text'] = None

if not st.session_state['authenticated']:
    st.markdown("<div class='opera-header'><span>LOGIN REQUIRED</span></div>", unsafe_allow_html=True)
    if st.text_input("ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    # Sidebar
    with st.sidebar:
        st.markdown("### DATA INPUT")
        sb_id = st.text_input("SimBrief ID", value="906331")
        if st.button("LOAD FLIGHT PLAN"):
            with st.spinner("FETCHING..."):
                data = fetch_simbrief(sb_id)
                if data:
                    st.session_state['sb_json'] = data
                    st.session_state['ofp_text'] = generate_ofp_text(data)
                else: st.error("FAILED")
        
        st.markdown("---")
        st.markdown("### T/D CALC")
        fl = st.number_input("CRZ FL", 350)
        tgt = st.number_input("TGT ALT", 3000)
        gs = st.number_input("GS", 450)
        dist = ((fl*100-tgt)/1000)*3
        st.markdown(f"DIST: **{dist:.1f} NM** | V/S: **-{gs*5}**")

    # Top Bar
    st.markdown("<div class='opera-header'><span>WebAIMS OPERA | EFB PLUS</span><span>UNIT: LBS / UTC</span></div>", unsafe_allow_html=True)

    # Main OFP
    if st.session_state['ofp_text']:
        st.markdown(f"<div class='ofp-paper'>{st.session_state['ofp_text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='ofp-paper'>AWAITING SIMBRIEF DATA...</div>", unsafe_allow_html=True)

    # Tools
    st.markdown("<div class='bottom-tools'>", unsafe_allow_html=True)
    col_cl, col_sp = st.columns([2, 1])
    
    with col_cl:
        st.markdown("**[ CHECKLIST ]**")
        sb_data = st.session_state.get('sb_json')
        # 機体タイプ自動判定、なければデフォルトB787
        raw_ac = get_val(sb_data, 'aircraft', 'icao_code')
        cur_ac = raw_ac if raw_ac in cl_db else "B787"
        
        sel_ac = st.selectbox("SELECT AIRCRAFT", list(cl_db.keys()), index=list(cl_db.keys()).index(cur_ac))
        
        phases = list(cl_db[sel_ac].keys())
        # フェーズ切り替え
        cols = st.columns(len(phases))
        if 'cur_phase' not in st.session_state or st.session_state.get('last_ac') != sel_ac:
            st.session_state['cur_phase'] = phases[0]
            st.session_state['last_ac'] = sel_ac

        for i, ph in enumerate(phases):
            if cols[i].button(ph): st.session_state['cur_phase'] = ph
            
        st.markdown(f"--- {sel_ac} / {st.session_state['cur_phase']} ---")
        for item in cl_db[sel_ac][st.session_state['cur_phase']]:
            st.checkbox(item, key=f"check_{sel_ac}_{item}")

    with col_sp:
        st.markdown("**[ SCRATCH PAD ]**")
        st_canvas(stroke_width=2, stroke_color="black", background_color="#fff", height=250, key="pad")
    
    st.markdown("</div>", unsafe_allow_html=True)
