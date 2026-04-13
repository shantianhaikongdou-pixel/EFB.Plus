import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import time
from streamlit_drawable_canvas import st_canvas

# --- 1. 定数・設定 ---
SB_USER = "906331"

# チェックリストDB（絵文字なし・大文字のみ）
cl_db = {
    "A350": {
        "COCKPIT PREP": ["PARKING BRAKE - SET", "ALL BATTERY SWITCH - ON", "EXTERNAL POWER - PUSH", "ADIRS (1, 2, 3) - NAV", "CREW SUPPLY - ON", "PACKS - AUTO", "NAV LIGHTS - ON", "LOGO LIGHTS - ON", "APU - MASTER-START", "NO SMOKING - AUTO", "NO MOBILE - AUTO", "EMERGENCY LIGHTS - ARMED", "FLIGHT DIRECTORS - ON", "ALTIMETERS - SET", "MCDU - SETUP", "FLT CTL PAGE - CHECK"],
        "BEFORE START": ["WINDOWS/DOORS - CLOSED", "BEACON - ON", "THRUST LEVERS - IDLE", "FUEL PUMPS - ON", "TRANSPONDER - AS REQ"],
        "AFTER START": ["ENGINE MODE SELECTOR - NORM", "PITCH TRIM - SET", "AUTOBRAKE - MAX", "FLAPS - SET", "GND SPOILERS - ARMED", "APU - OFF", "FLIGHT CONTROLS - CHECKED", "RUDDER TRIM - ZERO", "ANTI-ICE - AS REQ"],
        "TAXI/TAKEOFF": ["GROUND EQUIPMENT - CLEAR", "NOSEWHEEL LIGHTS - TAXI", "BRAKES - CHECK", "AUTO THRUST - BLUE", "TCAS - TA/RA", "PACKS - OFF/ON"],
        "CRUISE": ["ALTIMETERS - STD", "ANTI-ICE - AS REQ", "ECAM MEMO - CHECKED"]
    },
    "B787": {
        "ELECTRICAL POWERUP": ["SERVICE INTERPHONE - OFF", "BACKUP WINDOW HEAT - ON", "PRIMARY WINDOW HEAT - ON", "ENGINE PRIMARY PUMP L&R - ON", "C1 & C2 ELEC PUMP - OFF", "L & R DEMAND PUMP - OFF", "SEAT BELT SIGNS - ON", "APU FIRE PANEL - SET", "CARGO FIRE ARM - NORM", "ENGINE EEC MODE - NORM", "FUEL JETTISON - OFF", "WING/ENGINE ANTI-ICE - AUTO"],
        "BEFORE START": ["FLIGHT DECK DOOR - CLOSED/LOCKED", "PASSENGER SIGNS - ON", "MCP - SET", "FMS - COMPLETED", "BEACON - ON"],
        "AFTER START/TAXI": ["FLAPS - SET", "AUTOBRAKE - RTO", "FLIGHT CONTROLS - CHECKED"],
        "CLIMB/CRUISE": ["LANDING GEAR - UP", "FLAPS - UP", "ALTIMETERS - STD"]
    },
    "A320/321": {
        "COCKPIT PREP": ["GEAR PINS and COVERS - REMOVED", "FUEL QUANTITY - KG CHECK", "SIGNS - ON/AUTO", "ADIRS - NAV", "BARO REF - SET (BOTH)"],
        "BEFORE START": ["PARKING BRAKE - SET", "T.O SPEEDS & THRUST - BOTH SET", "WINDOWS/DOORS - CLOSED", "BEACON - ON"],
        "AFTER START": ["APU - OFF", "Y ELEC PUMP - OFF", "ANTI ICE - AS REQ", "PITCH TRIM - SET", "RUDDER TRIM - ZERO"]
    },
    "HondaJet": {
        "CDU SETUP": ["Database Status - CONNECT", "Avionics Settings - AS DESIRED", "Flight Plan - ENTER/VERIFY"],
        "BEFORE START": ["ATC Clearance - OBTAIN", "Transponder - SQUAWK SET", "Alt Select - SET CLEARED ALT", "Parking Brake - SET"],
        "AFTER START/TAXI": ["External Power - DISCONNECT", "Lights - AS REQ", "Flaps - TAKE OFF", "Trim - SET (GREEN)"]
    }
}

