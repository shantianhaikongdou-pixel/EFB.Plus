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

# --- Checklist Database (全機体統合) ---
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

# --- 1. Page Configuration & Professional CSS ---
st.set_page_config(page_title="EFBPro | Flight Portal", layout="wide")

st.markdown("""
    <style>
    /* 全体の背景: 業務用ダークネイビー・グラデーション */
    .stApp {
        background: linear-gradient(180deg, #001433 0%, #002b5c 100%) !important;
    }

    /* メインコンテンツエリア: 白・カクカクのフラットデザイン */
    .main .block-container {
        background-color: #FFFFFF !important;
        padding: 1.5rem;
        border-radius: 2px;
        border: 2px solid #333;
        margin-top: 1rem;
        box-shadow: none;
    }

    /* サイドバー: グレー系 */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
        border-right: 2px solid #333;
        min-width: 350px !important;
    }

    /* 文字色: 視認性重視の黒 */
    h1, h2, h3, p, label, .stMarkdown {
        color: #000000 !important;
    }

    /* ボタン: 業務用・画像風（黒背景にネオン緑文字） */
    .stButton>button {
        background-color: #1a1a1a !important; 
        color: #00FF41 !important; 
        border: 1px solid #444 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #333333 !important;
        border-color: #00FF41 !important;
    }

    /* 入力エリア: 枠線を強調 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div>div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #555 !important;
        border-radius: 0px !important;
    }

    /* タブのスタイル: アクティブ時に業務用カラー */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #333;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1a1a1a !important;
        color: #00FF41 !important;
        border-radius: 0px !important;
    }

    /* ラジオボタンのカスタム (業務用セレクター風) */
    div[role="radiogroup"] > label {
        background-color: #eeeeee !important;
        border: 1px solid #999 !important;
        padding: 10px !important;
        border-radius: 0px !important;
        color: #333 !important;
    }
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1a1a1a !important;
        color: #00FF41 !important;
        border: 1px solid #00FF41 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Persistence & Session State ---
DB_FILE, LINK_FILE, POS_FILE = "pilot_logbook.json", "quick_links.json", "pilot_positions.json"
SB_USER = "906331" 

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'sb_json' not in st.session_state: st.session_state['sb_json'] = None
if 'sw_running' not in st.session_state: st.session_state['sw_running'] = False
if 'sw_start_time' not in st.session_state: st.session_state['sw_start_time'] = 0
if 'timer_end' not in st.session_state: st.session_state['timer_end'] = None

# --- Data Load ---
if os.path.exists(POS_FILE):
    with open(POS_FILE, "r", encoding="utf-8") as f: p_pos = json.load(f)
else:
    p_pos = {"ANA": "RJTT", "JAL": "RJTT", "HDJT": "RJTT", "Delta": "KATL", "Lufthansa": "EDDF"}

default_links = [
    {"name": "ATIS GURU", "url": "https://atis.guru/"},
    {"name": "TRANSITION ALT LIST", "url": "https://docs.google.com/spreadsheets/d/1uTvrw-5uoGPuzGyB8lEkhyn7TO_HaZQ6WB-5N6nH-NM/edit?gid=1698518120#gid=1698518120"},
    {"name": "SIMBRIEF", "url": "https://www.simbrief.com/system/dispatch.php"},
    {"name": "NAVIGRAPH", "url": "https://charts.navigraph.com/"},
    {"name": "FAA NOTAM SEARCH", "url": "https://notams.aim.faa.gov/notamSearch/nsapp.html#/"}
]

if os.path.exists(LINK_FILE):
    with open(LINK_FILE, "r", encoding="utf-8") as f: quick_links = json.load(f)
else:
    quick_links = default_links

# --- 3. Login Logic ---
if not st.session_state['authenticated']:
    st.title("EFBPro SYSTEM ACCESS")
    if st.text_input("ENTER ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    with st.sidebar:
        st.title("EFBPro")
        st.markdown(f"**USER ID:** `{SB_USER}`")
        st.markdown("---")
        s_tab1, s_tab2 = st.tabs(["LINKS", "TOOLS"])
        
        with s_tab1:
            for link in quick_links:
                st.markdown(f'[{link["name"]}]({link["url"]})')
            with st.expander("ADD NEW LINK"):
                with st.form("add_link_form", clear_on_submit=True):
                    new_name = st.text_input("LINK NAME")
                    new_url = st.text_input("URL")
                    if st.form_submit_button("ADD"):
                        quick_links.append({"name": new_name, "url": new_url})
                        with open(LINK_FILE, "w", encoding="utf-8") as f: json.dump(quick_links, f)
                        st.rerun()

        with s_tab2:
            menu = st.radio("SELECT TOOL", ["PILOT LOCATIONS", "TIMERS", "OFP", "T/D CALC", "TURN RADIUS", "PAD", "WEATHER (METAR/ATIS)", "LOG", "UNIT CONVERTER", "X-WIND CALC", "VATSIM TRAFFIC"])

    # --- MAIN CONTENT TABS ---
    main_tab1, main_tab2, main_tab3 = st.tabs(["MAIN TOOLS", "CHECKLIST", "MAINTENANCE"])

    with main_tab1:
        if menu == "PILOT LOCATIONS":
            st.subheader("PILOT LOCATIONS")
            cols = st.columns(len(p_pos))
            for i, (airline, icao) in enumerate(p_pos.items()):
                new_icao = cols[i].text_input(f"{airline}", value=icao).upper()
                if new_icao != icao:
                    p_pos[airline] = new_icao
                    with open(POS_FILE, "w", encoding="utf-8") as f: json.dump(p_pos, f)
                    st.rerun()

        elif menu == "TIMERS":
            st.subheader("FLIGHT TIMERS")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### STOPWATCH")
                if st.button("START"): st.session_state['sw_start_time'] = time.time(); st.session_state['sw_running'] = True
                if st.button("RESET"): st.session_state['sw_running'] = False; st.session_state['sw_start_time'] = 0
                if st.session_state['sw_running']:
                    st.code(f"SW: {time.strftime('%H:%M:%S', time.gmtime(time.time() - st.session_state['sw_start_time']))}")
            with c2:
                st.markdown("### COUNTDOWN")
                t_min = st.number_input("MIN", 1, 180, 15)
                if st.button("SET TIMER"): st.session_state['timer_end'] = time.time() + (t_min * 60)
                if st.session_state['timer_end']:
                    rem = st.session_state['timer_end'] - time.time()
                    if rem > 0: st.metric("REM", time.strftime('%H:%M:%S', time.gmtime(rem)))
                    else: st.warning("TIME UP!"); st.session_state['timer_end'] = None

        elif menu == "OFP":
            st.subheader("SIMBRIEF OFP")
            if st.button("FETCH SIMBRIEF"):
                res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={SB_USER}&json=1")
                if res.status_code == 200:
                    st.session_state['sb_json'] = res.json()
                    st.success("LOADED")
            
            if st.session_state.get('sb_json'):
                sb = st.session_state['sb_json']
                st.metric("CALLSIGN", sb.get('atc', {}).get('callsign', "N/A"))
                st.info(f"**ROUTE:** {sb.get('general', {}).get('route', 'N/A')}")

        elif menu == "T/D CALC":
            st.subheader("T/D CALCULATOR")
            c1, c2, c3 = st.columns(3)
            curr = c1.number_input("Current Alt", 0, 45000, 35000)
            tgt = c2.number_input("Target Alt", 0, 45000, 3000)
            gs = c3.number_input("GS (kt)", 100, 600, 400)
            dist = ((curr - tgt) / 1000) * 3
            st.metric("Dist from Target", f"{dist:.1f} NM")
            st.metric("Req VS", f"-{gs * 5} fpm")

        elif menu == "TURN RADIUS":
            st.subheader("TURN RADIUS")
            gs_tr = st.number_input("GS (KT)", 50, 600, 200)
            bank = st.number_input("Bank (deg)", 10, 45, 25)
            radius = (gs_tr**2) / (11.26 * math.tan(math.radians(bank)))
            st.metric("Radius (NM)", f"{(radius / 6076.12):.2f} NM")

        elif menu == "PAD":
            st.subheader("SCRATCH PAD")
            st_canvas(stroke_width=3, stroke_color="#000000", background_color="#FFFFFF", height=400, key="canvas")

        elif menu == "WEATHER (METAR/ATIS)":
            st.subheader("WEATHER")
            icao = st.text_input("ICAO", "RJTT").upper()
            if icao:
                res = requests.get(f"https://metar.vatsim.net/metar.php?id={icao}")
                st.code(res.text)

        elif menu == "LOG":
            st.subheader("FLIGHT LOG")
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f: logs = json.load(f)
            else: logs = []
            with st.form("log_form"):
                rt = st.text_input("ROUTE", value=st.session_state.get('sb_json', {}).get('origin', {}).get('icao_code', "") + "-" + st.session_state.get('sb_json', {}).get('destination', {}).get('icao_code', ""))
                if st.form_submit_button("SAVE"):
                    logs.append({"date": str(datetime.now().date()), "route": rt, "maint_status": "PENDING"})
                    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(logs, f)
                    st.rerun()

        elif menu == "UNIT CONVERTER":
            st.subheader("CONVERTER")
            kg = st.number_input("KG", value=0)
            st.write(f"{kg * 2.20462:.1f} LB")

        elif menu == "X-WIND CALC":
            st.subheader("X-WIND")
            r_hdg = st.number_input("Runway", 0, 360, 340)
            w_dir = st.number_input("Wind Dir", 0, 360, 20)
            w_spd = st.number_input("Speed (KT)", 0, 100, 15)
            diff = abs(r_hdg - w_dir)
            st.metric("Crosswind", f"{abs(w_spd * math.sin(math.radians(diff))):.1f} KT")

        elif menu == "VATSIM TRAFFIC":
            st.subheader("VATSIM")
            v_icao = st.text_input("ICAO", "RJTT").upper()
            v_res = requests.get("https://data.vatsim.net/v3/vatsim-data.json")
            if v_res.status_code == 200:
                pilots = [p for p in v_res.json().get("pilots", []) if (p.get("flight_plan", {}) or {}).get("arrival") == v_icao]
                for p in pilots: st.write(f"**{p['callsign']}** ➔ {v_icao}")

    with main_tab2:
        st.subheader("CHECKLIST")
        ac_type = st.selectbox("AIRCRAFT", list(cl_db.keys()))
        phase = st.radio("PHASE", list(cl_db[ac_type].keys()), horizontal=True)
        for item in cl_db[ac_type][phase]:
            st.checkbox(item, key=f"main_cl_{ac_type}_{phase}_{item}")

    with main_tab3:
        st.subheader("MAINTENANCE")
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f: all_logs = json.load(f)
        else: all_logs = []
        for idx, entry in enumerate(reversed(all_logs)):
            with st.expander(f"{entry['date']} | {entry['route']} - {entry.get('maint_status', 'PENDING')}"):
                if entry.get("maint_status") == "PENDING" and st.button(f"RELEASE (IDX:{idx})"):
                    all_logs[len(all_logs)-1-idx]["maint_status"] = "RELEASED"
                    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(all_logs, f)
                    st.rerun()

    if st.session_state['sw_running'] or st.session_state['timer_end']:
        time.sleep(1); st.rerun()
