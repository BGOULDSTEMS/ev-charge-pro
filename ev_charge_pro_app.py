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

import streamlit as st

import folium
from streamlit_folium 
import st_folium
import geopy
from geopy.geocoders 
import Nominatim

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


# Vehicle database with comprehensive specifications
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

# Comprehensive charging provider database
CHARGING_PROVIDERS = {
    # Rapid Charging Networks (UK)
    "MFG EV Power": {
        "energy": 0.79, "time": 0.00, "currency": "GBP", "default_kw": 150, 
        "type": "public", "category": "Rapid", "network": "Regional"
    },
    "EVYVE Charging Stations": {
        "energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "Regional"
    },
    "Osprey Charging (App)": {
        "energy": 0.82, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "National"
    },
    "Osprey Charging (Contactless)": {
        "energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "National"
    },
    "Electroverse": {
        "energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Roaming", "network": "Multi-Network"
    },
    "Zapmap Zap-Pay": {
        "energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Roaming", "network": "Multi-Network"
    },
    "Plugsurfing": {
        "energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Roaming", "network": "Multi-Network"
    },
    "BP Pulse PAYG": {
        "energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "National"
    },
    "Pod Point": {
        "energy": 0.69, "time": 0.00, "currency": "GBP", "default_kw": 75,
        "type": "public", "category": "Fast", "network": "National"
    },
    
    # European Networks
    "IZIVIA Pass": {
        "energy": 0.75, "time": 0.00, "currency": "EUR", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "European"
    },
    "Electra+": {
        "energy": 0.49, "time": 0.00, "currency": "EUR", "default_kw": 150,
        "type": "public", "category": "Rapid", "network": "European"
    },
    "Freshmile": {
        "energy": 0.25, "time": 0.05, "currency": "EUR", "default_kw": 50,
        "type": "public", "category": "Fast", "network": "European"
    },
    
    # Home Charging Options
    "Home - Octopus Intelligent": {
        "energy": 0.08, "time": 0.00, "currency": "GBP", "default_kw": 7,
        "type": "home", "category": "Home", "network": "Domestic"
    },
    "Home - E.ON Drive": {
        "energy": 0.09, "time": 0.00, "currency": "GBP", "default_kw": 7,
        "type": "home", "category": "Home", "network": "Domestic"
    },
    "Home - EDF Standard": {
        "energy": 0.10, "time": 0.00, "currency": "GBP", "default_kw": 7,
        "type": "home", "category": "Home", "network": "Domestic"
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_data(ttl=Config.CACHE_TTL)
def fetch_exchange_rates() -> Dict[str, float]:
    """
    Fetch live exchange rates from Frankfurter API
    Returns EUR-based rates with fallback values
    """
    fallback_rates = {
        "EUR": 1.0, 
        "GBP": 0.87, 
        "USD": 1.10, 
        "_date": "fallback",
        "_status": "Using fallback rates"
    }
    
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest?from=EUR&to=GBP,USD",
            timeout=Config.API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        
        return {
            "EUR": 1.0,
            "GBP": float(rates.get("GBP", fallback_rates["GBP"])),
            "USD": float(rates.get("USD", fallback_rates["USD"])),
            "_date": data.get("date", "unknown"),
            "_status": "Live rates"
        }
    except Exception as e:
        st.warning(f"⚠️ Unable to fetch live exchange rates. Using fallback values.")
        return fallback_rates


def convert_currency(amount: float, from_currency: str, to_currency: str, rates: Dict) -> float:
    """Convert amount between currencies using provided exchange rates"""
    if from_currency == to_currency:
        return amount
    
    if from_currency not in rates or to_currency not in rates:
        return amount
    
    # Convert to EUR first, then to target currency
    eur_amount = amount if from_currency == "EUR" else amount / rates[from_currency]
    return eur_amount * rates[to_currency]


def calculate_charging_time(
    battery_kwh: float,
    effective_kw: float,
    start_pct: float,
    end_pct: float,
    apply_taper: bool = True
) -> float:
    """
    Calculate charging time in minutes with optional power tapering model
    
    Taper model:
    - 0-80%: Full power
    - 80-90%: 50% power
    - 90-100%: 30% power
    """
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
        
        # Calculate energy for this segment
        pct_segment = (next_milestone - current_pct) / 100.0
        energy_segment = battery_kwh * pct_segment
        
        # Calculate time for this segment
        segment_minutes = (energy_segment / max(power_rate, 0.1)) * 60.0
        total_minutes += segment_minutes
        
        current_pct = next_milestone
    
    return total_minutes


def calculate_charging_cost(
    energy_kwh: float,
    time_minutes: float,
    energy_price: float,
    time_price: float,
    session_fee: float
) -> float:
    """Calculate total charging cost based on energy, time, and session fees"""
    energy_cost = energy_kwh * energy_price
    time_cost = time_minutes * time_price
    total_cost = energy_cost + time_cost + session_fee
    return total_cost


def format_time(minutes: float) -> str:
    """Format minutes into a human-readable string"""
    if minutes < 60:
        return f"{minutes:.0f} min"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"


def format_currency(amount: float, currency: str) -> str:
    """Format amount with currency symbol"""
    symbols = {"GBP": "£", "EUR": "€", "USD": "$"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"

@st.cache_data(ttl=Config.CACHE_TTL)
def geocode_postcode(postcode: str) -> Optional[Tuple[float, float]]:
    """
    Convert a UK postcode to latitude and longitude using Nominatim
    Returns (lat, lon) or None if not found
    """
    geolocator = Nominatim(user_agent="ev_charge_pro_app")
    try:
        location = geolocator.geocode(postcode)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception:
        return None
        
# ============================================================================
# STYLING
# ============================================================================

def apply_custom_styles():
    """Apply professional custom CSS styling"""
    st.markdown("""
        <style>
        /* Import Professional Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Root Variables */
        :root {
            --bg-primary: #0a0e1a;
            --bg-secondary: #0f1419;
            --bg-card: rgba(15, 20, 30, 0.95);
            --border-color: rgba(139, 173, 240, 0.15);
            --text-primary: #ffffff;
            --text-secondary: #a0aec0;
            --accent-primary: #00ADF0;
            --accent-secondary: #2182FF;
            --success: #10B981;
            --warning: #F59E0B;
        }
        
        /* Global Styles */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
            color: var(--text-primary);
        }
        
        /* Main App Container */
        .stApp {
            background: 
                radial-gradient(circle at 20% 10%, rgba(0, 173, 240, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(33, 130, 255, 0.08) 0%, transparent 50%),
                linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        }
        
        /* Block Container */
        .block-container {
            max-width: 1400px;
            padding: 2rem 1rem;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        
        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 1.875rem !important; }
        h3 { font-size: 1.5rem !important; }
        
        /* Professional Card Design */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: rgba(139, 173, 240, 0.3);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
        }
        
        /* Hero Section */
        .hero-section {
            background: linear-gradient(135deg, rgba(0, 173, 240, 0.1) 0%, rgba(33, 130, 255, 0.1) 100%);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00ADF0 0%, #2182FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            color: var(--text-secondary);
            margin-bottom: 0;
        }
        def render_location_input():
    """Render postcode input and display location map"""
    st.markdown("### 🗺️ Your Charging Location")
    
    postcode = st.text_input(
        "Enter your UK postcode",
        placeholder="e.g., SW1A 1AA",
        help="Optional: Enter your postcode to visualise nearby charging"
    )
    
    if postcode:
        coords = geocode_postcode(postcode)
        if coords:
            lat, lon = coords
            st.success(f"📍 Postcode located at: {lat:.5f}, {lon:.5f}")
            
            # Create a Folium map centered on the postcode
            m = folium.Map(location=[lat, lon], zoom_start=14)
            folium.Marker([lat, lon], tooltip="Your location", icon=folium.Icon(color="blue")).add_to(m)
            
            st_folium(m, width=700, height=500)
        else:
            st.error("❌ Could not find that postcode. Please check your input.")

            render_hero_section()
render_location_input()
        
        /* Metrics */
        div[data-testid="stMetric"] {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stMetric"]:hover {
            border-color: var(--accent-primary);
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        div[data-testid="stMetricValue"] {
            color: var(--text-primary) !important;
            font-size: 1.875rem;
            font-weight: 700;
        }
        
        div[data-testid="stMetricDelta"] {
            font-size: 0.875rem;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 173, 240, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 173, 240, 0.4);
        }
        
        /* Form Inputs */
        .stSelectbox, .stNumberInput, .stTextInput {
            margin-bottom: 1rem;
        }
        
        label {
            color: var(--text-primary) !important;
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        /* Input Fields with Black Text */
        input, select, textarea {
            background: rgba(255, 255, 255, 0.95) !important;
            color: #1a1a1a !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        /* Dropdown Options */
        [data-baseweb="select"] * {
            color: #1a1a1a !important;
        }
        
        div[role="listbox"] *,
        div[role="option"] {
            color: #1a1a1a !important;
            background: white !important;
        }
        
        /* Slider Styling */
        .stSlider {
            padding: 1rem 0;
        }
        
        /* Checkbox & Radio */
        .stCheckbox label, .stRadio label {
            color: var(--text-primary) !important;
        }
        
        /* Dataframe */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            color: var(--text-primary) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            color: var(--text-secondary);
            padding: 0.75rem 1.5rem;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: white;
        }
        
        /* Info/Warning/Success Messages */
        .stAlert {
            border-radius: 12px;
            border-left: 4px solid;
        }
        
        /* Caption Text */
        .stCaption, .caption-text {
            color: var(--text-secondary) !important;
            font-size: 0.875rem;
        }
        
        /* Divider */
        hr {
            border-color: var(--border-color);
            margin: 2rem 0;
        }
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem 0.5rem;
            }
            
            .hero-title {
                font-size: 2rem;
            }
            
            .hero-subtitle {
                font-size: 1rem;
            }
        }
        
        /* Custom Classes */
        .info-badge {
            display: inline-block;
            background: rgba(0, 173, 240, 0.2);
            color: var(--accent-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .success-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .warning-badge {
            display: inline-block;
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_hero_section():
    """Render the hero section with app title and description"""
    st.markdown(f"""
        <div class="hero-section">
            <div class="hero-title">{Config.APP_ICON} EV Charge Pro UK</div>
            <div class="hero-subtitle">
                Professional EV charging cost comparison • Compare providers • Calculate savings
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_vehicle_selector(ios_safe_mode: bool) -> Tuple[float, float]:
    """
    Render vehicle selection interface
    Returns: (battery_kwh, car_max_kw)
    """
    st.markdown("### 🚗 Vehicle Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        vehicle_name = st.selectbox(
            "Select Your Vehicle",
            VEHICLE_DATABASE["model"].tolist(),
            index=7,
            help="Choose your EV model or select 'Custom Vehicle' for manual input"
        )
    
    vehicle_data = VEHICLE_DATABASE[VEHICLE_DATABASE["model"] == vehicle_name].iloc[0]
    default_battery = float(vehicle_data["battery_kwh"])
    default_max_kw = float(vehicle_data["max_dc_kw"])
    
    with col2:
        category = vehicle_data["category"]
        st.markdown(f'<span class="info-badge">{category}</span>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        if vehicle_name == "Custom Vehicle":
            battery_kwh = st.number_input(
                "Battery Capacity (kWh)",
                min_value=10.0,
                max_value=220.0,
                value=80.0,
                step=1.0,
                help="Enter your vehicle's battery capacity"
            )
        else:
            battery_kwh = st.number_input(
                "Battery Capacity (kWh)",
                min_value=10.0,
                max_value=220.0,
                value=default_battery,
                step=0.1,
                help="Adjust if your model has a different battery size"
            )
    
    with col4:
        if ios_safe_mode:
            car_max_kw = st.number_input(
                "Max DC Charging (kW)",
                min_value=20,
                max_value=400,
                value=int(default_max_kw),
                step=5,
                help="Maximum DC fast charging power your vehicle supports"
            )
        else:
            car_max_kw = st.slider(
                "Max DC Charging (kW)",
                min_value=20,
                max_value=400,
                value=int(default_max_kw),
                step=5,
                help="Maximum DC fast charging power your vehicle supports"
            )
    
    return float(battery_kwh), float(car_max_kw)


def render_charging_session_config(ios_safe_mode: bool) -> Tuple:
    """
    Render charging session configuration
    Returns: (start_pct, end_pct, efficiency_loss, apply_taper, miles_per_kwh)
    """
    st.markdown("### ⚡ Charging Session Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if ios_safe_mode:
            start_pct = st.number_input(
                "Current State of Charge (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                help="Your battery level at the start of charging"
            )
        else:
            start_pct = st.slider(
                "Current State of Charge (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=1,
                help="Your battery level at the start of charging"
            )
    
    with col2:
        if ios_safe_mode:
            end_pct = st.number_input(
                "Target State of Charge (%)",
                min_value=0,
                max_value=100,
                value=80,
                step=5,
                help="Your desired battery level after charging"
            )
        else:
            end_pct = st.slider(
                "Target State of Charge (%)",
                min_value=0,
                max_value=100,
                value=80,
                step=1,
                help="Your desired battery level after charging"
            )
    
    with col3:
        if ios_safe_mode:
            efficiency_loss = st.number_input(
                "Charging Loss (%)",
                min_value=0,
                max_value=20,
                value=Config.DEFAULT_EFFICIENCY_LOSS,
                step=1,
                help="Typical energy loss during charging (heat, conversion)"
            )
        else:
            efficiency_loss = st.slider(
                "Charging Loss (%)",
                min_value=0,
                max_value=20,
                value=Config.DEFAULT_EFFICIENCY_LOSS,
                step=1,
                help="Typical energy loss during charging (heat, conversion)"
            )
    
    col4, col5 = st.columns(2)
    
    with col4:
        apply_taper = st.checkbox(
            "Apply Charging Curve Taper",
            value=True,
            help="Simulate realistic power reduction above 80% SoC"
        )
    
    with col5:
        miles_per_kwh = st.number_input(
            "Efficiency (mi/kWh)",
            min_value=1.0,
            max_value=7.0,
            value=Config.DEFAULT_MILES_PER_KWH,
            step=0.1,
            help="Your vehicle's typical efficiency"
        )
    
    return start_pct, end_pct, efficiency_loss, apply_taper, miles_per_kwh


def render_provider_configuration(
    label: str,
    key_prefix: str,
    car_max_kw: float,
    ios_safe_mode: bool
) -> Dict:
    """
    Render configuration controls for a charging provider
    Returns dictionary with provider settings
    """
    st.markdown(f"#### {label}")
    
    # Provider selection with category grouping
    provider_list = list(CHARGING_PROVIDERS.keys())
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        provider_name = st.selectbox(
            f"{label} - Select Provider",
            provider_list,
            key=f"{key_prefix}_name",
            help="Choose a charging network or provider"
        )
    
    preset = CHARGING_PROVIDERS[provider_name]
    
    with col2:
        category = preset.get("category", "Unknown")
        network = preset.get("network", "")
        st.markdown(f'<span class="info-badge">{category}</span>', unsafe_allow_html=True)
        if network:
            st.caption(f"Network: {network}")
    
    # Currency selection
    currency = st.selectbox(
        f"{label} - Currency",
        ["GBP", "EUR", "USD"],
        index=["GBP", "EUR", "USD"].index(preset["currency"]) if preset["currency"] in ["GBP", "EUR", "USD"] else 0,
        key=f"{key_prefix}_currency",
    )
    
    # Charger capacity
    if ios_safe_mode:
        station_kw = st.number_input(
            f"{label} - Charger Power (kW)",
            min_value=3,
            max_value=400,
            value=min(400, int(preset["default_kw"])),
            step=5,
            key=f"{key_prefix}_kw",
            help="Power rating of the charging station"
        )
    else:
        station_kw = st.slider(
            f"{label} - Charger Power (kW)",
            min_value=3,
            max_value=400,
            value=min(400, int(preset["default_kw"])),
            step=1,
            key=f"{key_prefix}_kw",
            help="Power rating of the charging station"
        )
    
    # Pricing configuration
    if preset["type"] == "home":
        # Home charging uses pence/kWh for easier input
        if ios_safe_mode:
            home_pence = st.number_input(
                f"{label} - Tariff Rate (p/kWh)",
                min_value=5,
                max_value=50,
                value=max(5, min(50, int(round(preset["energy"] * 100)))),
                step=1,
                key=f"{key_prefix}_home_pence",
                help="Your electricity tariff rate"
            )
        else:
            home_pence = st.slider(
                f"{label} - Tariff Rate (p/kWh)",
                min_value=5,
                max_value=50,
                value=max(5, min(50, int(round(preset["energy"] * 100)))),
                step=1,
                key=f"{key_prefix}_home_pence",
                help="Your electricity tariff rate"
            )
        energy_price = float(home_pence) / 100.0
        time_price = 0.0
        session_fee = 0.0
    else:
        # Public charging
        col_energy, col_time = st.columns(2)
        
        with col_energy:
            if ios_safe_mode:
                energy_price = st.number_input(
                    f"{label} - Energy Price ({currency}/kWh)",
                    min_value=0.00,
                    max_value=2.00,
                    value=float(preset["energy"]),
                    step=0.01,
                    key=f"{key_prefix}_energy",
                    help="Cost per kilowatt-hour"
                )
            else:
                energy_price = st.slider(
                    f"{label} - Energy Price ({currency}/kWh)",
                    min_value=0.00,
                    max_value=2.00,
                    value=float(preset["energy"]),
                    step=0.01,
                    key=f"{key_prefix}_energy",
                    help="Cost per kilowatt-hour"
                )
        
        with col_time:
            use_per_min = st.checkbox(
                "Time-based Charging",
                value=bool(preset["time"] > 0),
                key=f"{key_prefix}_use_per_min",
                help="Some providers charge per minute"
            )
            
            if use_per_min:
                if ios_safe_mode:
                    time_price = st.number_input(
                        f"Time Price ({currency}/min)",
                        min_value=0.00,
                        max_value=1.00,
                        value=float(max(preset["time"], 0.01)),
                        step=0.01,
                        key=f"{key_prefix}_time",
                    )
                else:
                    time_price = st.slider(
                        f"Time Price ({currency}/min)",
                        min_value=0.00,
                        max_value=1.00,
                        value=float(max(preset["time"], 0.01)),
                        step=0.01,
                        key=f"{key_prefix}_time",
                    )
            else:
                time_price = 0.0
        
        # Session fee
        if ios_safe_mode:
            session_fee = st.number_input(
                f"{label} - Connection Fee ({currency})",
                min_value=0.00,
                max_value=10.00,
                value=0.00,
                step=0.25,
                key=f"{key_prefix}_session",
                help="One-time fee per charging session"
            )
        else:
            session_fee = st.slider(
                f"{label} - Connection Fee ({currency})",
                min_value=0.00,
                max_value=10.00,
                value=0.00,
                step=0.05,
                key=f"{key_prefix}_session",
                help="One-time fee per charging session"
            )
    
    # Calculate effective power
    effective_kw = min(float(station_kw), float(car_max_kw))
    
    # Display effective power info
    if effective_kw < station_kw:
        st.info(f"ℹ️ Charging limited by vehicle: {effective_kw:.0f}kW (station: {station_kw:.0f}kW, vehicle max: {car_max_kw:.0f}kW)")
    else:
        st.caption(f"Effective charging power: {effective_kw:.0f}kW")
    
    return {
        "provider": provider_name,
        "currency": currency,
        "station_kw": float(station_kw),
        "effective_kw": effective_kw,
        "energy_price": float(energy_price),
        "time_price": float(time_price),
        "session_fee": float(session_fee),
    }


def render_results(
    battery_kwh: float,
    start_pct: float,
    end_pct: float,
    efficiency_loss: float,
    miles_per_kwh: float,
    apply_taper: bool,
    provider_a: Dict,
    provider_b: Dict,
    comparison_currency: str,
    rates: Dict
):
    """Render comprehensive results comparison"""
    
    # Calculate energy needed
    energy_needed = battery_kwh * ((end_pct - start_pct) / 100.0)
    energy_needed *= (1.0 + efficiency_loss / 100.0)
    
    # Calculate charging times
    time_a = calculate_charging_time(battery_kwh, provider_a["effective_kw"], start_pct, end_pct, apply_taper)
    time_b = calculate_charging_time(battery_kwh, provider_b["effective_kw"], start_pct, end_pct, apply_taper)
    
    # Calculate costs in native currencies
    native_cost_a = calculate_charging_cost(
        energy_needed, time_a,
        provider_a["energy_price"], provider_a["time_price"], provider_a["session_fee"]
    )
    native_cost_b = calculate_charging_cost(
        energy_needed, time_b,
        provider_b["energy_price"], provider_b["time_price"], provider_b["session_fee"]
    )
    
    # Convert to comparison currency
    total_cost_a = convert_currency(native_cost_a, provider_a["currency"], comparison_currency, rates)
    total_cost_b = convert_currency(native_cost_b, provider_b["currency"], comparison_currency, rates)
    
    # Calculate per-mile costs
    miles_added = energy_needed * miles_per_kwh
    cost_per_100mi_a = (total_cost_a / miles_added * 100.0) if miles_added > 0 else 0.0
    cost_per_100mi_b = (total_cost_b / miles_added * 100.0) if miles_added > 0 else 0.0
    
    # Determine winner
    savings = abs(total_cost_a - total_cost_b)
    if total_cost_a < total_cost_b:
        winner = provider_a["provider"]
        winner_cost = total_cost_a
        loser_cost = total_cost_b
    else:
        winner = provider_b["provider"]
        winner_cost = total_cost_b
        loser_cost = total_cost_a
    
    savings_pct = (savings / loser_cost * 100) if loser_cost > 0 else 0
    
    # Display Results
    st.markdown("---")
    st.markdown("## 📊 Comparison Results")
    
    # Summary metrics
    st.markdown("### Session Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Energy Delivered",
            f"{energy_needed:.2f} kWh",
            help="Total energy added to battery (including charging losses)"
        )
    
    with col2:
        st.metric(
            "Range Added",
            f"{miles_added:.1f} mi",
            help="Estimated range based on your efficiency setting"
        )
    
    with col3:
        st.metric(
            f"{provider_a['provider'][:15]}",
            format_time(time_a),
            delta=None,
            help="Time to complete charging session"
        )
    
    with col4:
        st.metric(
            f"{provider_b['provider'][:15]}",
            format_time(time_b),
            delta=None,
            help="Time to complete charging session"
        )
    
    # Cost comparison
    st.markdown("### Cost Comparison")
    
    col5, col6, col7 = st.columns([1, 1, 1])
    
    with col5:
        delta_a = f"-{format_currency(savings, comparison_currency)}" if total_cost_a < total_cost_b else None
        st.metric(
            f"💰 {provider_a['provider']}",
            format_currency(total_cost_a, comparison_currency),
            delta=delta_a,
            delta_color="normal",
            help=f"Total cost • {cost_per_100mi_a:.2f} {comparison_currency}/100mi"
        )
        st.caption(f"Per 100 miles: {format_currency(cost_per_100mi_a, comparison_currency)}")
    
    with col6:
        delta_b = f"-{format_currency(savings, comparison_currency)}" if total_cost_b < total_cost_a else None
        st.metric(
            f"💰 {provider_b['provider']}",
            format_currency(total_cost_b, comparison_currency),
            delta=delta_b,
            delta_color="normal",
            help=f"Total cost • {cost_per_100mi_b:.2f} {comparison_currency}/100mi"
        )
        st.caption(f"Per 100 miles: {format_currency(cost_per_100mi_b, comparison_currency)}")
    
    with col7:
        st.metric(
            "💵 Potential Savings",
            format_currency(savings, comparison_currency),
            delta=f"{savings_pct:.1f}%",
            delta_color="normal",
            help="Cost difference between providers"
        )
        st.markdown(f'<span class="success-badge">Choose {winner}</span>', unsafe_allow_html=True)
    
    # Detailed breakdown
    st.markdown("### Detailed Cost Breakdown")
    
    breakdown_data = []
    
    for provider, cost, time, native, label in [
        (provider_a, total_cost_a, time_a, native_cost_a, "Provider A"),
        (provider_b, total_cost_b, time_b, native_cost_b, "Provider B")
    ]:
        energy_component = energy_needed * provider["energy_price"]
        time_component = time * provider["time_price"]
        
        breakdown_data.append({
            "Provider": provider["provider"],
            "Network": CHARGING_PROVIDERS[provider["provider"]].get("network", "N/A"),
            "Power (kW)": f"{provider['effective_kw']:.0f}",
            "Duration": format_time(time),
            "Energy Cost": format_currency(energy_component, provider["currency"]),
            "Time Cost": format_currency(time_component, provider["currency"]) if time_component > 0 else "—",
            "Session Fee": format_currency(provider["session_fee"], provider["currency"]) if provider["session_fee"] > 0 else "—",
            f"Total ({provider['currency']})": format_currency(native, provider["currency"]),
            f"Total ({comparison_currency})": format_currency(cost, comparison_currency),
        })
    
    breakdown_df = pd.DataFrame(breakdown_data)
    st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
    
    # Cost progression chart
    st.markdown("### 📈 Cost Progression Chart")
    st.caption("How costs accumulate as you charge from your starting point to 100%")
    
    charge_levels = np.linspace(start_pct, 100, 30)
    costs_a = []
    costs_b = []
    
    for charge_pct in charge_levels:
        # Provider A
        energy_a = battery_kwh * ((charge_pct - start_pct) / 100.0) * (1.0 + efficiency_loss / 100.0)
        time_a_curve = calculate_charging_time(battery_kwh, provider_a["effective_kw"], start_pct, charge_pct, apply_taper)
        native_a = calculate_charging_cost(energy_a, time_a_curve, provider_a["energy_price"], provider_a["time_price"], provider_a["session_fee"])
        costs_a.append(convert_currency(native_a, provider_a["currency"], comparison_currency, rates))
        
        # Provider B
        energy_b = battery_kwh * ((charge_pct - start_pct) / 100.0) * (1.0 + efficiency_loss / 100.0)
        time_b_curve = calculate_charging_time(battery_kwh, provider_b["effective_kw"], start_pct, charge_pct, apply_taper)
        native_b = calculate_charging_cost(energy_b, time_b_curve, provider_b["energy_price"], provider_b["time_price"], provider_b["session_fee"])
        costs_b.append(convert_currency(native_b, provider_b["currency"], comparison_currency, rates))
    
    chart_data = pd.DataFrame({
        "Battery Level (%)": charge_levels,
        f"{provider_a['provider'][:20]}": costs_a,
        f"{provider_b['provider'][:20]}": costs_b,
    })
    
    st.line_chart(chart_data.set_index("Battery Level (%)"), use_container_width=True)
    
    # Additional insights
    with st.expander("💡 Key Insights & Recommendations"):
        st.markdown(f"""
        **Cost Analysis:**
        - **Cheapest Option**: {winner} saves you {format_currency(savings, comparison_currency)} ({savings_pct:.1f}% less)
        - **Per-Mile Cost**: {format_currency(min(cost_per_100mi_a, cost_per_100mi_b), comparison_currency)}/100mi (best rate)
        
        **Charging Speed:**
        - **Provider A**: {provider_a['effective_kw']:.0f}kW → {format_time(time_a)}
        - **Provider B**: {provider_b['effective_kw']:.0f}kW → {format_time(time_b)}
        
        **💡 Optimization Tips:**
        - Charging to 80% is typically most cost-effective due to power tapering above this level
        - Home charging is significantly cheaper for daily top-ups
        - Consider roaming apps like Electroverse or Zapmap for access to multiple networks
        - Plan charging stops on longer journeys using the cheapest available networks
        """)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title=Config.APP_TITLE,
        page_icon=Config.APP_ICON,
        layout=Config.PAGE_LAYOUT,
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom styling
    apply_custom_styles()
    
    # Fetch exchange rates
    exchange_rates = fetch_exchange_rates()
    
    # Hero section
    render_hero_section()
    
    # Main content area
    with st.container():
        # iOS safe mode toggle (for slider vs input preference)
        col_toggle, col_rates = st.columns([1, 2])
        with col_toggle:
            ios_safe_mode = st.toggle(
                "📱 iOS-Friendly Inputs",
                value=True,
                help="Use number inputs instead of sliders to prevent accidental changes while scrolling"
            )
        
        with col_rates:
            rate_status = exchange_rates.get("_status", "Unknown")
            rate_date = exchange_rates.get("_date", "Unknown")
            st.caption(f"💱 Exchange rates: {rate_status} • Updated: {rate_date}")
        
        st.markdown("---")
        
        # Vehicle configuration
        with st.container():
            battery_kwh, car_max_kw = render_vehicle_selector(ios_safe_mode)
        
        st.markdown("---")
        
        # Charging session configuration
        with st.container():
            start_pct, end_pct, efficiency_loss, apply_taper, miles_per_kwh = render_charging_session_config(ios_safe_mode)
        
        # Comparison currency
        comparison_currency = st.selectbox(
            "💵 Display Results In",
            ["GBP", "EUR", "USD"],
            index=0,
            help="All costs will be converted to this currency for comparison"
        )
        
        st.markdown("---")
        
        # Provider comparison section
        st.markdown("## 🔌 Charging Provider Comparison")
        st.caption("Configure two providers to compare costs, charging times, and savings")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            with st.container():
                provider_a = render_provider_configuration("Provider A", "provider_a", car_max_kw, ios_safe_mode)
        
        with col_b:
            with st.container():
                provider_b = render_provider_configuration("Provider B", "provider_b", car_max_kw, ios_safe_mode)
        
        # Compare button
        st.markdown("---")
        compare_button = st.button(
            "🔍 Compare Providers",
            type="primary",
            use_container_width=True,
            help="Calculate and compare charging costs"
        )
        
        # Results section
        if compare_button:
            if end_pct <= start_pct:
                st.error("❌ Target charge level must be greater than current charge level")
            else:
                with st.spinner("Calculating costs and generating comparison..."):
                    render_results(
                        battery_kwh, start_pct, end_pct, efficiency_loss, miles_per_kwh,
                        apply_taper, provider_a, provider_b, comparison_currency, exchange_rates
                    )
    # ============================================================================
# ROUTE PLANNER MODULE (IONITY STYLE)
# ============================================================================

import folium
from streamlit_folium import st_folium
import openrouteservice
from openrouteservice import convert

st.markdown("---")
st.markdown("## 🗺 EV Route Planner")
st.caption("Plan long journeys • Estimate charging stops • Visual route mapping")

with st.container():

    col_r1, col_r2, col_r3 = st.columns([2,2,1])

    with col_r1:
        start_location = st.text_input("Start Location", "Eastbourne")

    with col_r2:
        end_location = st.text_input("Destination", "Manchester")

    with col_r3:
        plan_route = st.button("Plan Route", use_container_width=True)

    if plan_route:

        ORS_API_KEY = st.secrets.get("ORS_API_KEY", None)

        if not ORS_API_KEY:
            st.error("Missing OpenRouteService API key. Add ORS_API_KEY to Streamlit secrets.")
        else:

            try:
                client = openrouteservice.Client(key=ORS_API_KEY)

                # Geocode start & end
                start_geo = client.pelias_search(text=start_location)["features"][0]["geometry"]["coordinates"]
                end_geo = client.pelias_search(text=end_location)["features"][0]["geometry"]["coordinates"]

                route = client.directions(
                    coordinates=[start_geo, end_geo],
                    profile="driving-car",
                    format="geojson"
                )

                distance_km = route["features"][0]["properties"]["summary"]["distance"] / 1000
                duration_min = route["features"][0]["properties"]["summary"]["duration"] / 60

                distance_miles = distance_km * 0.621371

                # Real world max range (10–80% window)
                usable_battery = battery_kwh * 0.70
                max_range = usable_battery * miles_per_kwh

                required_stops = max(0, int(distance_miles // max_range))

                # Estimate energy required
                total_energy_needed = distance_miles / miles_per_kwh

                # Estimate cost using Provider A
                energy_price = provider_a["energy_price"]
                est_cost_native = total_energy_needed * energy_price

                est_cost = convert_currency(
                    est_cost_native,
                    provider_a["currency"],
                    comparison_currency,
                    exchange_rates
                )

                # Display Metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                col_m1.metric("Distance", f"{distance_miles:.1f} mi")
                col_m2.metric("Drive Time", format_time(duration_min))
                col_m3.metric("Charging Stops Needed", required_stops)
                col_m4.metric("Estimated Charging Cost",
                              format_currency(est_cost, comparison_currency))

                # Map Rendering
                m = folium.Map(location=[start_geo[1], start_geo[0]], zoom_start=6)

                folium.GeoJson(route).add_to(m)

                folium.Marker(
                    [start_geo[1], start_geo[0]],
                    tooltip="Start",
                    icon=folium.Icon(color="green")
                ).add_to(m)

                folium.Marker(
                    [end_geo[1], end_geo[0]],
                    tooltip="Destination",
                    icon=folium.Icon(color="red")
                ).add_to(m)

                st_folium(m, width=1200, height=600)

            except Exception as e:
                st.error("Route calculation failed. Check locations or API key.")
   
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: var(--text-secondary); padding: 2rem 0;'>
            <p><strong>EV Charge Pro UK</strong> • Professional Edition</p>
            <p style='font-size: 0.875rem;'>
                Tariffs vary by location and time. Always verify pricing before charging.<br>
                Exchange rates provided by Frankfurter (ECB data) • Updated live
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
