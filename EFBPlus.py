import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import requests
import re
import time
import math
from streamlit_drawable_canvas import st_canvas

# --- 1. Database & Configuration ---
SB_USER = "906331"

# 完全版チェックリストDB（絵文字なし）
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

# --- 2. Page Config & Styles ---
st.set_page_config(page_title="EFBPlus | OPERA", layout="wide")

# CSS to make the app look like the OFP image (Monospace, no padding)
st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #f4f4f4; color: black; }
    
    /* Monospace font for everything */
    html, body, [class*="css"] {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 13px !important;
    }

    /* OFP Header - ANA Style */
    .ofp-header {
        background-color: #003194; color: white;
        padding: 5px 10px; font-weight: bold;
        display: flex; justify-content: space-between;
    }

    /* Remove padding and borders for main area */
    .block-container { padding: 0 !important; }
    
    /* Fix Sidebar to monospace and white background */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid #ccc;
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #003194 !important; color: white !important;
        font-family: monospace; border-radius: 0;
    }
    
    /* Input Styling */
    .stTextInput input {
        font-family: monospace; border-radius: 0; border: 1px solid #ccc;
    }
    
    /* OFP Text Area - Exactly as image */
    .ofp-text {
        background-color: white; padding: 10px;
        white-space: pre; overflow-x: auto;
        line-height: 1.2; border-bottom: 2px solid black;
    }
    
    /* Calculator / Checklist Area */
    .tool-area { background-color: white; padding: 10px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Session State Management ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'sb_json' not in st.session_state: st.session_state['sb_json'] = None
if 'ofp_text' not in st.session_state: st.session_state['ofp_text'] = None

# --- 4. Logic Functions ---
def fetch_simbrief(user_id):
    res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&json=1")
    return res.json() if res.status_code == 200 else None

def generate_ofp_text(sb):
    # Get current timestamp for release time
    now = datetime.utcnow()
    release_time = now.strftime("%d%H%M %b%y").upper()
    flight_date = datetime.fromtimestamp(int(sb['params']['time_generated'])).strftime("%d%b%y").upper()

    # Get ETOPS airports (handles lists or single entry)
    etops_apts = sb.get('etops', {}).get('alternates', [])
    if isinstance(etops_apts, str): etops_apts = [etops_apts]
    etops_apt_str = " ".join(etops_apts)

    text = f"""[ OFP ]
--------------------------------------------------------------------
{sb['atc']['callsign']}   {flight_date}   {sb['origin']['icao_code']}-{sb['destination']['icao_code']}   {sb['aircraft']['icao_code']} {sb['aircraft']['reg']}   RELEASE {release_time}
OFP 0   {sb['origin']['name'].upper()}-{sb['destination']['name'].upper()}
                WX PROG {sb['times']['sched_out'][7:11]} OBS ...

 ATC C/S   {sb['atc']['callsign']}      {sb['origin']['icao_code']}/{sb['origin']['iata_code']}   {sb['destination']['icao_code']}/{sb['destination']['iata_code']}      CRZ SYS      CI {sb['general']['costindex']}
{flight_date}   {sb['aircraft']['reg']}         {sb['times']['est_out'][7:11]}/{sb['times']['sched_out'][7:11]}  {sb['times']['est_in'][7:11]}/{sb['times']['sched_in'][7:11]}      GND DIST      {sb['general']['route_distance']}
{sb['aircraft']['icao_code']} /                      STA  {sb['times']['sched_in'][7:11]}      AIR DIST      {sb['general']['air_distance']}
                                  CTOT:....                G/C DIST      0
                                                           AVG WIND   {sb['general']['avg_wind_dir']}/{sb['general']['avg_wind_speed']}
MAXIMUM   TOW {sb['weights']['max_takeoff_weight']}  LAW {sb['weights']['max_landing_weight']}  ZFW {sb['weights']['max_zfw']}      AVG W/C      {sb['general']['avg_wind_comp']}
ESTIMATED TOW {sb['weights']['est_takeoff_weight']}  LAW {sb['weights']['est_landing_weight']}  ZFW {sb['weights']['est_zfw']}      AVG ISA      {sb['general']['avg_isa_dev']}
                                                           AVG FF LB/HR ...
                                                           FUEL BIAS    P00.0
ALTN {sb['alternate'][0]['icao_code'] if sb.get('alternate') else 'NONE'}                                                           TKOF ALTN    ...
FL STEPS ...
--------------------------------------------------------------------
                       *** {sb['general']['flight_type'].upper()} FLIGHT ***
--------------------------------------------------------------------
DISP RMKS  SAYINTENTIONS.AI TEST FLIGHTNH9921 
           PLANNED OPTIMUM FLIGHT LEVEL

--------------------------------------------------------------------
          PLANNED FUEL
---------------------------------
FUEL            ARPT   FUEL   TIME
---------------------------------
TRIP             {sb['destination']['iata_code']}  {sb['fuel']['enroute_burn']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['est_time_enroute'])))}
CONT {sb['fuel']['contingency_p']} %             {sb['fuel']['contingency']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['contingency_time'])))}
ALTN             {sb['alternate'][0]['iata_code'] if sb.get('alternate') else '...'}  {sb['fuel']['alternate_burn'] if sb.get('alternate') else '...'}   {time.strftime('%H%M', time.gmtime(int(sb['times']['alternate_time']))) if sb.get('alternate') else '...'}
FINRES                {sb['fuel']['reserve']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['reserve_time'])))}
{sb['general']['flight_type'].upper()}/ETP                0   0000
---------------------------------
MINIMUM T/OFF FUEL   {sb['fuel']['min_takeoff']}   ...
---------------------------------
EXTRA                    0   0000
---------------------------------
T/OFF FUEL           {sb['fuel']['plan_takeoff']}   ...
TAXI             {sb['origin']['iata_code']}  {sb['fuel']['taxi']}   ...
---------------------------------
BLOCK FUEL       {sb['origin']['iata_code']}  {sb['fuel']['plan_block']}
PIC EXTRA             .....
TOTAL FUEL            .....
REASON FOR PIC EXTRA ............
--------------------------------------------------------------------
FMC INFO:
FINRES+ALTN           {int(sb['fuel']['reserve']) + int(sb['fuel']['alternate_burn'])}
TRIP+TAXI            {int(sb['fuel']['enroute_burn']) + int(sb['fuel']['taxi'])}
--------------------------------------------------------------------
MEL/CDL ITEMS DESCRIPTION
------------- -----------
{sb['general']['mel_remarks'] or 'NIL'}
--------------------------------------------------------------------
ROUTING:
ROUTE ID: {sb['general']['route_id']}
{sb['origin']['icao_code']}/{sb['origin']['plan_rwy']} {sb['general']['route']} {sb['destination']['icao_code']}/{sb['destination']['plan_rwy']}
--------------------------------------------------------------------
DISPATCHER: PATRICIA MITCHELL           PIC NAME: MIKU, ゴリ
TEL: +1 800 555 0199           PIC SIGNATURE: ...............

ETOPS/ETP {etops_apt_str}
--------------------------------------------------------------------
FLIGHT LOG
--------------------------------------------------------------------
POSITION EET ETO MORA IMT WIND EFOB PBRN
--------------------------------------------------------------------
{sb['origin']['icao_code']} ... ... {sb['general']['initial_fl']} {sb['general']['avg_wind_dir']}/{sb['general']['avg_wind_speed']} {sb['fuel']['plan_takeoff']} ...
--------------------------------------------------------------------
"""
    return text

# --- 5. Main UI Logic ---
if not st.session_state['authenticated']:
    st.markdown("<div class='opera-header'><span>WebAIMS OPERA | LOGIN</span></div>", unsafe_allow_html=True)
    if st.text_input("ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### OPERA MAIN")
        sb_input = st.text_input("SimBrief ID", value=SB_USER)
        if st.button("FETCH OFP"):
            uid = re.search(r"userid=(\d+)", sb_input).group(1) if "userid=" in sb_input else sb_input
            st.session_state['sb_json'] = fetch_simbrief(uid)
            if st.session_state['sb_json']:
                st.session_state['ofp_text'] = generate_ofp_text(st.session_state['sb_json'])
        
        st.markdown("---")
        # Quick Calc
        st.markdown("### T/D CALCULATOR")
        c1, c2, c3 = st.columns(3)
        curr = c1.number_input("CRZ FL", value=350, step=10) * 100
        targ = c2.number_input("TGT ALT", value=3000, step=100)
        gs = c3.number_input("GS", value=450, step=10)
        dist = ((curr - targ) / 1000) * 3
        vs = gs * 5
        st.markdown(f"**DIST:** {dist:.1f} NM | **V/S:** -{vs} FPM")

    # --- Main Area ---
    st.markdown("<div class='ofp-header'><span>WebAIMS OPERA</span><span>FLIGHT OPERATIONS PORTAL | BETA 2.0</span></div>", unsafe_allow_html=True)

    # OFP Text Area (If data exists)
    if st.session_state['ofp_text']:
        st.markdown(f"<div class='ofp-text'>{st.session_state['ofp_text']}</div>", unsafe_allow_html=True)
    else:
        st.info("Input SimBrief ID in sidebar and press FETCH OFP.")

    # Lower Tools Area
    st.markdown("<div class='tool-area'>", unsafe_allow_html=True)
    
    col_tools1, col_tools2 = st.columns([2, 1])
    
    with col_tools1:
        st.markdown("### CHECKLIST")
        sb = st.session_state['sb_json']
        # Set default AC type based on OFP if available
        default_ac = sb['aircraft']['icao_code'] if sb else "B787"
        if default_ac not in cl_db: default_ac = "B787"
        
        ac_type = st.selectbox("AIRCRAFT", list(cl_db.keys()), index=list(cl_db.keys()).index(default_ac))
        
        phases = list(cl_db[ac_type].keys())
        # Use columns for phases for monospace look
        phase_cols = st.columns(len(phases))
        # Logic to remember selected phase (using buttons to mimic tabs)
        if 'cl_phase' not in st.session_state: st.session_state['cl_phase'] = phases[0]
        for i, ph in enumerate(phases):
            if phase_cols[i].button(ph, key=f"btn_ph_{ph}"):
                st.session_state['cl_phase'] = ph
        
        selected_phase = st.session_state['cl_phase']
        st.markdown(f"**--- {ac_type} {selected_phase} ---**")
        for item in cl_db[ac_type][selected_phase]:
            st.checkbox(item, key=f"cl_{ac_type}_{selected_phase}_{item}")

    with col_tools2:
        st.markdown("### SCRATCH PAD")
        st_canvas(stroke_width=2, stroke_color="black", background_color="white", height=300, key="canvas")

    st.markdown("</div>", unsafe_allow_html=True)
