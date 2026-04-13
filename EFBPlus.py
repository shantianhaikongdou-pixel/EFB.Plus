import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import requests
import time
import math
from streamlit_drawable_canvas import st_canvas

# --- 1. Checklist Database (フル版) ---
cl_db = {
    "A350": {
        "COCKPIT PREP": ["PARKING BRAKE - SET", "ALL BATTERY SWITCH - ON", "EXTERNAL POWER - PUSH", "ADIRS (1, 2, 3) - NAV", "CREW SUPPLY - ON", "PACKS - AUTO", "NAV LIGHTS - ON", "LOGO LIGHTS - ON", "APU - MASTER-START", "NO SMOKING - AUTO", "EMERGENCY LIGHTS - ARMED", "FLIGHT DIRECTORS - ON", "ALTIMETERS - SET", "MCDU - SETUP", "FLT CTL PAGE - CHECK"],
        "BEFORE START": ["WINDOWS/DOORS - CLOSED", "BEACON - ON", "THRUST LEVERS - IDLE", "FUEL PUMPS - ON", "TRANSPONDER - AS REQ"],
        "AFTER START": ["ENGINE MODE SELECTOR - NORM", "PITCH TRIM - SET", "AUTOBRAKE - MAX", "FLAPS - SET", "GND SPOILERS - ARMED", "APU - OFF", "FLIGHT CONTROLS - CHECKED", "RUDDER TRIM - ZERO", "ANTI-ICE - AS REQ"],
        "TAXI/TAKEOFF": ["GROUND EQUIPMENT - CLEAR", "NOSEWHEEL LIGHTS - TAXI", "BRAKES - CHECK", "AUTO THRUST - BLUE", "TCAS - TA/RA", "PACKS - OFF/ON"],
        "LANDING": ["GND SPOILERS - ARM", "ENG MODE SELECTOR - AS REQ", "AUTOBRAKE - AS REQ", "FLAPS - SET LDG", "GO AROUND ALTITUDE - SET", "ECAM MEMO - LDG NO BLUE"],
        "SHUTDOWN/SECURE": ["PARKING BRAKE - SET", "APU - START", "ENG 1 & 2 MASTER - OFF", "BEACON LIGHTS - OFF", "FUEL PUMPS - OFF", "ADIRS - OFF", "BATTERY - OFF"]
    },
    "B787": {
        "BEFORE START": ["FLIGHT DECK DOOR - CLOSED", "PASSENGER SIGNS - ON", "MCP - SET", "FMS - COMPLETED", "BEACON - ON"],
        "AFTER START/TAXI": ["FLAPS - SET", "AUTOBRAKE - RTO", "FLIGHT CONTROLS - CHECKED"],
        "APPROACH/LANDING": ["ALTIMETER - RESET", "LANDING LIGHTS - ON", "SEAT BELTS - ON"],
        "SHUTDOWN": ["PARKING BRAKE - SET", "APU - RUNNING", "FUEL CONTROL - CUTOFF", "BEACON - OFF"]
    },
    "A320/321": {
        "COCKPIT PREP": ["GEAR PINS - REMOVED", "FUEL QTY - CHECK", "SIGNS - ON", "ADIRS - NAV"],
        "BEFORE START": ["PARKING BRAKE - SET", "WINDOWS/DOORS - CLOSED", "BEACON - ON"],
        "AFTER START": ["APU - OFF", "ANTI ICE - AS REQ", "PITCH TRIM - SET"],
        "LANDING": ["GEAR - DOWN", "SPLRS - ARM", "FLAPS - SET", "ECAM MEMO - LDG NO BLUE"]
    },
    "B777": {
        "PREFLIGHT": ["ADIRU - ON", "EMER LIGHTS - ARMED", "HYD PANEL - SET", "FMC - SETUP"],
        "BEFORE START": ["FLIGHT DECK DOOR - CLOSED", "PASSENGER SIGNS - ON", "BEACON - ON"],
        "SHUTDOWN": ["FUEL PUMPS - OFF", "FLAPS - UP", "FUEL CONTROL - CUTOFF"]
    },
    "B767": {
        "PREFLIGHT": ["IRS - NAV", "WINDOW HEAT - ON", "PARKING BRAKE - SET"],
        "BEFORE START": ["WINDOWS - CLOSED", "PASSENGER SIGNS - ON", "DOORS - ARMED"],
        "LANDING": ["SPEEDBRAKE - ARMED", "GEAR - DOWN", "FLAPS - SET"]
    },
    "A330": {
        "COCKPIT PREP": ["ADIRS - NAV", "BARO REF - SET", "SEAT BELTS - ON"],
        "LANDING": ["ECAM MEMO - LDG NO BLUE", "GEAR - DOWN", "FLAPS - SET"],
        "PARKING": ["PARKING BRAKE - SET", "ENGINES - OFF", "FUEL PUMPS - OFF"]
    },
    "HondaJet": {
        "CDU SETUP": ["Database Status - CONNECT", "Flight Plan - VERIFY"],
        "BEFORE START": ["Battery - ON", "Parking Brake - SET"],
        "LANDING": ["Gear - DOWN", "Flaps - LDG", "Yaw Damper - OFF @50ft"],
        "SHUTDOWN": ["Engines - OFF", "Electrical - OFF"]
    }
}

