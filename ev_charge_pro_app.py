"""
EV Charge Pro UK - Professional Edition
A comprehensive EV charging cost comparison tool for the UK market
"""

import numpy as np
import pandas as pd
import requests
from typing import Dict, Tuple, Optional
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ============================================================================
# CONFIGURATION & DATA
# ============================================================================

class Config:
    APP_TITLE = "EV Charge Pro UK"
    APP_ICON = "⚡"
    PAGE_LAYOUT = "wide"
    CACHE_TTL = 1800
    API_TIMEOUT = 8
    DEFAULT_MILES_PER_KWH = 3.5
    DEFAULT_EFFICIENCY_LOSS = 6  # percent

VEHICLE_DATABASE = pd.DataFrame([
    {"model": "Tesla Model Y Long Range", "battery_kwh": 75.0, "max_dc_kw": 250, "category": "Premium SUV"},
    {"model": "Tesla Model 3 Long Range", "battery_kwh": 75.0, "max_dc_kw": 250, "category": "Premium Sedan"},
    {"model": "Audi Q4 e-tron 77", "battery_kwh": 77.0, "max_dc_kw": 135, "category": "Premium SUV"},
    {"model": "Audi Q6 e-tron", "battery_kwh": 94.9, "max_dc_kw": 270, "category": "Premium SUV"},
    {"model": "Ford Explorer Extended Range", "battery_kwh": 79.0, "max_dc_kw": 185, "category": "SUV"},
    {"model": "BMW i4 eDrive40", "battery_kwh": 81.3, "max_dc_kw": 205, "category": "Premium Sedan"},
    {"model": "Skoda Enyaq 85", "battery_kwh": 82.0, "max_dc_kw": 175, "category": "SUV"},
    {"model": "Kia EV3 Long Range", "battery_kwh": 81.4, "max_dc_kw": 135, "category": "SUV"},
    {"model": "Skoda Elroq 85", "battery_kwh": 82.0, "max_dc_kw": 175, "category": "SUV"},
    {"model": "Volvo EX30 Extended Range", "battery_kwh": 69.0, "max_dc_kw": 153, "category": "Compact SUV"},
    {"model": "MG4 Long Range", "battery_kwh": 77.0, "max_dc_kw": 144, "category": "Hatchback"},
    {"model": "Hyundai Kona Electric 65", "battery_kwh": 65.4, "max_dc_kw": 102, "category": "Compact SUV"},
    {"model": "VW ID.4 Pro", "battery_kwh": 77.0, "max_dc_kw": 175, "category": "SUV"},
    {"model": "Nissan Ariya 87", "battery_kwh": 87.0, "max_dc_kw": 130, "category": "SUV"},
    {"model": "Kia EV6 Long Range", "battery_kwh": 84.0, "max_dc_kw": 235, "category": "SUV"},
    {"model": "Hyundai IONIQ 5 Long Range", "battery_kwh": 84.0, "max_dc_kw": 235, "category": "SUV"},
    {"model": "Mercedes EQA 350", "battery_kwh": 70.5, "max_dc_kw": 100, "category": "Premium SUV"},
    {"model": "Polestar 2 Long Range", "battery_kwh": 82.0, "max_dc_kw": 205, "category": "Premium Sedan"},
    {"model": "BYD Dolphin Comfort", "battery_kwh": 60.4, "max_dc_kw": 88, "category": "Hatchback"},
    {"model": "Vauxhall Corsa Electric", "battery_kwh": 51.0, "max_dc_kw": 100, "category": "Hatchback"},
    {"model": "Custom Vehicle", "battery_kwh": 80.0, "max_dc_kw": 150, "category": "Custom"},
])

CHARGING_PROVIDERS = {
    "MFG EV Power": {"energy":0.79,"time":0.0,"currency":"GBP","default_kw":150,"type":"public","category":"Rapid","network":"Regional"},
    "EVYVE Charging Stations": {"energy":0.80,"time":0.0,"currency":"GBP","default_kw":150,"type":"public","category":"Rapid","network":"Regional"},
    "Osprey Charging (App)": {"energy":0.82,"time":0.0,"currency":"GBP","default_kw":150,"type":"public","category":"Rapid","network":"National"},
    "Pod Point": {"energy":0.69,"time":0.0,"currency":"GBP","default_kw":75,"type":"public","category":"Fast","network":"National"},
    "Home - Octopus Intelligent": {"energy":0.08,"time":0.0,"currency":"GBP","default_kw":7,"type":"home","category":"Home","network":"Domestic"},
    "Home - EDF Standard": {"energy":0.10,"time":0.0,"currency":"GBP","default_kw":7,"type":"home","category":"Home","network":"Domestic"},
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_data(ttl=Config.CACHE_TTL)
def fetch_exchange_rates() -> Dict[str,float]:
    fallback = {"EUR":1.0,"GBP":0.87,"USD":1.10,"_date":"fallback","_status":"fallback"}
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=GBP,USD", timeout=Config.API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates",{})
        return {"EUR":1.0,"GBP":float(rates.get("GBP",0.87)),"USD":float(rates.get("USD",1.10)),"_date":data.get("date","unknown"),"_status":"live"}
    except:
        return fallback

def convert_currency(amount: float, from_currency: str, to_currency: str, rates: Dict) -> float:
    if from_currency==to_currency: return amount
    eur_amt = amount if from_currency=="EUR" else amount / rates[from_currency]
    return eur_amt * rates[to_currency]

