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
    # Add more providers here
}

# ---------------------------------------------------
# USER INPUT
# ---------------------------------------------------
st.sidebar.header("Battery & Charge Info")
battery_size = st.sidebar.number_input("Battery size (kWh)", value=81.1, step=1.0)
start_soc = st.sidebar.slider("Current charge (%)", 0, 100, 80)
target_soc = st.sidebar.slider("Target charge (%)", start_soc + 1, 100, 100)
efficiency = st.sidebar.slider("Charging efficiency (%)", 80, 100, 90) / 100

st.sidebar.header("Select providers to compare")
selected_providers = st.sidebar.multiselect("Providers", list(providers.keys()), default=list(providers.keys()))

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
# PROVIDER INPUTS & CALCULATION
# ---------------------------------------------------
all_results = []

for provider in selected_providers:
    st.header(f"⚡ {provider}")
    # Slider per provider for charger power
    allowed_powers = sorted([int(p) for p in providers[provider].keys()])
    charger_power = st.slider(
        f"Select charger power (kW) for {provider}",
        min_value=min(allowed_powers),
        max_value=max(allowed_powers),
        value=min(allowed_powers),
        step=1,
        key=f"{provider}_slider"
    )
    # Calculate time and cost
    time_min, total_cost = calculate_cost_time(charger_power, energy_needed, start_soc, target_soc, provider)
    st.write(f"Energy to add: {energy_needed:.1f} kWh")
    st.write(f"Estimated charging time: {time_min:.1f} minutes")
    st.write(f"Estimated cost: {total_cost:.2f} (currency)")

    all_results.append({
        "Provider": provider,
        "Charger kW": charger_power,
        "Time (min)": time_min,
        "Cost": total_cost
    })

# ---------------------------------------------------
# SUMMARY COMPARISON
# ---------------------------------------------------
if all_results:
    df_comp = pd.DataFrame(all_results)
    st.write("### Comparison Across Providers")
    st.dataframe(df_comp)

    st.write("### Cost vs Provider & Charger")
    st.bar_chart(df_comp.set_index("Provider")["Cost"])

    best = df_comp.loc[df_comp["Cost"].idxmin()]
    st.success(f"💡 Cheapest option: {best['Provider']} at {best['Charger kW']} kW → Cost: {best['Cost']:.2f}, Time: {best['Time (min)']:.1f} minutes")
