import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="EV Charge Pro", page_icon="⚡", layout="centered")

st.title("⚡ EV Charge Pro")

# ---------------------------------------------------
# VEHICLE DATABASE
# ---------------------------------------------------

VEHICLES = {
    "Kia EV3 Long Range": 81.1,
    "Tesla Model 3 Long Range": 75,
    "Hyundai Kona Electric 65kWh": 65,
    "VW ID.4 Pro": 77,
    "Nissan Ariya 87kWh": 87,
    "Custom": None
}

# ---------------------------------------------------
# PROVIDER PRESETS
# ---------------------------------------------------

DEFAULT_PROVIDERS = {
    "Ionity": {"energy": 0.69, "time": 0.00, "currency": "EUR"},
    "Tesla Supercharger UK": {"energy": 0.44, "time": 0.00, "currency": "GBP"},
    "Shell Recharge UK": {"energy": 0.79, "time": 0.00, "currency": "GBP"},
    "Freshmile": {"energy": 0.30, "time": 0.30, "currency": "EUR"},
    "Electroverse": {"energy": 0.80, "time": 0.00, "currency": "GBP"},
    "Custom": {"energy": 0.0, "time": 0.0, "currency": "GBP"}
}

if "providers" not in st.session_state:
    st.session_state.providers = DEFAULT_PROVIDERS.copy()

# ---------------------------------------------------
# LIVE FX RATES
# ---------------------------------------------------

@st.cache_data(ttl=3600)
def get_fx_rates():
    url = "https://api.exchangerate.host/latest?base=EUR"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if "rates" in data:
            return data["rates"]
        else:
            st.warning("Exchange rate API returned unexpected data. Using fallback rates.")
            return {"USD": 1.1, "GBP": 0.88, "EUR": 1.0}  # fallback
    except Exception as e:
        st.warning(f"Exchange rate API error: {e}. Using fallback rates.")
        return {"USD": 1.1, "GBP": 0.88, "EUR": 1.0}  # fallback

rates = get_fx_rates()

def convert(amount, from_curr, to_curr):
    """Convert amount from one currency to another using rates."""
    if from_curr == to_curr:
        return amount
    # Convert to EUR first if necessary
    eur_value = amount / rates[from_curr] if from_curr != "EUR" else amount
    return eur_value * rates[to_curr]
# ---------------------------------------------------
# CHARGING MODEL
# ---------------------------------------------------

def charging_time(battery, charger_kw, start_pct, end_pct, taper=True):
    time = 0
    current = start_pct
    while current < end_pct:
        if taper:
            if current < 80:
                rate = charger_kw
                next_stop = min(end_pct, 80)
            elif current < 90:
                rate = charger_kw * 0.5
                next_stop = min(end_pct, 90)
            else:
                rate = charger_kw * 0.3
                next_stop = end_pct
        else:
            rate = charger_kw
            next_stop = end_pct

        segment = (next_stop - current) / 100
        energy = battery * segment
        time += (energy / rate) * 60
        current = next_stop
    return time

# ---------------------------------------------------
# UI
# ---------------------------------------------------

st.header("🚗 Vehicle")

vehicle = st.selectbox("Select Vehicle", list(VEHICLES.keys()))

if vehicle == "Custom":
    battery_kwh = st.number_input("Battery size (kWh)", 10.0, 200.0, 80.0)
else:
    battery_kwh = VEHICLES[vehicle]
    st.info(f"Battery size: {battery_kwh} kWh")

start_pct = st.slider("Current Charge (%)", 0, 100, 50)
end_pct = st.slider("Target Charge (%)", 0, 100, 80)

st.header("⚡ Charger")

charger_kw = st.slider("Charger Power (kW)", 7, 400, 75)

st.header("🏷 Providers")

provider_names = list(st.session_state.providers.keys())
provA = st.selectbox("Provider A", provider_names, index=0)
provB = st.selectbox("Provider B", provider_names, index=1)

def provider_inputs(name):
    p = st.session_state.providers[name]
    energy = st.number_input(f"{name} energy ({p['currency']}/kWh)", value=p["energy"])
    time = st.number_input(f"{name} time ({p['currency']}/min)", value=p["time"])
    return energy, time, p["currency"]

energyA, timeA, currA = provider_inputs(provA)
energyB, timeB, currB = provider_inputs(provB)

comparison_currency = st.selectbox("Compare In Currency", ["GBP", "EUR", "USD"])

st.header("⚙ Advanced")

efficiency_loss = st.slider("Efficiency Loss (%)", 0, 15, 5)
miles_per_kwh = st.number_input("Miles per kWh", 1.0, 6.0, 3.5)
taper = st.toggle("Apply Charging Taper", True)

# ---------------------------------------------------
# CALCULATION
# ---------------------------------------------------

if st.button("Compare ⚡"):

    energy_needed = battery_kwh * ((end_pct - start_pct)/100)
    energy_needed *= (1 + efficiency_loss/100)

    time_minutes = charging_time(battery_kwh, charger_kw, start_pct, end_pct, taper)

    costA = (energy_needed * energyA) + (time_minutes * timeA)
    costB = (energy_needed * energyB) + (time_minutes * timeB)

    costA_conv = convert(costA, currA, comparison_currency)
    costB_conv = convert(costB, currB, comparison_currency)

    st.subheader("Results")

    st.write(f"Energy Added: {energy_needed:.2f} kWh")
    st.write(f"Time: {time_minutes:.1f} mins")
    st.write(f"Miles Added: {energy_needed * miles_per_kwh:.1f}")

    st.metric(provA, f"{costA_conv:.2f} {comparison_currency}")
    st.metric(provB, f"{costB_conv:.2f} {comparison_currency}")

    st.write(f"Cost per 100 miles ({provA}): {(costA_conv/(energy_needed*miles_per_kwh)*100):.2f}")
    st.write(f"Cost per 100 miles ({provB}): {(costB_conv/(energy_needed*miles_per_kwh)*100):.2f}")

    # Graph cost vs %
    pct_range = np.linspace(start_pct, 100, 20)
    cost_curve_A = []
    cost_curve_B = []

    for pct in pct_range:
        e = battery_kwh*((pct-start_pct)/100)
        t = charging_time(battery_kwh, charger_kw, start_pct, pct, taper)
        cA = convert((e*energyA)+(t*timeA), currA, comparison_currency)
        cB = convert((e*energyB)+(t*timeB), currB, comparison_currency)
        cost_curve_A.append(cA)
        cost_curve_B.append(cB)

    df = pd.DataFrame({
        "Charge %": pct_range,
        provA: cost_curve_A,
        provB: cost_curve_B
    })

    st.line_chart(df.set_index("Charge %"))
