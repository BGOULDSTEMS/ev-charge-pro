import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="EV Charge Pro UK", page_icon="⚡", layout="wide")

# ---------------------------------------------------
# UI STYLE
# ---------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #f4f7fb;
        --surface: #ffffff;
        --text: #0f172a;
        --muted: #5b6474;
        --line: #dbe1ea;
      }
      .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Avenir Next",
                     "Helvetica Neue", "Segoe UI", Roboto, Arial, sans-serif;
      }
      .block-container {
        max-width: 1180px;
        padding-top: 1rem;
        padding-bottom: 2rem;
      }
      .hero {
        background: linear-gradient(110deg, #0b3a66 0%, #155e75 100%);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: white;
        margin-bottom: 1rem;
      }
      .hero p { margin: .3rem 0 0; color: #e8eef7; }
      .panel {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .9rem 1rem .6rem;
        box-shadow: 0 6px 18px rgba(15,23,42,.05);
        margin-bottom: 1rem;
      }
      .small-note { color: var(--muted); font-size: .9rem; }
      .stButton > button { min-height: 46px; font-weight: 600; }
      @media (max-width: 900px) {
        .block-container { padding-left: .8rem; padding-right: .8rem; }
        div[data-testid="column"] { width:100%!important; flex:1 1 100%!important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# VEHICLES (TOP UK EVS + MAX DC kW)
# ---------------------------------------------------
DEFAULT_VEHICLES = pd.DataFrame(
    [
        {"model": "Tesla Model Y Long Range", "battery_kwh": 75.0, "max_dc_kw": 250},
        {"model": "Tesla Model 3 Long Range", "battery_kwh": 75.0, "max_dc_kw": 250},
        {"model": "Audi Q4 e-tron 77", "battery_kwh": 77.0, "max_dc_kw": 135},
        {"model": "Audi Q6 e-tron", "battery_kwh": 94.9, "max_dc_kw": 270},
        {"model": "Ford Explorer Extended Range", "battery_kwh": 79.0, "max_dc_kw": 185},
        {"model": "BMW i4 eDrive40", "battery_kwh": 81.3, "max_dc_kw": 205},
        {"model": "Skoda Enyaq 85", "battery_kwh": 82.0, "max_dc_kw": 175},
        {"model": "Kia EV3 Long Range", "battery_kwh": 81.4, "max_dc_kw": 135},
        {"model": "Skoda Elroq 85", "battery_kwh": 82.0, "max_dc_kw": 175},
        {"model": "Volvo EX30 Extended Range", "battery_kwh": 69.0, "max_dc_kw": 153},
        {"model": "MG4 Long Range", "battery_kwh": 77.0, "max_dc_kw": 144},
        {"model": "Hyundai Kona Electric 65", "battery_kwh": 65.4, "max_dc_kw": 102},
        {"model": "VW ID.4 Pro", "battery_kwh": 77.0, "max_dc_kw": 175},
        {"model": "Nissan Ariya 87", "battery_kwh": 87.0, "max_dc_kw": 130},
        {"model": "Kia EV6 Long Range", "battery_kwh": 84.0, "max_dc_kw": 235},
        {"model": "Hyundai IONIQ 5 Long Range", "battery_kwh": 84.0, "max_dc_kw": 235},
        {"model": "Mercedes EQA 350", "battery_kwh": 70.5, "max_dc_kw": 100},
        {"model": "Polestar 2 Long Range", "battery_kwh": 82.0, "max_dc_kw": 205},
        {"model": "BYD Dolphin Comfort", "battery_kwh": 60.4, "max_dc_kw": 88},
        {"model": "Vauxhall Corsa Electric", "battery_kwh": 51.0, "max_dc_kw": 100},
    ]
)

# ---------------------------------------------------
# PROVIDERS (public + home)
# category: Public or Home
# one row = one provider + charger speed
# ---------------------------------------------------
DEFAULT_PROVIDERS = pd.DataFrame(
    [
        # Public networks/cards
        {"provider": "MFG EV Power", "category": "Public", "charger_kw": 150, "energy_price": 0.79, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Edit to local tariff if needed."},
        {"provider": "EVYVE Charging Stations", "category": "Public", "charger_kw": 150, "energy_price": 0.80, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Edit to local tariff if needed."},
        {"provider": "Osprey Charging (App)", "category": "Public", "charger_kw": 150, "energy_price": 0.82, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Edit to local tariff if needed."},
        {"provider": "Osprey Charging (Contactless)", "category": "Public", "charger_kw": 150, "energy_price": 0.87, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Edit to local tariff if needed."},
        {"provider": "Electroverse", "category": "Public", "charger_kw": 150, "energy_price": np.nan, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Variable by partner network."},
        {"provider": "Zapmap Zap-Pay", "category": "Public", "charger_kw": 150, "energy_price": np.nan, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Variable by network."},
        {"provider": "Plugsurfing", "category": "Public", "charger_kw": 150, "energy_price": np.nan, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Variable by operator."},
        {"provider": "IZIVIA Pass", "category": "Public", "charger_kw": 150, "energy_price": np.nan, "time_price": 0.00, "session_fee": 0.00, "currency": "EUR", "notes": "Variable roaming."},
        {"provider": "Electra+", "category": "Public", "charger_kw": 150, "energy_price": 0.49, "time_price": 0.00, "session_fee": 0.00, "currency": "EUR", "notes": "Country/plan dependent."},
        {"provider": "Pod Point", "category": "Public", "charger_kw": 75, "energy_price": 0.69, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Site dependent."},
        {"provider": "BP Pulse PAYG App", "category": "Public", "charger_kw": 150, "energy_price": 0.87, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Edit to latest tariff if needed."},
        {"provider": "Freshmile", "category": "Public", "charger_kw": 50, "energy_price": 0.25, "time_price": 0.05, "session_fee": 0.00, "currency": "EUR", "notes": "kWh + per-minute model; verify in app for station."},

        # Home providers (energy price will be overridden by slider 6p-30p)
        {"provider": "Home - Octopus", "category": "Home", "charger_kw": 7, "energy_price": 0.08, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Set your own home tariff with slider."},
        {"provider": "Home - E.ON Next", "category": "Home", "charger_kw": 7, "energy_price": 0.09, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Set your own home tariff with slider."},
        {"provider": "Home - EDF", "category": "Home", "charger_kw": 7, "energy_price": 0.10, "time_price": 0.00, "session_fee": 0.00, "currency": "GBP", "notes": "Set your own home tariff with slider."},
    ]
)

if "vehicles_df" not in st.session_state:
    st.session_state.vehicles_df = DEFAULT_VEHICLES.copy()
if "providers_df" not in st.session_state:
    st.session_state.providers_df = DEFAULT_PROVIDERS.copy()

# ---------------------------------------------------
# LIVE FX (EUR base -> GBP, USD)
# ---------------------------------------------------
@st.cache_data(ttl=1800)
def get_fx_rates():
    fallback = {"EUR": 1.0, "GBP": 0.87, "USD": 1.10, "_date": "fallback"}
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=GBP,USD", timeout=7)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        return {
            "EUR": 1.0,
            "GBP": float(rates.get("GBP", fallback["GBP"])),
            "USD": float(rates.get("USD", fallback["USD"])),
            "_date": data.get("date", "unknown"),
        }
    except Exception:
        return fallback


rates = get_fx_rates()


def convert(amount, from_curr, to_curr):
    if from_curr == to_curr:
        return amount
    if from_curr not in rates or to_curr not in rates:
        return amount
    eur_value = amount if from_curr == "EUR" else amount / rates[from_curr]
    return eur_value * rates[to_curr]


def charging_time_minutes(battery_kwh, effective_kw, start_pct, end_pct, taper=True):
    if effective_kw <= 0 or end_pct <= start_pct:
        return 0.0
    mins = 0.0
    current = float(start_pct)
    while current < end_pct:
        if taper:
            if current < 80:
                rate = effective_kw
                next_stop = min(end_pct, 80)
            elif current < 90:
                rate = effective_kw * 0.5
                next_stop = min(end_pct, 90)
            else:
                rate = effective_kw * 0.3
                next_stop = end_pct
        else:
            rate = effective_kw
            next_stop = end_pct
        segment = (next_stop - current) / 100
        energy = battery_kwh * segment
        mins += (energy / max(rate, 0.1)) * 60
        current = next_stop
    return mins


def sanitize_df(df):
    x = df.copy()
    for col in ["charger_kw", "energy_price", "time_price", "session_fee"]:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    x["provider"] = x["provider"].astype(str).str.strip()
    x["category"] = x["category"].astype(str).str.strip()
    x["currency"] = x["currency"].astype(str).str.upper().str.strip()
    x = x.dropna(subset=["provider", "charger_kw", "currency"])
    return x[x["provider"] != ""]


def select_provider(label, key_prefix, providers_df):
    provider_names = sorted(providers_df["provider"].dropna().unique().tolist())
    provider_name = st.selectbox(f"{label} Provider", provider_names, key=f"{key_prefix}_provider")

    p_df = providers_df[providers_df["provider"] == provider_name].copy()
    speed_options = sorted(p_df["charger_kw"].dropna().unique().tolist())
    charger_kw = st.selectbox(
        f"{label} Charger Speed (kW)",
        speed_options,
        key=f"{key_prefix}_speed",
        format_func=lambda v: f"{int(v)} kW" if float(v).is_integer() else f"{v:.1f} kW",
    )

    row = p_df[np.isclose(p_df["charger_kw"], charger_kw)].iloc[0]
    category = row["category"]
    currency = row["currency"]

    energy_price = row["energy_price"] if not pd.isna(row["energy_price"]) else 0.0
    time_price = row["time_price"] if not pd.isna(row["time_price"]) else 0.0
    session_fee = row["session_fee"] if not pd.isna(row["session_fee"]) else 0.0

    # Home tariff slider 6p-30p (GBP/kWh)
    if category.lower() == "home":
        home_pence = st.slider(
            f"{label} Home Tariff (p/kWh)",
            min_value=6,
            max_value=30,
            value=int(round(float(energy_price) * 100)) if energy_price > 0 else 8,
            key=f"{key_prefix}_home_tariff",
            help="Home tariff override between 6p and 30p per kWh.",
        )
        energy_price = home_pence / 100.0
        currency = "GBP"
        time_price = 0.0  # most home tariffs modeled as energy-only
        session_fee = 0.0
    elif pd.isna(row["energy_price"]):
        energy_price = st.number_input(
            f"{label} Live Energy Price ({currency}/kWh)",
            min_value=0.0,
            value=0.75,
            step=0.01,
            key=f"{key_prefix}_live_kwh",
        )

    st.caption(f"{label} Notes: {row.get('notes', '')}")

    return {
        "provider": provider_name,
        "category": category,
        "charger_kw": float(charger_kw),
        "energy_price": float(energy_price),
        "time_price": float(time_price),
        "session_fee": float(session_fee),
        "currency": currency,
    }


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h2 style="margin:0;">EV Charge Pro UK</h2>
      <p>Compares providers by charger speed, car max charging capability, and live FX conversion.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# SIDEBAR JOURNEY
# ---------------------------------------------------
with st.sidebar:
    st.header("Journey Setup")
    vehicle_names = st.session_state.vehicles_df["model"].dropna().tolist()
    vehicle = st.selectbox("Vehicle", vehicle_names)

    v_row = st.session_state.vehicles_df[st.session_state.vehicles_df["model"] == vehicle].iloc[0]
    battery_kwh = float(v_row["battery_kwh"])
    default_max_dc = float(v_row["max_dc_kw"])

    vehicle_max_kw = st.slider(
        "Car Max DC Charging (kW)",
        min_value=20,
        max_value=400,
        value=int(default_max_dc),
        step=1,
        help="Effective charging power = min(provider charger kW, car max kW).",
    )

    start_pct = st.slider("Current Charge (%)", 0, 100, 20)
    end_pct = st.slider("Target Charge (%)", 0, 100, 80)

    st.divider()
    st.subheader("Advanced")
    taper = st.toggle("Apply Charging Taper", value=True)
    efficiency_loss = st.slider("Efficiency Loss (%)", 0, 20, 6)
    miles_per_kwh = st.number_input("Miles per kWh", min_value=1.0, max_value=6.0, value=3.5, step=0.1)
    comparison_currency = st.selectbox("Compare In", ["GBP", "EUR", "USD"], index=0)

# ---------------------------------------------------
# EDITABLE TABLES
# ---------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Provider Database (Add unlimited rows)")
st.caption("Each row = one provider + one charger speed. Include kWh, per-minute, session fee as needed.")
st.session_state.providers_df = st.data_editor(
    st.session_state.providers_df,
    num_rows="dynamic",
    use_container_width=True,
    key="provider_editor",
)
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Edit Vehicle List"):
    st.session_state.vehicles_df = st.data_editor(
        st.session_state.vehicles_df,
        num_rows="dynamic",
        use_container_width=True,
        key="vehicle_editor",
    )

providers_clean = sanitize_df(st.session_state.providers_df)

# ---------------------------------------------------
# PROVIDER COMPARISON
# ---------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Compare Two Providers")
c1, c2 = st.columns(2)
with c1:
    provider_a = select_provider("Provider A", "provider_a", providers_clean)
with c2:
    provider_b = select_provider("Provider B", "provider_b", providers_clean)

run_compare = st.button("Compare Providers", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if run_compare:
    if end_pct <= start_pct:
        st.error("Target Charge must be greater than Current Charge.")
    else:
        energy_needed = battery_kwh * ((end_pct - start_pct) / 100.0)
        energy_needed *= (1 + efficiency_loss / 100.0)
        miles_added = energy_needed * miles_per_kwh

        # key logic requested: cap by car max kW
        effective_kw_a = min(provider_a["charger_kw"], float(vehicle_max_kw))
        effective_kw_b = min(provider_b["charger_kw"], float(vehicle_max_kw))

        time_a = charging_time_minutes(battery_kwh, effective_kw_a, start_pct, end_pct, taper)
        time_b = charging_time_minutes(battery_kwh, effective_kw_b, start_pct, end_pct, taper)

        native_cost_a = (energy_needed * provider_a["energy_price"]) + (time_a * provider_a["time_price"]) + provider_a["session_fee"]
        native_cost_b = (energy_needed * provider_b["energy_price"]) + (time_b * provider_b["time_price"]) + provider_b["session_fee"]

        cost_a = convert(native_cost_a, provider_a["currency"], comparison_currency)
        cost_b = convert(native_cost_b, provider_b["currency"], comparison_currency)

        per100_a = (cost_a / miles_added * 100) if miles_added > 0 else 0.0
        per100_b = (cost_b / miles_added * 100) if miles_added > 0 else 0.0

        st.subheader("Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Energy Added", f"{energy_needed:.2f} kWh")
        m2.metric("Miles Added", f"{miles_added:.1f} mi")
        m3.metric("Provider A Time", f"{time_a:.1f} min")
        m4.metric("Provider B Time", f"{time_b:.1f} min")

        r1, r2 = st.columns(2)
        r1.metric(provider_a["provider"], f"{cost_a:.2f} {comparison_currency}", f"{per100_a:.2f} /100mi")
        r2.metric(provider_b["provider"], f"{cost_b:.2f} {comparison_currency}", f"{per100_b:.2f} /100mi")

        st.write(
            f"Provider A effective power: min({provider_a['charger_kw']:.0f}kW station, {vehicle_max_kw:.0f}kW car) = **{effective_kw_a:.0f}kW**"
        )
        st.write(
            f"Provider B effective power: min({provider_b['charger_kw']:.0f}kW station, {vehicle_max_kw:.0f}kW car) = **{effective_kw_b:.0f}kW**"
        )

        # Cost curve to 100%
        pct_range = np.linspace(start_pct, 100, 24)
        curve_a, curve_b = [], []
        for pct in pct_range:
            e = battery_kwh * ((pct - start_pct) / 100.0)
            e *= (1 + efficiency_loss / 100.0)

            t_a = charging_time_minutes(battery_kwh, effective_kw_a, start_pct, pct, taper)
            t_b = charging_time_minutes(battery_kwh, effective_kw_b, start_pct, pct, taper)

            n_a = (e * provider_a["energy_price"]) + (t_a * provider_a["time_price"]) + provider_a["session_fee"]
            n_b = (e * provider_b["energy_price"]) + (t_b * provider_b["time_price"]) + provider_b["session_fee"]

            curve_a.append(convert(n_a, provider_a["currency"], comparison_currency))
            curve_b.append(convert(n_b, provider_b["currency"], comparison_currency))

        df_chart = pd.DataFrame(
            {
                "Charge %": pct_range,
                f"A: {provider_a['provider']}": curve_a,
                f"B: {provider_b['provider']}": curve_b,
            }
        )
        st.line_chart(df_chart.set_index("Charge %"), use_container_width=True)

st.markdown(
    f'<p class="small-note">Live FX (Frankfurter/ECB): EUR→GBP {rates["GBP"]:.5f}, EUR→USD {rates["USD"]:.5f}, date {rates["_date"]}. '
    "Tariffs vary by site/time and should be verified in-app before charging.</p>",
    unsafe_allow_html=True,
)