def calculate_charging_time(battery_kwh:float,effective_kw:float,start_pct:float,end_pct:float,apply_taper=True)->float:
    if effective_kw<=0 or end_pct<=start_pct: return 0.0
    total_min=0.0;current=start_pct
    while current<end_pct:
        if apply_taper:
            if current<80: power=effective_kw; next_m=min(end_pct,80)
            elif current<90: power=effective_kw*0.5; next_m=min(end_pct,90)
            else: power=effective_kw*0.3; next_m=end_pct
        else: power=effective_kw; next_m=end_pct
        seg_energy=battery_kwh*((next_m-current)/100.0)
        total_min += (seg_energy/max(power,0.1))*60.0
        current=next_m
    return total_min

def calculate_charging_cost(energy_kwh:float,time_minutes:float,energy_price:float,time_price:float,session_fee:float)->float:
    return energy_kwh*energy_price + time_minutes*time_price + session_fee

def format_time(minutes:float)->str:
    if minutes<60: return f"{minutes:.0f} min"
    h=int(minutes//60); m=int(minutes%60); return f"{h}h {m}m"

def format_currency(amount:float,currency:str)->str:
    syms={"GBP":"£","EUR":"€","USD":"$"}; s=syms.get(currency,currency); return f"{s}{amount:.2f}"

@st.cache_data(ttl=Config.CACHE_TTL)
def geocode_postcode(postcode:str)->Optional[Tuple[float,float]]:
    try:
        geoloc=Nominatim(user_agent="ev_charge_pro_app").geocode(postcode)
        if geoloc: return geoloc.latitude,geoloc.longitude
        return None
    except: return None

# ============================================================================
# STREAMLIT APP
# ============================================================================

st.set_page_config(page_title=Config.APP_TITLE,page_icon=Config.APP_ICON,layout=Config.PAGE_LAYOUT)

# Hero Section
st.markdown(f"""
<div style="text-align:center;padding:2rem;background:#0a0e1a;border-radius:12px;margin-bottom:1rem;">
<h1 style="background:linear-gradient(135deg,#00ADF0 0%,#2182FF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{Config.APP_ICON} EV Charge Pro UK</h1>
<p style="color:#a0aec0;font-size:1.2rem;">Professional EV charging cost comparison • Compare providers • Calculate savings</p>
</div>
""",unsafe_allow_html=True)

# Postcode Input & Map
st.markdown("### 🗺️ Your Charging Location")
postcode = st.text_input("Enter your UK postcode",placeholder="e.g., SW1A 1AA")
if postcode:
    coords = geocode_postcode(postcode)
    if coords:
        lat,lon = coords
        st.success(f"📍 Postcode located at: {lat:.5f}, {lon:.5f}")
        m=folium.Map(location=[lat,lon],zoom_start=14)
        folium.Marker([lat,lon],tooltip="Your location",icon=folium.Icon(color="blue")).add_to(m)
        st_folium(m,width=700,height=500)
    else: st.error("❌ Could not find that postcode.")

# Vehicle Selection
st.markdown("### 🚗 Vehicle Configuration")
vehicle_name = st.selectbox("Select Your Vehicle",VEHICLE_DATABASE["model"].tolist(),index=7)
vdata=VEHICLE_DATABASE[VEHICLE_DATABASE["model"]==vehicle_name].iloc[0]
battery_kwh = st.number_input("Battery Capacity (kWh)",min_value=10.0,max_value=220.0,value=float(vdata["battery_kwh"]),step=0.1)
car_max_kw = st.slider("Max DC Charging (kW)",min_value=20,max_value=400,value=int(vdata["max_dc_kw"]),step=5)

# Charging Session Parameters
st.markdown("### ⚡ Charging Session Parameters")
start_pct = st.slider("Current State of Charge (%)",0,100,20)
end_pct = st.slider("Target State of Charge (%)",0,100,80)
efficiency_loss = st.slider("Charging Loss (%)",0,20,Config.DEFAULT_EFFICIENCY_LOSS)
apply_taper = st.checkbox("Apply Charging Curve Taper",value=True)
miles_per_kwh = st.number_input("Efficiency (mi/kWh)",min_value=1.0,max_value=7.0,value=Config.DEFAULT_MILES_PER_KWH,step=0.1)

# Provider Selection
st.markdown("### 🔌 Provider Configuration")
provider_list=list(CHARGING_PROVIDERS.keys())
provider_a_name = st.selectbox("Provider A",provider_list,index=0)
provider_b_name = st.selectbox("Provider B",provider_list,index=1)
provider_a = CHARGING_PROVIDERS[provider_a_name]
provider_b = CHARGING_PROVIDERS[provider_b_name]

# Convert to effective charging kW
effective_kw_a = min(car_max_kw,provider_a["default_kw"])
effective_kw_b = min(car_max_kw,provider_b["default_kw"])

# Calculation
energy_needed = battery_kwh*((end_pct-start_pct)/100.0)*(1+efficiency_loss/100.0)
time_a = calculate_charging_time(battery_kwh,effective_kw_a,start_pct,end_pct,apply_taper)
time_b = calculate_charging_time(battery_kwh,effective_kw_b,start_pct,end_pct,apply_taper)
cost_a = calculate_charging_cost(energy_needed,time_a,provider_a["energy"],provider_a["time"],0)
cost_b = calculate_charging_cost(energy_needed,time_b,provider_b["energy"],provider_b["time"],0)

# Results Display
st.markdown("---")
st.markdown("## 📊 Comparison Results")
col1,col2 = st.columns(2)
col1.metric(provider_a_name,format_currency(cost_a,"GBP"),format_time(time_a))
col2.metric(provider_b_name,format_currency(cost_b,"GBP"),format_time(time_b))

st.markdown(f"💵 Potential Savings: {format_currency(abs(cost_a-cost_b),'GBP')}")
