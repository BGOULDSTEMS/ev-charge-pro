import streamlit as st
import pandas as pd

st.title("🔋 EV Charging Cost & Time Calculator")

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
    # Add more providers as needed
}

# ---------------------------------------------------
# USER INPUT
# ---------------------------------------------------
provider = st.selectbox("Select your charging card/provider", list(providers.keys()))

# Battery info
battery_size = st.number_input("Battery size (kWh)", value=81.1, step=1.0)
start_soc = st.slider("Current charge (%)", 0, 100, 80)
target_soc = st.slider("Target charge (%)", start_soc + 1, 100, 100)
efficiency = st.slider("Charging efficiency (%)", 80, 100, 90)/100

# Allowed charger powers for this provider
allowed_powers = sorted([int(p) for p in providers[provider].keys()])

# Charger power slider (for single selected charger)
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

st.write(f"### Charging Summary for {provider} at {charger_power} kW")
st.write(f"Energy to add: {energy_needed:.1f} kWh")
st.write(f"Estimated charging time: {time_selected:.1f} minutes")
st.write(f"Estimated cost: {cost_selected:.2f} (currency)")

# ---------------------------------------------------
# COMPARE ALL ALLOWED CHARGERS FOR THIS PROVIDER
# ---------------------------------------------------
comparison = []
for kw in allowed_powers:
    t, c = calculate_cost_time(kw, energy_needed, start_soc, target_soc, provider)
    comparison.append({"Charger kW": kw, "Time (min)": t, "Cost": c})

df_comp = pd.DataFrame(comparison)

st.write("### Comparison of all allowed chargers")
st.dataframe(df_comp)

# ---------------------------------------------------
# BAR CHART OF COST VS CHARGER POWER
# ---------------------------------------------------
st.write("### Cost vs Charger Power")
st.bar_chart(df_comp.set_index("Charger kW")["Cost"])

# ---------------------------------------------------
# CHEAPEST OPTION
# ---------------------------------------------------
best = df_comp.loc[df_comp["Cost"].idxmin()]
st.success(f"💡 Cheapest option: {best['Charger kW']} kW → Cost: {best['Cost']:.2f}, Time: {best['Time (min)']:.1f} minutes")
