"""
EV Charge Pro UK - Professional Edition
A comprehensive EV charging cost and route planning tool for the UK market
"""

from typing import Dict, Tuple, Optional, List, Set

import json
import requests
import numpy as np
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
from openrouteservice import convert

# ============================================================================
# CONFIGURATION & DATA
# ============================================================================

class Config:
    APP_TITLE = "EV Charge Pro UK"
    APP_ICON = "⚡"
    PAGE_LAYOUT = "wide"
    CACHE_TTL = 1800  # 30 minutes
    API_TIMEOUT = 8
    DEFAULT_MILES_PER_KWH = 3.5
    DEFAULT_EFFICIENCY_LOSS = 6  # percentage


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

CHARGING_PROVIDERS: Dict[str, Dict] = {
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

OCM_API_KEY = st.secrets.get("OCM_API_KEY")

NETWORK_TARIFF_MAP = {
    "bp pulse": "BP Pulse PAYG",
    "bp pulse payg": "BP Pulse PAYG",
    "osprey": "Osprey Charging (App)",
    "mfg ev power": "MFG EV Power",
    "motor fuel group": "MFG EV Power",
    "pod point": "Pod Point",
    "evyve": "EVYVE Charging Stations",
}

# ============================================================================
# HELPERS
# ============================================================================

def infer_tariff_from_operator(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    for needle, tariff in NETWORK_TARIFF_MAP.items():
        if needle in t:
            return tariff
    return None


@st.cache_data(ttl=Config.CACHE_TTL)
def fetch_nearby_chargers(
    lat: float,
    lon: float,
    distance_km: float = 10,
    max_results: int = 20,
) -> list:
    if not OCM_API_KEY:
        return []
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "countrycode": "GB",
        "latitude": lat,
        "longitude": lon,
        "distance": distance_km,
        "distanceunit": "KM",
        "maxresults": max_results,
        "compact": False,
        "verbose": True,
        "includeoperatorinfo": True,
    }
    try:
        resp = requests.get(
            url,
            params=params,
            headers={"X-API-Key": OCM_API_KEY},
            timeout=Config.API_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


@st.cache_data(ttl=Config.CACHE_TTL)
def fetch_exchange_rates() -> Dict[str, float]:
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
    except Exception:
        st.warning("⚠️ Unable to fetch live exchange rates. Using fallback values.")
        return fallback_rates


def convert_currency(amount: float, from_currency: str, to_currency: str, rates: Dict) -> float:
    if from_currency == to_currency:
        return amount
    if from_currency not in rates or to_currency not in rates:
        return amount
    eur_amount = amount if from_currency == "EUR" else amount / rates[from_currency]
    return eur_amount * rates[to_currency]


def calculate_charging_time(
    battery_kwh: float,
    effective_kw: float,
    start_pct: float,
    end_pct: float,
    apply_taper: bool = True
) -> float:
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
        location = geolocator.geocode(postcode)
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        pass
    return None


def pick_best_charger_stop(
    lon: float,
    lat: float,
    battery_kwh: float,
    miles_per_kwh: float,
    start_soc: float,
    end_soc: float,
    efficiency_loss: float,
    apply_taper: bool,
    car_max_kw: float,
    comparison_currency: str,
    exchange_rates: Dict,
    available_cards: Optional[Set[str]] = None,
) -> Optional[Dict]:
    pois = fetch_nearby_chargers(lat, lon, distance_km=5, max_results=10)
    if not pois:
        return None

    energy_needed = battery_kwh * ((end_soc - start_soc) / 100.0)
    energy_needed *= (1.0 + efficiency_loss / 100.0)
    if energy_needed <= 0:
        return None

    best = None

    for poi in pois:
        addr = poi.get("AddressInfo", {}) or {}
        op_info = poi.get("OperatorInfo") or {}
        operator_title = op_info.get("Title")
        site_title = addr.get("Title")
        display_operator = operator_title or site_title or "Unknown"

        lat_c = addr.get("Latitude")
        lon_c = addr.get("Longitude")

        connections = poi.get("Connections") or []
        power_kw = connections[0].get("PowerKW") if connections else None
        if not isinstance(power_kw, (int, float)):
            power_kw = 50.0
        effective_kw = min(float(power_kw), float(car_max_kw))

        search_text = f"{operator_title or ''} {site_title or ''}"
        tariff_name = infer_tariff_from_operator(search_text)
        if not tariff_name:
            continue
        if available_cards and tariff_name not in available_cards:
            continue

        preset = CHARGING_PROVIDERS.get(tariff_name)
        if not preset:
            continue

        time_min = calculate_charging_time(
            battery_kwh, effective_kw, start_soc, end_soc, apply_taper
        )
        native_cost = calculate_charging_cost(
            energy_needed,
            time_min,
            preset["energy"],
            preset["time"],
            0.0,
        )
        total_cost = convert_currency(
            native_cost,
            preset["currency"],
            comparison_currency,
            exchange_rates,
        )

        if best is None or total_cost < best["total_cost"]:
            best = {
                "charger_name": site_title or display_operator,
                "operator": display_operator,
                "lat": lat_c,
                "lon": lon_c,
                "power_kw": effective_kw,
                "card": tariff_name,
                "total_cost": total_cost,
                "time_min": time_min,
            }

    return best

# ============================================================================
# STYLING & UI
# ============================================================================

def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%);
            color: #ffffff;
        }
        .block-container {
            max-width: 1400px;
            padding: 2rem 1rem;
        }
        .hero-section {
            background: linear-gradient(135deg, rgba(0, 173, 240, 0.1) 0%, rgba(33, 130, 255, 0.1) 100%);
            border-radius: 20px;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            border: 1px solid rgba(139,173,240,0.15);
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
            color: #a0aec0;
        }
        .info-badge {
            display: inline-block;
            background: rgba(0, 173, 240, 0.2);
            color: #00ADF0;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .success-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: #10B981;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


def render_hero_section():
    st.markdown(f"""
        <div class="hero-section">
            <div class="hero-title">{Config.APP_ICON} EV Charge Pro UK</div>
            <div class="hero-subtitle">
                Professional EV charging cost comparison • Optimise chargers & cards • Plan long routes
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_vehicle_selector(ios_safe_mode: bool) -> Tuple[float, float]:
    st.markdown("### 🚗 Vehicle Configuration")
    col1, col2 = st.columns([2, 1])

    with col1:
        vehicle_name = st.selectbox(
            "Select Your Vehicle",
            VEHICLE_DATABASE["model"].tolist(),
            index=7,
        )

    vehicle_data = VEHICLE_DATABASE[VEHICLE_DATABASE["model"] == vehicle_name].iloc[0]
    default_battery = float(vehicle_data["battery_kwh"])
    default_max_kw = float(vehicle_data["max_dc_kw"])

    with col2:
        st.markdown(f'<span class="info-badge">{vehicle_data["category"]}</span>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        if vehicle_name == "Custom Vehicle":
            battery_kwh = st.number_input(
                "Battery Capacity (kWh)", 10.0, 220.0, 80.0, 1.0
            )
        else:
            battery_kwh = st.number_input(
                "Battery Capacity (kWh)", 10.0, 220.0, default_battery, 0.1
            )
    with col4:
        if ios_safe_mode:
            car_max_kw = st.number_input(
                "Max DC Charging (kW)", 20, 400, int(default_max_kw), 5
            )
        else:
            car_max_kw = st.slider(
                "Max DC Charging (kW)", 20, 400, int(default_max_kw), 5
            )
    return float(battery_kwh), float(car_max_kw)


def render_charging_session_config(ios_safe_mode: bool):
    st.markdown("### ⚡ Charging Session Parameters")
    col1, col2, col3 = st.columns(3)

    with col1:
        if ios_safe_mode:
            start_pct = st.number_input("Current SoC (%)", 0, 100, 20, 5)
        else:
            start_pct = st.slider("Current SoC (%)", 0, 100, 20, 1)

    with col2:
        if ios_safe_mode:
            end_pct = st.number_input("Target SoC (%)", 0, 100, 80, 5)
        else:
            end_pct = st.slider("Target SoC (%)", 0, 100, 80, 1)

    with col3:
        if ios_safe_mode:
            efficiency_loss = st.number_input(
                "Charging Loss (%)", 0, 20, Config.DEFAULT_EFFICIENCY_LOSS, 1
            )
        else:
            efficiency_loss = st.slider(
                "Charging Loss (%)", 0, 20, Config.DEFAULT_EFFICIENCY_LOSS, 1
            )

    col4, col5 = st.columns(2)
    with col4:
        apply_taper = st.checkbox("Apply Charging Curve Taper", True)
    with col5:
        miles_per_kwh = st.number_input(
            "Efficiency (mi/kWh)", 1.0, 7.0, Config.DEFAULT_MILES_PER_KWH, 0.1
        )

    return start_pct, end_pct, efficiency_loss, apply_taper, miles_per_kwh


def render_provider_configuration(
    label: str,
    key_prefix: str,
    car_max_kw: float,
    ios_safe_mode: bool
) -> Dict:
    st.markdown(f"#### {label}")
    provider_list = list(CHARGING_PROVIDERS.keys())
    col1, col2 = st.columns([2, 1])

    with col1:
        provider_name = st.selectbox(
            f"{label} - Select Provider",
            provider_list,
            key=f"{key_prefix}_name",
        )
    preset = CHARGING_PROVIDERS[provider_name]

    with col2:
        st.markdown(f'<span class="info-badge">{preset.get("category","")}</span>', unsafe_allow_html=True)
        net = preset.get("network")
        if net:
            st.caption(f"Network: {net}")

    currency = st.selectbox(
        f"{label} - Currency",
        ["GBP", "EUR", "USD"],
        index=["GBP", "EUR", "USD"].index(preset["currency"])
        if preset["currency"] in ["GBP", "EUR", "USD"] else 0,
        key=f"{key_prefix}_currency",
    )

    if ios_safe_mode:
        station_kw = st.number_input(
            f"{label} - Charger Power (kW)",
            3, 400, min(400, int(preset["default_kw"])), 5,
            key=f"{key_prefix}_kw",
        )
    else:
        station_kw = st.slider(
            f"{label} - Charger Power (kW)",
            3, 400, min(400, int(preset["default_kw"])), 1,
            key=f"{key_prefix}_kw",
        )

    if preset["type"] == "home":
        if ios_safe_mode:
            home_pence = st.number_input(
                f"{label} - Tariff Rate (p/kWh)",
                5, 50, max(5, min(50, int(round(preset["energy"] * 100)))), 1,
                key=f"{key_prefix}_home_pence",
            )
        else:
            home_pence = st.slider(
                f"{label} - Tariff Rate (p/kWh)",
                5, 50, max(5, min(50, int(round(preset["energy"] * 100)))), 1,
                key=f"{key_prefix}_home_pence",
            )
        energy_price = float(home_pence) / 100.0
        time_price = 0.0
        session_fee = 0.0
    else:
        col_energy, col_time = st.columns(2)
        with col_energy:
            if ios_safe_mode:
                energy_price = st.number_input(
                    f"{label} - Energy Price ({currency}/kWh)",
                    0.0, 2.0, float(preset["energy"]), 0.01,
                    key=f"{key_prefix}_energy",
                )
            else:
                energy_price = st.slider(
                    f"{label} - Energy Price ({currency}/kWh)",
                    0.0, 2.0, float(preset["energy"]), 0.01,
                    key=f"{key_prefix}_energy",
                )
        with col_time:
            use_per_min = st.checkbox(
                "Time-based Charging",
                value=bool(preset["time"] > 0),
                key=f"{key_prefix}_use_per_min",
            )
            if use_per_min:
                if ios_safe_mode:
                    time_price = st.number_input(
                        f"Time Price ({currency}/min)",
                        0.0, 1.0, float(max(preset["time"], 0.01)), 0.01,
                        key=f"{key_prefix}_time",
                    )
                else:
                    time_price = st.slider(
                        f"Time Price ({currency}/min)",
                        0.0, 1.0, float(max(preset["time"], 0.01)), 0.01,
                        key=f"{key_prefix}_time",
                    )
            else:
                time_price = 0.0
        if ios_safe_mode:
            session_fee = st.number_input(
                f"{label} - Connection Fee ({currency})",
                0.0, 10.0, 0.0, 0.25,
                key=f"{key_prefix}_session",
            )
        else:
            session_fee = st.slider(
                f"{label} - Connection Fee ({currency})",
                0.0, 10.0, 0.0, 0.05,
                key=f"{key_prefix}_session",
            )

    effective_kw = min(float(station_kw), float(car_max_kw))
    if effective_kw < station_kw:
        st.info(
            f"ℹ️ Charging limited by vehicle: {effective_kw:.0f}kW "
            f"(station: {station_kw:.0f}kW, vehicle max: {car_max_kw:.0f}kW)"
        )
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

# ============================================================================
# NEARBY CHARGERS (MAP-FIRST, CLICKABLE)
# ============================================================================

def render_location_and_cards_section(
    battery_kwh: float,
    start_pct: float,
    end_pct: float,
    efficiency_loss: float,
    miles_per_kwh: float,
    apply_taper: bool,
    car_max_kw: float,
    comparison_currency: str,
    exchange_rates: Dict,
    available_cards: List[str],
):
    st.markdown("## 🗺️ Nearby chargers & cheapest payment card")

    card_set = set(available_cards or [])

    col_loc1, col_loc2 = st.columns([2, 1])
    with col_loc1:
        postcode = st.text_input(
            "Enter your UK postcode (or click the map to set location)",
            placeholder="e.g., SW1A 1AA",
        )
    with col_loc2:
        use_map_click = st.checkbox("Use map click as location", value=False)

    lat = lon = None

    if use_map_click and "nearby_click_coords" in st.session_state:
        lat, lon = st.session_state["nearby_click_coords"]

    if lat is None and postcode:
        coords = geocode_postcode(postcode.strip())
        if not coords:
            st.error("❌ Could not find that postcode. Please check your input.")
            return
        lat, lon = coords

    if lat is None or lon is None:
        base_map = folium.Map(location=[54.0, -2.0], zoom_start=6)
        base_state = st_folium(base_map, width=800, height=500, key="nearby_base_map")
        click = base_state.get("last_clicked")
        if click:
            st.session_state["nearby_click_coords"] = (click["lat"], click["lng"])
            st.experimental_rerun()
        st.info("Click anywhere on the map to set your location, or enter a postcode above.")
        return

    st.success(f"📍 Location set at: {lat:.5f}, {lon:.5f}")

    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker([lat, lon], tooltip="Your location", icon=folium.Icon(color="blue")).add_to(m)

    pois = fetch_nearby_chargers(lat, lon, distance_km=10, max_results=25)
    if not pois:
        st.warning("No chargers returned from OpenChargeMap or API key missing.")
        map_state = st_folium(m, width=800, height=500, key="nearby_chargers_map")
        return

    if end_pct <= start_pct:
        st.info("Increase your target SoC above your current SoC to estimate costs.")
        energy_needed = 0.0
        miles_added = 0.0
    else:
        energy_needed = battery_kwh * ((end_pct - start_pct) / 100.0)
        energy_needed *= (1.0 + efficiency_loss / 100.0)
        miles_added = energy_needed * miles_per_kwh if energy_needed > 0 else 0.0

    rows = []

    for poi in pois:
        addr = poi.get("AddressInfo", {}) or {}
        op_info = poi.get("OperatorInfo") or {}
        operator_title = op_info.get("Title")
        site_title = addr.get("Title")
        operator = operator_title or "Unknown"

        title = site_title or operator or "Unknown charger"
        dist_km = addr.get("Distance")
        dist_str = f"{dist_km:.1f} km" if isinstance(dist_km, (int, float)) else "—"
        lat_c = addr.get("Latitude")
        lon_c = addr.get("Longitude")

        connections = poi.get("Connections") or []
        power_kw = connections[0].get("PowerKW") if connections else None
        if not isinstance(power_kw, (int, float)):
            power_kw = 50.0
        effective_kw = min(float(power_kw), float(car_max_kw))

        popup_text = f"{title}<br>{operator}<br>~{dist_str}"
        folium.Marker(
            [lat_c, lon_c],
            tooltip=title,
            popup=popup_text,
            icon=folium.Icon(color="green")
        ).add_to(m)

        tariff_name = infer_tariff_from_operator(f"{operator_title or ''} {site_title or ''}")
        best_card = None
        best_cost = None

        if tariff_name and tariff_name in card_set and energy_needed > 0:
            preset = CHARGING_PROVIDERS.get(tariff_name)
            if preset:
                time_min = calculate_charging_time(
                    battery_kwh, effective_kw, start_pct, end_pct, apply_taper
                )
                native_cost = calculate_charging_cost(
                    energy_needed,
                    time_min,
                    preset["energy"],
                    preset["time"],
                    0.0,
                )
                total_cost = convert_currency(
                    native_cost,
                    preset["currency"],
                    comparison_currency,
                    exchange_rates,
                )
                best_card = tariff_name
                best_cost = total_cost

        rows.append({
            "Charger": title,
            "Operator": operator,
            "Distance": dist_str,
            "Approx. Power (kW)": f"{effective_kw:.0f}",
            "Cheapest Card (you own)": best_card or "N/A",
            f"Est. Session Cost ({comparison_currency})": best_cost,
        })

    map_state = st_folium(m, width=800, height=500, key="nearby_chargers_map")

    st.markdown("### Nearby chargers & cheapest card (your cards only)")
    df = pd.DataFrame(rows)
    cost_col = f"Est. Session Cost ({comparison_currency})"
    if cost_col in df.columns:
        def fmt_cost(x):
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return "—"
            return format_currency(float(x), comparison_currency)
        df[cost_col] = df[cost_col].apply(fmt_cost)
    st.dataframe(df, use_container_width=True, hide_index=True)

    clicked_popup = map_state.get("last_object_clicked_popup")
    if clicked_popup:
        charger_name = clicked_popup.split("<br>")[0]
        selected = next((row for row in rows if row["Charger"] == charger_name), None)
        if selected:
            st.markdown("#### Selected charger details")
            st.write(selected)

    if energy_needed > 0:
        st.markdown("#### Overall cheapest cards for this session (your cards only)")
        card_rows = []
        for name, preset in CHARGING_PROVIDERS.items():
            if name not in card_set:
                continue
            station_kw = min(preset.get("default_kw", 50), car_max_kw)
            time_min = calculate_charging_time(
                battery_kwh, station_kw, start_pct, end_pct, apply_taper
            )
            native_cost = calculate_charging_cost(
                energy_needed,
                time_min,
                preset["energy"],
                preset["time"],
                0.0,
            )
            total_cost = convert_currency(
                native_cost, preset["currency"], comparison_currency, exchange_rates
            )
            cost_per_100 = (total_cost / miles_added * 100.0) if miles_added > 0 else 0.0
            card_rows.append({
                "Card / Provider": name,
                "Network Type": preset.get("network", "N/A"),
                f"Total Cost ({comparison_currency})": total_cost,
                f"Cost / 100 mi ({comparison_currency})": cost_per_100,
            })

        if card_rows:
            card_df = pd.DataFrame(card_rows).sort_values(
                by=f"Total Cost ({comparison_currency})"
            )
            for col in [
                f"Total Cost ({comparison_currency})",
                f"Cost / 100 mi ({comparison_currency})",
            ]:
                card_df[col] = card_df[col].apply(lambda x: format_currency(x, comparison_currency))
            st.dataframe(card_df, use_container_width=True, hide_index=True)
            cheapest = min(card_rows, key=lambda r: r[f"Total Cost ({comparison_currency})"])
            st.success(
                f"Overall best card for this session: **{cheapest['Card / Provider']}** "
                f"≈ {format_currency(cheapest[f'Total Cost ({comparison_currency})'], comparison_currency)}."
            )

# ============================================================================
# ROUTE PLANNER
# ============================================================================

def geocode_place_ors(query: str, headers: Dict[str, str]) -> Tuple[float, float]:
    url = "https://api.openrouteservice.org/geocode/search"
    params = {"text": query, "size": 1, "boundary.country": "GB"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features") or []
    if not feats:
        raise ValueError(f"No geocode result for '{query}'")
    coords = feats[0]["geometry"]["coordinates"]
    return coords[0], coords[1]


def render_route_planner(
    battery_kwh: float,
    miles_per_kwh: float,
    provider_a: Dict,
    comparison_currency: str,
    exchange_rates: Dict,
    available_cards: List[str],
):
    st.markdown("## 🗺 EV route planner")

    if "route_planned" not in st.session_state:
        st.session_state["route_planned"] = False

    col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
    with col_r1:
        start_location = st.text_input("Start Location", "Eastbourne, UK")
    with col_r2:
        end_location = st.text_input("Destination", "Manchester, UK")
    with col_r3:
        plan_clicked = st.button("Plan Route", use_container_width=True)

    if plan_clicked:
        st.session_state["route_planned"] = True
    if not st.session_state["route_planned"]:
        return

    ORS_API_KEY = st.secrets.get("ORS_API_KEY")
    if not ORS_API_KEY:
        st.error("Missing OpenRouteService API key. Add ORS_API_KEY to Streamlit secrets.")
        return

    headers = {"Authorization": ORS_API_KEY}
    card_set = set(available_cards or [])

    try:
        start_lon, start_lat = geocode_place_ors(start_location, headers)
        end_lon, end_lat = geocode_place_ors(end_location, headers)

        url_dir = "https://api.openrouteservice.org/v2/directions/driving-car"
        body = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}
        r_dir = requests.post(url_dir, headers=headers, json=body, timeout=20)
        r_dir.raise_for_status()
        route = r_dir.json()

        if "routes" not in route or not route["routes"]:
            st.error("Route service returned an unexpected response.")
            st.caption(f"Raw response: {json.dumps(route, indent=2)[:600]}")
            return

        route0 = route["routes"][0]
        summary = route0["summary"]
        distance_km = summary["distance"] / 1000
        duration_min = summary["duration"] / 60
        distance_miles = distance_km * 0.621371

        usable_battery = battery_kwh * 0.70
        max_range = usable_battery * miles_per_kwh
        required_stops = max(0, int(distance_miles // max_range))

        total_energy_needed = distance_miles / miles_per_kwh
        energy_price = provider_a["energy_price"]
        est_cost_native = total_energy_needed * energy_price
        est_cost = convert_currency(
            est_cost_native,
            provider_a["currency"],
            comparison_currency,
            exchange_rates
        )

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Distance", f"{distance_miles:.1f} mi")
        col_m2.metric("Drive Time", format_time(duration_min))
        col_m3.metric("Charging Stops Needed", required_stops)
        col_m4.metric("Estimated Charging Cost",
                      format_currency(est_cost, comparison_currency))

        stop_fractions: List[float] = []
        if required_stops == 1:
            stop_fractions = [0.5]
        elif required_stops >= 2:
            step = 1.0 / (required_stops + 1)
            stop_fractions = [step * (i + 1) for i in range(required_stops)]

        geom = route0.get("geometry")
        coords: List[Tuple[float, float]] = []
        if isinstance(geom, dict) and geom.get("coordinates"):
            coords = geom["coordinates"]
        elif isinstance(geom, str):
            decoded = convert.decode_polyline(geom)
            coords = decoded["coordinates"]

        stop_suggestions: List[Dict] = []
        if coords and stop_fractions:
            n = len(coords) - 1
            for frac in stop_fractions:
                idx = int(round(frac * n))
                idx = max(0, min(n, idx))
                lon_s, lat_s = coords[idx]
                best = pick_best_charger_stop(
                    lon_s,
                    lat_s,
                    battery_kwh=battery_kwh,
                    miles_per_kwh=miles_per_kwh,
                    start_soc=10.0,
                    end_soc=80.0,
                    efficiency_loss=Config.DEFAULT_EFFICIENCY_LOSS,
                    apply_taper=True,
                    car_max_kw=provider_a["station_kw"],
                    comparison_currency=comparison_currency,
                    exchange_rates=exchange_rates,
                    available_cards=card_set,
                )
                if best:
                    stop_suggestions.append(best)

        if stop_suggestions:
            st.markdown("### Suggested charging stops (cheapest with your cards)")
            df_stops = pd.DataFrame([
                {
                    "Stop #": i + 1,
                    "Charger": s["charger_name"],
                    "Operator": s["operator"],
                    "Power (kW)": f"{s['power_kw']:.0f}",
                    "Best Card": s["card"],
                    f"Est. Cost ({comparison_currency})": format_currency(s["total_cost"], comparison_currency),
                    "Charging Time": format_time(s["time_min"]),
                }
                for i, s in enumerate(stop_suggestions)
            ])
            st.dataframe(df_stops, use_container_width=True, hide_index=True)

        m = folium.Map(location=[start_lat, start_lon], zoom_start=6)

        try:
            route_geom = None
            if isinstance(geom, dict):
                route_geom = geom
            elif isinstance(geom, str):
                decoded = convert.decode_polyline(geom)
                route_geom = {
                    "type": "LineString",
                    "coordinates": decoded["coordinates"],
                }
            if route_geom is not None:
                route_feature = {"type": "Feature", "geometry": route_geom, "properties": {}}
                folium.GeoJson(route_feature).add_to(m)
        except Exception:
            st.caption("Failed to decode route geometry; showing markers only.")

        folium.Marker(
            [start_lat, start_lon],
            tooltip="Start",
            icon=folium.Icon(color="green")
        ).add_to(m)
        folium.Marker(
            [end_lat, end_lon],
            tooltip="Destination",
            icon=folium.Icon(color="red")
        ).add_to(m)

        for i, s in enumerate(stop_suggestions):
            folium.Marker(
                [s["lat"], s["lon"]],
                tooltip=f"Stop {i+1}: {s['charger_name']}",
                popup=f"Stop {i+1}: {s['charger_name']}<br>"
                      f"{s['operator']}<br>"
                      f"Best card: {s['card']}<br>"
                      f"Est. cost: {format_currency(s['total_cost'], comparison_currency)}",
                icon=folium.Icon(color="orange"),
            ).add_to(m)

        map_state = st_folium(m, width=1200, height=600, key="route_planner_map")

        clicked_popup = map_state.get("last_object_clicked_popup")
        if clicked_popup and stop_suggestions:
            first_line = clicked_popup.split("<br>")[0]
            try:
                label = first_line.split(":")[0].strip()   # "Stop X"
                idx = int(label.split()[1]) - 1
                if 0 <= idx < len(stop_suggestions):
                    sel = stop_suggestions[idx]
                    st.markdown("#### Selected stop details")
                    st.write({
                        "Stop #": idx + 1,
                        "Charger": sel["charger_name"],
                        "Operator": sel["operator"],
                        "Power (kW)": f"{sel['power_kw']:.0f}",
                        "Best Card": sel["card"],
                        f"Est. Cost ({comparison_currency})": format_currency(sel["total_cost"], comparison_currency),
                        "Charging Time": format_time(sel["time_min"]),
                    })
            except Exception:
                pass

    except requests.HTTPError as e:
        body = ""
        try:
            body = e.response.text
        except Exception:
            pass
        if e.response is not None and e.response.status_code == 400 and "2004" in body:
            st.error(
                "Route is too long for this OpenRouteService plan (> 6,000 km), "
                "or one of the locations was geocoded outside the UK."
            )
            st.caption("Try more precise UK names, e.g. 'Eastbourne, UK' and 'Manchester, UK'.")
        else:
            st.error("Route calculation failed (HTTP error).")
            st.caption(f"Status: {e.response.status_code if e.response else 'unknown'}, "
                       f"Body: {body[:300]}")
    except Exception as e:
        st.error("Route calculation failed. Check locations or API key.")
        st.caption(str(e))

# ============================================================================
# PROVIDER COMPARISON
# ============================================================================

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
    energy_needed = battery_kwh * ((end_pct - start_pct) / 100.0)
    energy_needed *= (1.0 + efficiency_loss / 100.0)
    time_a = calculate_charging_time(
        battery_kwh, provider_a["effective_kw"], start_pct, end_pct, apply_taper
    )
    time_b = calculate_charging_time(
        battery_kwh, provider_b["effective_kw"], start_pct, end_pct, apply_taper
    )
    native_cost_a = calculate_charging_cost(
        energy_needed, time_a,
        provider_a["energy_price"], provider_a["time_price"], provider_a["session_fee"]
    )
    native_cost_b = calculate_charging_cost(
        energy_needed, time_b,
        provider_b["energy_price"], provider_b["time_price"], provider_b["session_fee"]
    )
    total_cost_a = convert_currency(
        native_cost_a, provider_a["currency"], comparison_currency, rates
    )
    total_cost_b = convert_currency(
        native_cost_b, provider_b["currency"], comparison_currency, rates
    )
    miles_added = energy_needed * miles_per_kwh
    cost_per_100mi_a = (total_cost_a / miles_added * 100.0) if miles_added > 0 else 0.0
    cost_per_100mi_b = (total_cost_b / miles_added * 100.0) if miles_added > 0 else 0.0
    savings = abs(total_cost_a - total_cost_b)
    if total_cost_a < total_cost_b:
        winner = provider_a["provider"]
        loser_cost = total_cost_b
    else:
        winner = provider_b["provider"]
        loser_cost = total_cost_a
    savings_pct = (savings / loser_cost * 100) if loser_cost > 0 else 0

    st.markdown("### 📊 Comparison results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Energy delivered", f"{energy_needed:.2f} kWh")
    with col2:
        st.metric("Range added", f"{miles_added:.1f} mi")
    with col3:
        st.metric(provider_a["provider"][:15], format_time(time_a))
    with col4:
        st.metric(provider_b["provider"][:15], format_time(time_b))

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric(
            f"💰 {provider_a['provider']}",
            format_currency(total_cost_a, comparison_currency),
        )
        st.caption(f"Per 100 miles: {format_currency(cost_per_100mi_a, comparison_currency)}")
    with col6:
        st.metric(
            f"💰 {provider_b['provider']}",
            format_currency(total_cost_b, comparison_currency),
        )
        st.caption(f"Per 100 miles: {format_currency(cost_per_100mi_b, comparison_currency)}")
    with col7:
        st.metric(
            "💵 Potential savings",
            format_currency(savings, comparison_currency),
            delta=f"{savings_pct:.1f}%",
        )
        st.markdown(f'<span class="success-badge">Choose {winner}</span>', unsafe_allow_html=True)

# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title=Config.APP_TITLE,
        page_icon=Config.APP_ICON,
        layout=Config.PAGE_LAYOUT,
        initial_sidebar_state="collapsed"
    )

    apply_custom_styles()
    exchange_rates = fetch_exchange_rates()
    render_hero_section()

    ios_safe_mode = st.toggle(
        "📱 iOS-friendly inputs",
        value=True,
        help="Use number inputs instead of sliders to prevent accidental changes while scrolling"
    )
    rate_status = exchange_rates.get("_status", "Unknown")
    rate_date = exchange_rates.get("_date", "Unknown")
    st.caption(f"💱 Exchange rates: {rate_status} • Updated: {rate_date}")
    st.markdown("---")

    battery_kwh, car_max_kw = render_vehicle_selector(ios_safe_mode)
    st.markdown("---")
    start_pct, end_pct, efficiency_loss, apply_taper, miles_per_kwh = render_charging_session_config(ios_safe_mode)

    comparison_currency = st.selectbox(
        "💵 Display results in",
        ["GBP", "EUR", "USD"],
        index=0,
    )

    all_cards = list(CHARGING_PROVIDERS.keys())
    default_cards = [name for name, p in CHARGING_PROVIDERS.items() if p["type"] != "home"]
    user_cards = st.multiselect(
        "💳 Payment options you have",
        options=all_cards,
        default=default_cards,
        help="We’ll only recommend chargers compatible with these cards."
    )

    st.markdown("---")
    nearby_tab, route_tab, compare_tab = st.tabs(
        ["Nearby chargers", "Route planner", "Provider comparison"]
    )

    with nearby_tab:
        render_location_and_cards_section(
            battery_kwh=battery_kwh,
            start_pct=start_pct,
            end_pct=end_pct,
            efficiency_loss=efficiency_loss,
            miles_per_kwh=miles_per_kwh,
            apply_taper=apply_taper,
            car_max_kw=car_max_kw,
            comparison_currency=comparison_currency,
            exchange_rates=exchange_rates,
            available_cards=user_cards,
        )

    with route_tab:
        # fallback provider if compare tab hasn’t been used yet
        fallback_provider = {
            "provider": list(CHARGING_PROVIDERS.keys())[0],
            "currency": CHARGING_PROVIDERS[list(CHARGING_PROVIDERS.keys())[0]]["currency"],
            "station_kw": CHARGING_PROVIDERS[list(CHARGING_PROVIDERS.keys())[0]]["default_kw"],
            "effective_kw": CHARGING_PROVIDERS[list(CHARGING_PROVIDERS.keys())[0]]["default_kw"],
            "energy_price": CHARGING_PROVIDERS[list(CHARGING_PROVIDERS.keys())[0]]["energy"],
            "time_price": CHARGING_PROVIDERS[list(CHARGING_PROVIDERS.keys())[0]]["time"],
            "session_fee": 0.0,
        }
        provider_for_route = st.session_state.get("provider_a_for_route", fallback_provider)
        render_route_planner(
            battery_kwh=battery_kwh,
            miles_per_kwh=miles_per_kwh,
            provider_a=provider_for_route,
            comparison_currency=comparison_currency,
            exchange_rates=exchange_rates,
            available_cards=user_cards,
        )

    with compare_tab:
        st.markdown("## 🔌 Charging provider comparison")
        col_a, col_b = st.columns(2)
        with col_a:
            provider_a = render_provider_configuration("Provider A", "provider_a", car_max_kw, ios_safe_mode)
        with col_b:
            provider_b = render_provider_configuration("Provider B", "provider_b", car_max_kw, ios_safe_mode)

        if st.button("🔍 Compare providers", type="primary", use_container_width=True, key="compare_button"):
            if end_pct <= start_pct:
                st.error("❌ Target charge level must be greater than current charge level")
            else:
                render_results(
                    battery_kwh, start_pct, end_pct, efficiency_loss, miles_per_kwh,
                    apply_taper, provider_a, provider_b, comparison_currency, exchange_rates
                )
            # store provider_a to reuse in route planner as default tariff
            st.session_state["provider_a_for_route"] = provider_a

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #a0aec0; padding: 2rem 0;'>
            <p><strong>EV Charge Pro UK</strong> • Professional Edition</p>
            <p style='font-size: 0.875rem;'>
                Tariffs vary by location and time. Always verify pricing before charging.<br>
                Exchange rates provided by Frankfurter (ECB data) • Updated live
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
