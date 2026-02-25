"""
EV Charge Pro UK – Route Planner Edition
Premium Map-Based EV Charging Cost & Route Planner
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import openrouteservice
from typing import Dict

# ============================
# CONFIG
# ============================

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjlhMDcwZmMwYWIwZTQxOWViN2M3MDgwNzM2NjMzYjI5IiwiaCI6Im11cm11cjY0In0="

st.set_page_config(
    page_title="EV Charge Pro UK",
    page_icon="⚡",
    layout="wide"
)

# ============================
# STYLING (IONITY-INSPIRED)
# ============================

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #0b0f1a;
    color: white;
}
.block-container {
    padding: 1rem 2rem 2rem 2rem;
    max-width: 100%;
}
h1, h2, h3 {
    font-weight: 700;
}
.stButton > button {
    background: linear-gradient(90deg, #00ADF0, #2182FF);
    color: white;
    border-radius: 12px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ============================
# DATA
# ============================

VEHICLES = {
    "Tesla Model Y Long Range": {"battery": 75, "max_kw": 250},
    "Tesla Model 3 Long Range": {"battery": 75, "max_kw": 250},
    "Audi Q6 e-tron": {"battery": 94.9, "max_kw": 270},
    "Kia EV6 Long Range": {"battery": 84, "max_kw": 235},
    "Hyundai IONIQ 5 Long Range": {"battery": 84, "max_kw": 235},
    "VW ID.4 Pro": {"battery": 77, "max_kw": 175},
}

PROVIDERS = {
    "IONITY (Example 0.79/kWh)": 0.79,
    "Osprey (0.82/kWh)": 0.82,
    "BP Pulse (0.87/kWh)": 0.87,
    "Home Octopus Intelligent (0.08/kWh)": 0.08,
}

# ============================
# EXCHANGE RATES
# ============================

@st.cache_data(ttl=1800)
def fetch_rates():
    fallback = {"EUR": 1.0, "GBP": 0.87}
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest?from=EUR&to=GBP",
            timeout=5
        ).json()
        return {"EUR": 1.0, "GBP": r["rates"]["GBP"]}
    except:
        return fallback

def convert(amount, from_cur, to_cur, rates):
    if from_cur == to_cur:
        return amount
    eur = amount / rates[from_cur]
    return eur * rates[to_cur]

# ============================
# ROUTING
# ============================

def generate_route(start, end):
    geolocator = Nominatim(user_agent="ev_charge_pro")
    start_geo = geolocator.geocode(start)
    end_geo = geolocator.geocode(end)

    if not start_geo or not end_geo:
        return None, None, None

    client = openrouteservice.Client(key=ORS_API_KEY)

    coords = [
        (start_geo.longitude, start_geo.latitude),
        (end_geo.longitude, end_geo.latitude)
    ]

    route = client.directions(coords, profile="driving-car", format="geojson")

    distance_km = route["features"][0]["properties"]["summary"]["distance"] / 1000

    return route, (start_geo.latitude, start_geo.longitude), distance_km

# ============================
# UI
# ============================

st.title("⚡ EV Charge Pro UK")
st.caption("Premium EV Route & Charging Cost Planner")

# Route Inputs
col1, col2, col3 = st.columns([2,2,1])

with col1:
    start_location = st.text_input("Start Location", "Eastbourne, UK")

with col2:
    end_location = st.text_input("Destination", "London, UK")

with col3:
    vehicle_name = st.selectbox("Vehicle", list(VEHICLES.keys()))

vehicle = VEHICLES[vehicle_name]

provider = st.selectbox("Charging Provider", list(PROVIDERS.keys()))
price_per_kwh = PROVIDERS[provider]

comparison_currency = st.selectbox("Display Currency", ["GBP", "EUR"])

# ============================
# GENERATE ROUTE
# ============================

if st.button("🔍 Plan Route & Estimate Charging"):

    if ORS_API_KEY == "PASTE_YOUR_KEY_HERE":
        st.error("Please add your OpenRouteService API key.")
        st.stop()

    with st.spinner("Generating route..."):
        route, start_coords, distance_km = generate_route(start_location, end_location)

    if route is None:
        st.error("Could not generate route.")
        st.stop()

    # ============================
    # MAP
    # ============================

    m = folium.Map(
        location=start_coords,
        zoom_start=8,
        tiles="CartoDB dark_matter"
    )

    folium.GeoJson(route, name="Route").add_to(m)

    st_folium(m, use_container_width=True, height=600)

    # ============================
    # TRIP CALCULATIONS
    # ============================

    efficiency = 3.5  # miles per kWh default
    distance_miles = distance_km * 0.621371

    energy_needed = distance_miles / efficiency
    charging_cost = energy_needed * price_per_kwh

    rates = fetch_rates()
    charging_cost = convert(charging_cost, "GBP", comparison_currency, rates)

    # Estimated charging stops
    usable_range = vehicle["battery"] * efficiency
    stops = max(0, int(distance_miles // usable_range))

    # ============================
    # RESULTS
    # ============================

    st.markdown("## 📊 Trip Summary")

    colA, colB, colC, colD = st.columns(4)

    colA.metric("Distance", f"{distance_miles:.1f} miles")
    colB.metric("Energy Required", f"{energy_needed:.1f} kWh")
    colC.metric("Estimated Stops", stops)
    colD.metric("Estimated Charging Cost", f"{comparison_currency} {charging_cost:.2f}")

    st.markdown("### 💡 Charging Insight")

    if stops == 0:
        st.success("Trip achievable on one charge.")
    else:
        st.info(f"Approx. {stops} rapid charging stop(s) required.")

    st.markdown("""
    ---
    ⚠️ Estimates assume constant efficiency and full rapid charging availability.
    Real-world range varies with speed, temperature, and elevation.
    """)
