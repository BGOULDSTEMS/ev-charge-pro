import streamlit as st
import pandas as pd
import requests

st.title("🔋 EV Charging Cost & Time Calculator")

# ---------------------------------------------------
# LIVE FX RATES WITH FALLBACK
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
    eur_value = amount / rates[from_curr] if from_curr != "EUR" else amount
    return eur_value * rates[to_curr]

# ---------------------------------------------------
# PROVIDERS & CHARGER DATA
# ---------------------------------------------------
providers = {
    "Freshmile": {
        "75": {"cost_kwh": 0.30, "cost_min": 0.30},
        "200": {"cost_kwh": 0.30, "cost_min": 0.30},
    },
    "Electroverse": {
        "75": {"cost_kwh": 0.80, "cost_min": 0.0},
    },
}

# ---------------------------------------------------
# USER INPUT
# ---------------------------------------------------
provider = st.selectbox("Select your charging card/provider", list(providers.keys()))

battery_size = st.number_input("Battery size (kWh)", value=81.1, step=1.0)
start_soc = st.slider("Current charge (%)", 0, 100, 80)
target_soc = st.slider("Target charge (%)", start_soc + 1, 100, 100)
efficiency = st.slider("Charging efficiency (%)", 80, 100, 90)/100

comparison_currency = st.selectbox("Currency for cost display", ["EUR", "GBP", "USD"])

# Allowed charger powers for this provider
allowed_powers = sorted([int(p) for p in providers[provider].keys()])

charger_power = st.slider(
    "Select charger power (kW) for this provider",
    min_value=min(allowed_powers),
    max_value=max(allowed_powers),
    value=min(allowed_powers),
    step=1
)

# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------
def taper_factor(soc):
    """Return fraction of charger power based on SOC"""
    if soc < 60:
        return 1.0
    elif soc < 80:
        return 0.7
    else:
        return 0.4

def calculate_cost_time(charger_kw, energy_needed, start_soc, target_soc, provider):
    avg_soc = (start_soc + target_soc) / 2
    effective_power = charger_kw * taper_factor(avg_soc)
    charging_time_hours = energy_needed / effective_power
    charging_time_minutes = charging_time_hours * 60

    energy_from_grid = energy_needed / efficiency
    cost_kwh = providers[provider][str(charger_kw)]["cost_kwh"]
    cost_min = providers[provider][str(charger_kw)]["cost_min"]
    total_cost = energy_from_grid * cost_kwh + charging_time_minutes * cost_min
    return charging_time_minutes, total_cost

# ---------------------------------------------------
# ENERGY REQUIRED
# ---------------------------------------------------
energy_needed = battery_size * (target_soc - start_soc) / 100

# ---------------------------------------------------
# CALCULATE SELECTED CHARGER
# ---------------------------------------------------
time_selected, cost_selected = calculate_cost_time(charger_power, energy_needed, start_soc, target_soc, provider)
cost_selected_conv = convert(cost_selected, "EUR", comparison_currency)

st.write(f"### Charging Summary for {provider} at {charger_power} kW")
st.write(f"Energy to add: {energy_needed:.1f} kWh")
st.write(f"Estimated charging time: {time_selected:.1f} minutes")
st.write(f"Estimated cost: {cost_selected_conv:.2f} {comparison_currency}")

# ---------------------------------------------------
# COMPARE ALL ALLOWED CHARGERS FOR THIS PROVIDER
# ---------------------------------------------------
comparison = []
for kw in allowed_powers:
    t, c = calculate_cost_time(kw, energy_needed, start_soc, target_soc, provider)
    c_conv = convert(c, "EUR", comparison_currency)
    comparison.append({"Charger kW": kw, "Time (min)": t, f"Cost ({comparison_currency})": c_conv})

df_comp = pd.DataFrame(comparison)

st.write("### Comparison of all allowed chargers")
st.dataframe(df_comp)

# ---------------------------------------------------
# BAR CHART OF COST VS CHARGER POWER
# ---------------------------------------------------
st.write(f"### Cost vs Charger Power ({comparison_currency})")
st.bar_chart(df_comp.set_index("Charger kW")[f"Cost ({comparison_currency})"])

# ---------------------------------------------------
# CHEAPEST OPTION
# ---------------------------------------------------
best = df_comp.loc[df_comp[f"Cost ({comparison_currency})"].idxmin()]
st.success(f"💡 Cheapest option: {best['Charger kW']} kW → Cost: {best[f'Cost ({comparison_currency})']:.2f} {comparison_currency}, Time: {best['Time (min)']:.1f} minutes")