# --- 2. Page Config & CSS ---
st.set_page_config(page_title="EFBPro | Professional", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #001f5b 0%, #004080 100%) !important; }
    .main .block-container { background-color: #FFFFFF !important; padding: 1.5rem; border-radius: 2px; border: 2px solid #333; margin-top: 1rem; }
    [data-testid="stSidebar"] > div:first-child { background-color: #f5f5f5 !important; border-right: 2px solid #333; }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #000000 !important; }
    .stButton>button {
        background-color: #1a1a1a !important; color: #00FF41 !important; 
        border: 1px solid #444 !important; border-radius: 0px !important;
        font-family: 'Courier New', Courier, monospace; font-weight: bold; text-transform: uppercase;
    }
    .stButton>button:hover { background-color: #333333 !important; border-color: #00FF41 !important; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div>div {
        background-color: #ffffff !important; color: #000 !important; border: 2px solid #555 !important; border-radius: 0px !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #1a1a1a !important; color: #00FF41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Session State & Files ---
DB_FILE, LINK_FILE, POS_FILE = "logbook.json", "links.json", "positions.json"
SB_USER = "906331"

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'sb_json' not in st.session_state: st.session_state['sb_json'] = None
if 'sw_start' not in st.session_state: st.session_state['sw_start'] = 0
if 'sw_run' not in st.session_state: st.session_state['sw_run'] = False
if 'timer_end' not in st.session_state: st.session_state['timer_end'] = None

# Load Dynamic Data
if os.path.exists(POS_FILE):
    with open(POS_FILE, "r") as f: p_pos = json.load(f)
else:
    p_pos = {"ANA": "RJTT", "JAL": "RJTT", "HDJT": "RJTT", "Delta": "KATL", "Lufthansa": "EDDF"}

if os.path.exists(LINK_FILE):
    with open(LINK_FILE, "r") as f: quick_links = json.load(f)
else:
    quick_links = [{"name": "SIMBRIEF", "url": "https://www.simbrief.com/"}, {"name": "NAVIGRAPH", "url": "https://charts.navigraph.com/"}]

# --- 4. Main App Logic ---
if not st.session_state['authenticated']:
    st.title("EFBPro SYSTEM ACCESS")
    if st.text_input("ENTER ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    with st.sidebar:
        st.title("EFBPro")
        menu = st.radio("TOOLBOX", ["OFP DATA", "TIMERS", "CALCULATORS", "WEATHER", "VATSIM", "SCRATCH PAD", "LOCATIONS", "LINKS"])

    m_tab1, m_tab2, m_tab3 = st.tabs(["FLIGHT TOOLS", "CHECKLIST", "LOG/MAINT"])

    with m_tab1:
        if menu == "OFP DATA":
            if st.button("FETCH FROM SIMBRIEF"):
                res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={SB_USER}&json=1")
                if res.status_code == 200: st.session_state['sb_json'] = res.json(); st.success("LOADED")
            if st.session_state['sb_json']:
                sb = st.session_state['sb_json']
                st.metric("CALLSIGN", sb['atc']['callsign'])
                st.code(f"ROUTE: {sb['general']['route']}")

        elif menu == "TIMERS":
            c1, c2 = st.columns(2)
            with c1:
                st.write("STOPWATCH")
                if st.button("START/RESET"): st.session_state['sw_run'] = True; st.session_state['sw_start'] = time.time()
                if st.session_state['sw_run']: st.code(time.strftime('%H:%M:%S', time.gmtime(time.time() - st.session_state['sw_start'])))
            with c2:
                st.write("TIMER")
                tm = st.number_input("MINUTES", 1, 180, 15)
                if st.button("SET"): st.session_state['timer_end'] = time.time() + (tm * 60)
                if st.session_state['timer_end']:
                    rem = st.session_state['timer_end'] - time.time()
                    st.metric("REM", time.strftime('%H:%M:%S', time.gmtime(max(0, rem))))

        elif menu == "CALCULATORS":
            st.write("T/D CALC")
            curr = st.number_input("Current Alt", 0, 45000, 35000)
            tgt = st.number_input("Target Alt", 0, 45000, 3000)
            st.metric("Distance (NM)", f"{((curr - tgt) / 1000) * 3:.1f}")
            st.write("---")
            st.write("UNIT CONVERTER")
            val = st.number_input("KG to LB", 0)
            st.code(f"{val * 2.20462:.1f} LB")

        elif menu == "WEATHER":
            icao = st.text_input("ICAO", "RJTT").upper()
            if icao: st.code(requests.get(f"https://metar.vatsim.net/metar.php?id={icao}").text)

        elif menu == "SCRATCH PAD":
            st_canvas(stroke_width=3, stroke_color="#000", background_color="#FFF", height=300, key="canvas")

        elif menu == "LOCATIONS":
            for airline, icao in p_pos.items():
                p_pos[airline] = st.text_input(f"{airline}", value=icao).upper()
            if st.button("SAVE"): 
                with open(POS_FILE, "w") as f: json.dump(p_pos, f)

        elif menu == "LINKS":
            for l in quick_links: st.markdown(f"[{l['name']}]({l['url']})")
            with st.expander("ADD LINK"):
                n = st.text_input("NAME")
                u = st.text_input("URL")
                if st.button("ADD"): 
                    quick_links.append({"name": n, "url": u})
                    with open(LINK_FILE, "w") as f: json.dump(quick_links, f)

    with m_tab2:
        ac = st.selectbox("AIRCRAFT", list(cl_db.keys()))
        ph = st.radio("PHASE", list(cl_db[ac].keys()), horizontal=True)
        for item in cl_db[ac][ph]: st.checkbox(item, key=f"cl_{ac}_{ph}_{item}")

    with m_tab3:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f: logs = json.load(f)
        else: logs = []
        with st.form("log"):
            rt = st.text_input("ROUTE")
            if st.form_submit_button("SAVE"):
                logs.append({"date": str(datetime.now().date()), "route": rt, "maint": "PENDING"})
                with open(DB_FILE, "w") as f: json.dump(logs, f)
        for i, l in enumerate(reversed(logs)):
            with st.expander(f"{l['date']} | {l['route']} | {l['maint']}"):
                if l['maint'] == "PENDING" and st.button(f"RELEASE", key=i):
                    logs[len(logs)-1-i]['maint'] = "RELEASED"
                    with open(DB_FILE, "w") as f: json.dump(logs, f); st.rerun()

    if st.session_state['sw_run'] or st.session_state['timer_end']:
        time.sleep(1); st.rerun()
