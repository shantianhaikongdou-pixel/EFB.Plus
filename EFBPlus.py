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

# 完全版チェックリストDB（全機体網羅）
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
        "PREFLIGHT": ["ADIRU - ON", "THRUST LEVERS - IDLE", "FUEL CONTROL - CUTOFF", "LANDING GEAR - DOWN", "FLAPS - UP", "BATTERY - ON"],
        "BEFORE START": ["FLIGHT DECK DOOR - CLOSED", "PASSENGER SIGNS - ON", "MCP - SET", "FMS - COMPLETED", "BEACON - ON"],
        "AFTER START": ["ANTI-ICE - AS REQ", "RECALL - CHECK", "AUTOBRAKE - RTO", "FLAPS - SET"],
        "BEFORE TAKEOFF": ["FLIGHT CONTROLS - CHECK", "TRANSPONDER - TA/RA"],
        "DESCENT/APPROACH": ["ALTIMETER - SET", "AUTOBRAKE - SET", "VREF - SET"],
        "LANDING": ["SPEEDBRAKE - ARMED", "LANDING GEAR - DOWN", "FLAPS - SET"],
        "SHUTDOWN": ["PARKING BRAKE - SET", "FUEL CONTROL - CUTOFF", "PASSENGER SIGNS - OFF"]
    },
    "B767": {
        "PREFLIGHT": ["BATTERY - ON", "STBY POWER - AUTO", "BUS TIE - AUTO", "IRS - NAV", "HYDRAULICS - ON/AUTO"],
        "BEFORE START": ["FUEL PUMPS - ON", "BEACON - ON", "MCP - SET"],
        "AFTER START": ["ANTI-ICE - AS REQ", "APU - OFF", "FLAPS - SET", "AUTOBRAKE - RTO"],
        "APPROACH": ["ALTIMETER - SET", "SEAT BELTS - ON", "AUTOBRAKE - SET"],
        "LANDING": ["LANDING GEAR - DOWN", "FLAPS - SET", "SPEEDBRAKE - ARMED"],
        "SHUTDOWN": ["PARKING BRAKE - SET", "FUEL CONTROL - CUTOFF", "IRS - OFF"]
    },
    "A330": {
        "COCKPIT PREP": ["BATTERIES - ON", "EXTERNAL POWER - ON", "ADIRS - NAV", "SIGNS - ON", "APU - START"],
        "BEFORE START": ["DOORS - CLOSED", "BEACON - ON", "THRUST LEVERS - IDLE"],
        "AFTER START": ["ANTI-ICE - AS REQ", "APU - OFF", "PITCH TRIM - SET", "FLAPS - SET"],
        "TAKEOFF": ["CONFIG - TEST", "TCAS - TA/RA", "PACKS - OFF/ON"],
        "LANDING": ["GEAR - DOWN", "FLAPS - FULL", "SPOILERS - ARMED"],
        "SHUTDOWN": ["PARKING BRAKE - SET", "ENGINES - OFF", "FUEL PUMPS - OFF"]
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
st.set_page_config(page_title="EFBplus Beta | OPERA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; color: #333; }
    .opera-header {
        background-color: #003194; color: white;
        padding: 12px 20px; border-radius: 4px;
        font-family: 'Arial', sans-serif;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); margin-bottom: 20px;
    }
    .opera-logo { font-size: 22px; font-weight: bold; font-style: italic; }
    .opera-table {
        width: 100%; border-collapse: collapse;
        background-color: white; border-radius: 4px; overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .opera-table th {
        background-color: #e6eef5; color: #003194;
        text-align: left; padding: 12px; font-size: 14px;
        border-bottom: 2px solid #003194;
    }
    .opera-table td { padding: 12px; border-bottom: 1px solid #ddd; font-family: monospace; }
    .actual-green { color: #1DB954; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ddd; }
    .stButton>button { background-color: #003194 !important; color: white !important; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Session State Management ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'sb_json' not in st.session_state: st.session_state['sb_json'] = None
if 'sw_running' not in st.session_state: st.session_state['sw_running'] = False
if 'sw_start_time' not in st.session_state: st.session_state['sw_start_time'] = 0
if 'timer_end' not in st.session_state: st.session_state['timer_end'] = None

# --- 4. Logic Functions ---
def fetch_simbrief(user_id):
    res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&json=1")
    return res.json() if res.status_code == 200 else None

# --- 5. Main UI Logic ---
if not st.session_state['authenticated']:
    st.markdown("<div class='opera-header'><div class='opera-logo'>EFBplus <span style='font-weight:normal'>LOGIN</span></div></div>", unsafe_allow_html=True)
    if st.text_input("ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    st.markdown("""
        <div class='opera-header'>
            <div class='opera-logo'>WebAIMS <span style='font-weight:normal'>OPERA</span></div>
            <div style='font-size:12px;'>FLIGHT OPERATIONS PORTAL | BETA 2.0</div>
        </div>
        """, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("⏱️ TIME MANAGEMENT")
        c1, c2 = st.columns(2)
        if c1.button("START SW"):
            st.session_state['sw_start_time'] = time.time()
            st.session_state['sw_running'] = True
        if c2.button("RESET SW"):
            st.session_state['sw_running'] = False
            st.session_state['sw_start_time'] = 0
        
        if st.session_state['sw_running']:
            elapsed = time.time() - st.session_state['sw_start_time']
            st.metric("STOPWATCH", time.strftime('%H:%M:%S', time.gmtime(elapsed)))
        
        t_min = st.number_input("MINUTES", 1, 180, 15)
        if st.button("SET TIMER"):
            st.session_state['timer_end'] = time.time() + (t_min * 60)
        
        if st.session_state['timer_end']:
            rem = st.session_state['timer_end'] - time.time()
            if rem > 0:
                st.metric("REMAINING", time.strftime('%H:%M:%S', time.gmtime(rem)))
            else:
                st.warning("TIME UP!")
                st.session_state['timer_end'] = None

        st.markdown("---")
        menu = st.radio("MENU", ["OPERA MAIN", "CALCULATORS", "WEATHER", "SCRATCH PAD"])

    # --- Main Content ---
    if menu == "OPERA MAIN":
        col_sb1, col_sb2 = st.columns([3, 1])
        with col_sb1:
            sb_input = st.text_input("SimBrief ID or URL", value=SB_USER)
        with col_sb2:
            st.write(" ")
            if st.button("FETCH OFP"):
                uid = re.search(r"userid=(\d+)", sb_input).group(1) if "userid=" in sb_input else sb_input
                st.session_state['sb_json'] = fetch_simbrief(uid)
        
        if st.session_state['sb_json']:
            sb = st.session_state['sb_json']
            st.markdown(f"### ✈️ {sb['atc']['callsign']} | {sb['origin']['icao_code']} → {sb['destination']['icao_code']}")
            st.markdown(f"""
            <table class='opera-table'>
                <thead><tr><th>EVENT</th><th>PLAN</th><th>ACTUAL</th><th>REMARKS</th></tr></thead>
                <tbody>
                    <tr><td>BLOCK OFF</td><td>{sb['times']['est_off']}</td><td class='actual-green'>---</td><td>WAITING</td></tr>
                    <tr><td>ZFW / TOW</td><td>{sb['weights']['est_zfw']} / {sb['weights']['est_takeoff_weight']}</td><td>---</td><td>KG</td></tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
            v = sb.get('takeoff', {})
            st.info(f"V1: {v.get('v1','--')} | VR: {v.get('vr','--')} | V2: {v.get('v2','--')} | TRIM: {v.get('trim','--')}")

    elif menu == "CALCULATORS":
        st.subheader("T/D CALCULATOR")
        c1, c2, c3 = st.columns(3)
        curr = c1.number_input("Current FT", 0, 45000, 35000)
        targ = c2.number_input("Target FT", 0, 45000, 3000)
        gs = c3.number_input("GS", 100, 600, 400)
        dist = ((curr - targ) / 1000) * 3
        vs = gs * 5
        st.success(f"Start Descent at: {dist:.1f} NM | VS: -{vs} fpm")
            
    elif menu == "WEATHER":
        icao = st.text_input("ICAO", "RJTT").upper()
        if icao:
            try:
                res = requests.get(f"https://metar.vatsim.net/metar.php?id={icao}")
                st.code(res.text)
            except:
                st.error("Weather data unavailable")

    elif menu == "SCRATCH PAD":
        st_canvas(stroke_width=3, stroke_color="#000", background_color="#FFF", height=400, key="canvas")

    # --- Checklist Tab (下部に常に表示) ---
    st.markdown("---")
    with st.expander("📋 AIRCRAFT CHECKLIST (FULL DATABASE)"):
        ac_type = st.selectbox("AIRCRAFT", list(cl_db.keys()))
        phase = st.radio("PHASE", list(cl_db[ac_type].keys()), horizontal=True)
        for item in cl_db[ac_type][phase]:
            st.checkbox(item, key=f"cl_{ac_type}_{phase}_{item}")

    # Auto Refresh for Timers
    if st.session_state['sw_running'] or st.session_state['timer_end']:
        time.sleep(1)
        st.rerun()