# --- 2. ページ構成 & 究極の無機質CSS ---
st.set_page_config(page_title="EFBPlus | WebAIMS OPERA", layout="wide")

st.markdown("""
    <style>
    /* 全体を等幅フォント、背景をグレーに */
    html, body, [class*="css"] {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 12px !important;
        background-color: #e0e0e0 !important;
        color: #000 !important;
    }
    
    /* 余計な余白を徹底排除 */
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* ヘッダー（ANA/OPERA風） */
    .opera-header {
        background-color: #003194; color: white;
        padding: 4px 12px; font-weight: bold;
        display: flex; justify-content: space-between;
        border-bottom: 2px solid #000;
    }

    /* サイドバーの無機質化 */
    [data-testid="stSidebar"] {
        background-color: #d0d0d0 !important;
        border-right: 2px solid #000;
    }
    
    /* OFP表示エリア：ここが画像の再現 */
    .ofp-paper {
        background-color: #fff !important;
        color: #000 !important;
        padding: 20px;
        margin: 0;
        line-height: 1.1;
        white-space: pre;
        overflow-x: auto;
        border-bottom: 2px solid #000;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
    }

    /* ボタン・入力欄の角を角に */
    .stButton>button {
        border-radius: 0 !important;
        border: 1px solid #000 !important;
        background-color: #eee !important;
        color: #000 !important;
        font-weight: bold;
    }
    .stTextInput input { border-radius: 0 !important; border: 1px solid #000 !important; }

    /* ツールエリア（下部） */
    .bottom-tools { background-color: #f0f0f0; padding: 10px; border-top: 1px solid #999; }
    
    /* チェックボックスのリスト化 */
    .stCheckbox { margin-bottom: -10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ロジック ---
def fetch_simbrief(user_id):
    res = requests.get(f"https://www.simbrief.com/api/xml.fetcher.php?userid={user_id}&json=1")
    return res.json() if res.status_code == 200 else None

def generate_ofp_text(sb):
    now = datetime.utcnow()
    release_time = now.strftime("%d%H%M %b%y").upper()
    flight_date = datetime.fromtimestamp(int(sb['params']['time_generated'])).strftime("%d%b%y").upper()
    etops_apts = sb.get('etops', {}).get('alternates', [])
    if isinstance(etops_apts, str): etops_apts = [etops_apts]
    etops_apt_str = " ".join(etops_apts)

    text = f"""[ OFP ] -----------------------------------------------------------
{sb['atc']['callsign']}   {flight_date}   {sb['origin']['icao_code']}-{sb['destination']['icao_code']}   {sb['aircraft']['icao_code']} {sb['aircraft']['reg']}   RELEASE {release_time}
OFP 0   {sb['origin']['name'].upper()}-{sb['destination']['name'].upper()}
--------------------------------------------------------------------
ATC C/S   {sb['atc']['callsign']}      {sb['origin']['icao_code']}/{sb['origin']['iata_code']}   {sb['destination']['icao_code']}/{sb['destination']['iata_code']}      CI {sb['general']['costindex']}
{flight_date}   {sb['aircraft']['reg']}         {sb['times']['est_out'][7:11]}/{sb['times']['sched_out'][7:11]}  {sb['times']['est_in'][7:11]}/{sb['times']['sched_in'][7:11]}
--------------------------------------------------------------------
FUEL            ARPT   FUEL   TIME
---------------------------------
TRIP             {sb['destination']['iata_code']}  {sb['fuel']['enroute_burn']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['est_time_enroute'])))}
CONT {sb['fuel']['contingency_p']} %             {sb['fuel']['contingency']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['contingency_time'])))}
ALTN             {sb['alternate'][0]['iata_code'] if sb.get('alternate') else '...'}  {sb['fuel']['alternate_burn'] if sb.get('alternate') else '...'}   {time.strftime('%H%M', time.gmtime(int(sb['times']['alternate_time']))) if sb.get('alternate') else '...'}
FINRES                {sb['fuel']['reserve']}   {time.strftime('%H%M', time.gmtime(int(sb['times']['reserve_time'])))}
---------------------------------
MINIMUM T/OFF FUEL   {sb['fuel']['min_takeoff']}
TAXI             {sb['origin']['iata_code']}  {sb['fuel']['taxi']}
BLOCK FUEL       {sb['origin']['iata_code']}  {sb['fuel']['plan_block']}
--------------------------------------------------------------------
ROUTING:
{sb['origin']['icao_code']}/{sb['origin']['plan_rwy']} {sb['general']['route']} {sb['destination']['icao_code']}/{sb['destination']['plan_rwy']}
--------------------------------------------------------------------
ETOPS/ETP: {etops_apt_str or 'NIL'}
--------------------------------------------------------------------
DISPATCHER: PATRICIA MITCHELL        PIC: MIKUTO / TAJIMA
--------------------------------------------------------------------"""
    return text

# --- 4. メイン画面表示 ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'ofp_text' not in st.session_state: st.session_state['ofp_text'] = None

if not st.session_state['authenticated']:
    st.markdown("<div class='opera-header'><span>LOGIN REQUIRED</span></div>", unsafe_allow_html=True)
    if st.text_input("ACCESS CODE", type="password") == "3910":
        st.session_state['authenticated'] = True
        st.rerun()
else:
    # サイドバー
    with st.sidebar:
        st.markdown("### DATA INPUT")
        sb_id = st.text_input("SimBrief ID", value=SB_USER)
        if st.button("LOAD FLIGHT PLAN"):
            data = fetch_simbrief(sb_id)
            if data:
                st.session_state['sb_json'] = data
                st.session_state['ofp_text'] = generate_ofp_text(data)
        
        st.markdown("---")
        st.markdown("### T/D CALC")
        c1, c2 = st.columns(2)
        fl = c1.number_input("CRZ FL", 350)
        tgt = c2.number_input("TGT ALT", 3000)
        gs = st.number_input("GS", 450)
        st.markdown(f"DIST: **{((fl*100-tgt)/1000)*3:.1f} NM**")
        st.markdown(f"V/S: **-{gs*5} FPM**")

    # メインヘッダー
    st.markdown("<div class='opera-header'><span>WebAIMS OPERA (BETA)</span><span>UNIT: LBS / UTC</span></div>", unsafe_allow_html=True)

    # OFPエリア（真っ白な紙風）
    if st.session_state['ofp_text']:
        st.markdown(f"<div class='ofp-paper'>{st.session_state['ofp_text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='ofp-paper'>NO OFP LOADED. ENTER SIMBRIEF ID TO START.</div>", unsafe_allow_html=True)

    # 下部ツールエリア
    st.markdown("<div class='bottom-tools'>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**[ CHECKLIST ]**")
        sb = st.session_state.get('sb_json')
        ac_type = sb['aircraft']['icao_code'] if sb else "B787"
        if ac_type not in cl_db: ac_type = "B787"
        
        # フェーズ選択をボタンで（業務用っぽく）
        phases = list(cl_db[ac_type].keys())
        if 'cl_phase' not in st.session_state: st.session_state['cl_phase'] = phases[0]
        
        cols = st.columns(len(phases))
        for i, p in enumerate(phases):
            if cols[i].button(p): st.session_state['cl_phase'] = p
            
        st.markdown(f"--- {st.session_state['cl_phase']} ---")
        for item in cl_db[ac_type][st.session_state['cl_phase']]:
            st.checkbox(item)

    with col2:
        st.markdown("**[ SCRATCH PAD ]**")
        st_canvas(stroke_width=2, stroke_color="black", background_color="#fff", height=250, key="canv")
    
    st.markdown("</div>", unsafe_allow_html=True)
