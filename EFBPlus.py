import streamlit as st
from datetime import datetime
import requests
import time
from streamlit_drawable_canvas import st_canvas

# --- 1. FULL CHECKLIST DATABASE (みくとのリストを完全統合) ---
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

# --- 2. STYLING (プロ仕様・柔軟レイアウト) ---
st.set_page_config(page_title="G3 OPERA EFB", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #080808; color: #ffffff; }
    
    /* ヘッダー */
    .header-bar {
        background-color: #00256e; padding: 10px 20px;
        display: flex; justify-content: space-between;
        border-bottom: 2px solid #000; font-weight: bold;
    }

    /* 各セクションのコンテナ */
    .pane {
        background: #121212; border: 1px solid #333;
        border-radius: 5px; padding: 15px; height: 82vh; overflow-y: auto;
    }

    /* OFP用紙 */
    .ofp-paper {
        background: #fff; color: #000; padding: 25px;
        font-family: 'Courier New', monospace; font-size: 13px;
        line-height: 1.2; white-space: pre; border-radius: 3px;
    }

    /* ボタン類 */
    .stButton>button {
        width: 100%; border-radius: 0; background: #222; color: #00e5ff; border: 1px solid #444;
    }
    .stButton>button:hover { background: #00e5ff; color: #000; }
    
    /* チェックボックス */
    .stCheckbox { padding: 5px 0; border-bottom: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MAIN UI ---
st.markdown('<div class="header-bar"><span>G3 EFB OPERATOR</span><span>MIKUTO TAJIMA | UTC ' + datetime.utcnow().strftime("%H:%M") + '</span></div>', unsafe_allow_html=True)

col_left, col_mid, col_right = st.columns([1, 2, 1.2])

# --- 左ペイン: データ接続 & TOD ---
with col_left:
    st.markdown('<div class="pane">', unsafe_allow_html=True)
    st.subheader("SYSTEM LINK")
    sb_id = st.text_input("SimBrief ID", "906331")
    if st.button("CONNECT / REFRESH"):
        try:
            r = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={sb_id}&json=1")
            st.session_state['sb'] = r.json()
        except: st.error("CONNECTION FAILED")
    
    st.markdown("---")
    st.subheader("TOD CALC")
    fl = st.number_input("CRZ FL", 100, 450, 350)
    tgt = st.number_input("TGT ALT", 0, 40000, 3000)
    dist = ((fl*100 - tgt)/1000) * 3
    st.info(f"DESCENT DIST: {dist:.1f} NM")
    
    st.markdown("---")
    st.subheader("MEMO")
    st_canvas(stroke_width=2, stroke_color="#00e5ff", background_color="#000", height=150, key="pad")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 中央ペイン: OFP表示 ---
with col_mid:
    st.markdown('<div class="pane">', unsafe_allow_html=True)
    if 'sb' in st.session_state:
        sb = st.session_state['sb']
        ofp = f"""
{sb['atc']['callsign']}   {sb['aircraft']['icao_code']}   {sb['aircraft']['reg']}
{sb['origin']['icao_code']} -> {sb['destination']['icao_code']}

CI: {sb['general']['costindex']}   FL: {sb['general']['initial_altitude']}
--------------------------------------------------
FUEL (LBS)
TRIP:    {sb['fuel']['enroute_burn']}
ALTN:    {sb['fuel']['alternate_burn']}
RESV:    {sb['fuel']['reserve']}
BLOCK:   {sb['fuel']['plan_block']}
--------------------------------------------------
ROUTE:
{sb['general']['route']}
        """
        st.markdown(f'<div class="ofp-paper">{ofp}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ofp-paper">AWAITING SYSTEM LINK...</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 右ペイン: 全機体・全フェーズ対応チェックリスト ---
with col_right:
    st.markdown('<div class="pane">', unsafe_allow_html=True)
    st.subheader("CHECKLIST")
    
    # 機体選択（SimBriefの機体コードを自動選択、なければ手動）
    auto_ac = st.session_state.get('sb', {}).get('aircraft', {}).get('icao_code', "A350")
    if auto_ac not in cl_db: auto_ac = "B787"
    
    sel_ac = st.selectbox("AIRCRAFT TYPE", list(cl_db.keys()), index=list(cl_db.keys()).index(auto_ac))
    
    # フェーズ選択
    phases = list(cl_db[sel_ac].keys())
    sel_phase = st.selectbox("FLIGHT PHASE", phases)
    
    st.markdown(f"**--- {sel_ac} / {sel_phase} ---**")
    
    # リスト表示
    for item in cl_db[sel_ac][sel_phase]:
        st.checkbox(item, key=f"cl_{sel_ac}_{sel_phase}_{item}")
        
    if st.button("CLEAR ALL"):
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
