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
    """Application configuration constants"""
    APP_TITLE = "EV Charge Pro UK"
    APP_ICON = "⚡"
    PAGE_LAYOUT = "wide"
    CACHE_TTL = 1800  # 30 minutes
    API_TIMEOUT = 8
    DEFAULT_MILES_PER_KWH = 3.5
    DEFAULT_EFFICIENCY_LOSS = 6  # percentage
    
    # Color scheme
    COLORS = {
        'primary': '#00ADF0',
        'secondary': '#2182FF',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'background': '#050a14',
        'card': 'rgba(10,18,34,.92)',
    }

# Vehicle database
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

# Charging providers database
CHARGING_PROVIDERS = {
    "MFG EV Power": {"energy": 0.79, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Rapid", "network": "Regional"},
    "EVYVE Charging Stations": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Rapid", "network": "Regional"},
    "Osprey Charging (App)": {"energy": 0.82, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Rapid", "network": "National"},
    "Osprey Charging (Contactless)": {"energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Rapid", "network": "National"},
    "Electroverse": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Roaming", "network": "Multi-Network"},
    "Zapmap Zap-Pay": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Roaming", "network": "Multi-Network"},
    "Plugsurfing": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Roaming", "network": "Multi-Network"},
    "BP Pulse PAYG": {"energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public", "category": "Rapid", "network": "National"},
    "Pod Point": {"energy": 0.69, "time": 0.00, "currency": "GBP", "default_kw": 75, "type": "public", "category": "Fast", "network": "National"},
    "IZIVIA Pass": {"energy": 0.75, "time": 0.00, "currency": "EUR", "default_kw": 150, "type": "public", "category": "Rapid", "network": "European"},
    "Electra+": {"energy": 0.49, "time": 0.00, "currency": "EUR", "default_kw": 150, "type": "public", "category": "Rapid", "network": "European"},
    "Freshmile": {"energy": 0.25, "time": 0.05, "currency": "EUR", "default_kw": 50, "type": "public", "category": "Fast", "network": "European"},
    "Home - Octopus Intelligent": {"energy": 0.08, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home", "category": "Home", "network": "Domestic"},
    "Home - E.ON Drive": {"energy": 0.09, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home", "category": "Home", "network": "Domestic"},
    "Home - EDF Standard": {"energy": 0.10, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home", "category": "Home", "network": "Domestic"},
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_data(ttl=Config.CACHE_TTL)
def fetch_exchange_rates() -> Dict[str, float]:
    """Fetch live exchange rates with fallback"""
    fallback_rates = {"EUR": 1.0, "GBP": 0.87, "USD": 1.10, "_date": "fallback", "_status": "Using fallback rates"}
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest?from=EUR&to=GBP,USD",
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        return {"EUR": 1.0, "GBP": float(rates.get("GBP", fallback_rates["GBP"])), "USD": float(rates.get("USD", fallback_rates["USD"])), "_date": data.get("date","unknown"), "_status":"Live rates"}
    except Exception:
        st.warning("⚠️ Unable to fetch live exchange rates. Using fallback values.")
        return fallback_rates


def convert_currency(amount: float, from_currency: str, to_currency: str, rates: Dict) -> float:
    """Convert between currencies using rates"""
    if from_currency == to_currency:
        return amount
    if from_currency not in rates or to_currency not in rates:
        return amount
    eur_amount = amount if from_currency == "EUR" else amount / rates[from_currency]
    return eur_amount * rates[to_currency]


def calculate_charging_time(battery_kwh: float, effective_kw: float, start_pct: float, end_pct: float, apply_taper: bool=True) -> float:
    """Calculate charging time (minutes) with tapering"""
    if effective_kw <= 0 or end_pct <= start_pct:
        return 0.0
    total_minutes = 0.0
    current_pct = float(start_pct)
    while current_pct < end_pct:
        if apply_taper:
            if current_pct < 80:
                power_rate = effective_kw
                next_milestone = min(end_pct, 80)
            elif current_pct < 90:
                power_rate = effective_kw * 0.5
                next_milestone = min(end_pct, 90)
            else:
                power_rate = effective_kw * 0.3
                next_milestone = end_pct
        else:
            power_rate = effective_kw
            next_milestone = end_pct
        pct_segment = (next_milestone - current_pct) / 100.0
        energy_segment = battery_kwh * pct_segment
        segment_minutes = (energy_segment / max(power_rate,0.1)) * 60.0
        total_minutes += segment_minutes
        current_pct = next_milestone
    return total_minutes


def calculate_charging_cost(energy_kwh: float, time_minutes: float, energy_price: float, time_price: float, session_fee: float) -> float:
    """Calculate total cost"""
    return energy_kwh * energy_price + time_minutes * time_price + session_fee


def format_time(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f} min"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m"


def format_currency(amount: float, currency: str) -> str:
    symbols = {"GBP": "£", "EUR": "€", "USD": "$"}
    return f"{symbols.get(currency, currency)}{amount:.2f}"


@st.cache_data(ttl=Config.CACHE_TTL)
def geocode_postcode(postcode: str) -> Optional[Tuple[float, float]]:
    geolocator = Nominatim(user_agent="ev_charge_pro_app")
    try:
        loc = geolocator.geocode(postcode)
        if loc:
            return (loc.latitude, loc.longitude)
        return None
    except Exception:
        return None


# ============================================================================
# STYLING
# ============================================================================

def apply_custom_styles():
    st.markdown("""
    <style>
    /* CSS styles here (your full CSS unchanged) */
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_hero_section():
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-title">{Config.APP_ICON} EV Charge Pro UK</div>
        <div class="hero-subtitle">Professional EV charging cost comparison • Compare providers • Calculate savings</div>
    </div>
    """, unsafe_allow_html=True)


def render_location_input():
    """Render postcode input and map"""
    st.markdown("### 🗺️ Your Charging Location")
    postcode = st.text_input("Enter your UK postcode", placeholder="e.g., SW1A 1AA")
    if postcode:
        coords = geocode_postcode(postcode)
        if coords:
            lat, lon = coords
            st.success(f"📍 Postcode located at: {lat:.5f}, {lon:.5f}")
            m = folium.Map(location=[lat, lon], zoom_start=14)
            folium.Marker([lat, lon], tooltip="Your location", icon=folium.Icon(color="blue")).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.error("❌ Could not find that postcode. Please check your input.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title=Config.APP_TITLE, page_icon=Config.APP_ICON, layout=Config.PAGE_LAYOUT)
    apply_custom_styles()
    render_hero_section()
    render_location_input()
    # ... Your existing code for vehicle selection, session config, providers, and results goes here
    # e.g., battery_kwh, car_max_kw = render_vehicle_selector(ios_safe_mode=False)
    # ... etc.

if __name__ == "__main__":
    main()
