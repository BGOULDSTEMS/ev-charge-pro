import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="EV Charge Pro UK", page_icon="⚡", layout="wide")

# ---------------------------------------------------
# PROFESSIONAL UI (iOS/mobile friendly)
# ---------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #f4f7fb;
        --surface: #ffffff;
        --text: #0f172a;
        --muted: #5b6474;
        --brand: #0b3a66;
        --accent: #0f766e;
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
        padding-top: 1.1rem;
        padding-bottom: 2rem;
      }
      .hero {
        background: linear-gradient(110deg, #0b3a66 0%, #155e75 100%);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: white;
        margin-bottom: 0.9rem;
      }
      .hero p {
        margin: 0.3rem 0 0;
        color: #e8eef7;
      }
      .panel {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.9rem 1rem 0.6rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        margin-bottom: 1rem;
      }
      div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
      }
      .small-note {
        color: var(--muted);
        font-size: 0.9rem;
      }
      .stButton > button {
        min-height: 46px;
        font-weight: 600;
      }
      @media (max-width: 900px) {
        .block-container {
          padding-left: 0.8rem;
          padding-right: 0.8rem;
        }
        div[data-testid="column"] {
          width: 100% !important;
          flex: 1 1 100% !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# TOP UK EV MODELS (expanded to 20, editable in-app)
# ---------------------------------------------------
DEFAULT_VEHICLES = pd.DataFrame(
    [
        {"model": "Tesla Model Y Long Range", "battery_kwh": 75.0},
        {"model": "Tesla Model 3 Long Range", "battery_kwh": 75.0},
        {"model": "Audi Q4 e-tron 77", "battery_kwh": 77.0},
        {"model": "Audi Q6 e-tron", "battery_kwh": 94.9},
        {"model": "Ford Explorer Extended Range", "battery_kwh": 79.0},
        {"model": "BMW i4 eDrive40", "battery_kwh": 81.3},
        {"model": "Skoda Enyaq 85", "battery_kwh": 82.0},
        {"model": "Kia EV3 Long Range", "battery_kwh": 81.4},
        {"model": "Skoda Elroq 85", "battery_kwh": 82.0},
        {"model": "Volvo EX30 Extended Range", "battery_kwh": 69.0},
        {"model": "MG4 Long Range", "battery_kwh": 77.0},
        {"model": "Hyundai Kona Electric 65", "battery_kwh": 65.4},
        {"model": "VW ID.4 Pro", "battery_kwh": 77.0},
        {"model": "Nissan Ariya 87", "battery_kwh": 87.0},
        {"model": "Kia EV6 Long Range", "battery_kwh": 84.0},
        {"model": "Hyundai IONIQ 5 Long Range", "battery_kwh": 84.0},
        {"model": "Mercedes EQA 350", "battery_kwh": 70.5},
        {"model": "Polestar 2 Long Range", "battery_kwh": 82.0},
        {"model": "BYD Dolphin Comfort", "battery_kwh": 60.4},
        {"model": "Vauxhall Corsa Electric", "battery_kwh": 51.0},
    ]
)

# ---------------------------------------------------
# DEFAULT CHARGING OFFERS (networks + cards)
# pricing_type: fixed or variable
# variable rows require manual kWh entry before compare
# ---------------------------------------------------
DEFAULT_OFFERS = pd.DataFrame(
    [
        # Requested charging station networks
        {
            "offer_name": "MFG EV Power (Rapid/Ultra typical)",
            "pricing_type": "fixed",
            "energy_price": 0.79,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Zapmap guide value; network can vary by site/speed.",
        },
        {
            "offer_name": "EVYVE Rapid (PAYG flat)",
            "pricing_type": "fixed",
            "energy_price": 0.80,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "EVYVE FAQ: flat 80p/kWh on rapid points.",
        },
        {
            "offer_name": "Osprey (contactless)",
            "pricing_type": "fixed",
            "energy_price": 0.87,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Official Osprey contactless tariff.",
        },
        {
            "offer_name": "Osprey (app)",
            "pricing_type": "fixed",
            "energy_price": 0.82,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Official Osprey app tariff.",
        },
        # Existing + requested card systems/payment methods
        {
            "offer_name": "Electroverse (roaming)",
            "pricing_type": "variable",
            "energy_price": np.nan,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Variable by partner network; set exact kWh before compare.",
        },
        {
            "offer_name": "Zapmap Zap-Pay",
            "pricing_type": "variable",
            "energy_price": np.nan,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Variable by network/tariff in app.",
        },
        {
            "offer_name": "Zapmap Premium (5% off first 50 kWh/mo)",
            "pricing_type": "variable",
            "energy_price": np.nan,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Enter discounted effective kWh for your session.",
        },
        {
            "offer_name": "Plugsurfing",
            "pricing_type": "variable",
            "energy_price": np.nan,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Operator sets price; check app tariff per charger.",
        },
        {
            "offer_name": "IZIVIA Pass",
            "pricing_type": "variable",
            "energy_price": np.nan,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "EUR",
            "notes": "Interoperable pass; pricing varies by network.",
        },
        {
            "offer_name": "Electra+ Start (EU example)",
            "pricing_type": "fixed",
            "energy_price": 0.49,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "EUR",
            "notes": "Electra+ rate is country-dependent; check UK availability.",
        },
        {
            "offer_name": "Electra+ Boost (EU example)",
            "pricing_type": "fixed",
            "energy_price": 0.39,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "EUR",
            "notes": "Electra+ rate is country-dependent; check UK availability.",
        },
        {
            "offer_name": "Pod Point Tesco 7kW (example)",
            "pricing_type": "fixed",
            "energy_price": 0.44,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Example live site tariff; site-specific.",
        },
        {
            "offer_name": "Pod Point Tesco 22kW (example)",
            "pricing_type": "fixed",
            "energy_price": 0.49,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Example live site tariff; site-specific.",
        },
        {
            "offer_name": "Pod Point Tesco 50kW (example)",
            "pricing_type": "fixed",
            "energy_price": 0.62,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Example live site tariff; site-specific.",
        },
        {
            "offer_name": "Pod Point Tesco 75kW (example)",
            "pricing_type": "fixed",
            "energy_price": 0.69,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Example live site tariff; site-specific.",
        },
        {
            "offer_name": "bp pulse Subscriber 150kW+",
            "pricing_type": "fixed",
            "energy_price": 0.69,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Monthly subscription fee not included.",
        },
        {
            "offer_name": "bp pulse PAYG app 150kW+",
            "pricing_type": "fixed",
            "energy_price": 0.87,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Official on-the-go PAYG value.",
        },
        {
            "offer_name": "bp pulse Contactless 150kW+",
            "pricing_type": "fixed",
            "energy_price": 0.89,
            "time_price": 0.00,
            "session_fee": 0.00,
            "currency": "GBP",
            "notes": "Official contactless value.",
        },
    ]
)

if "vehicles_df" not in st.session_state:
    st.session_state.vehicles_df = DEFAULT_VEHICLES.copy()

if "offers_df" not in st.session_state:
    st.session_state.offers_df = DEFAULT_OFFERS.copy()

# ---------------------------------------------------
# FX
# ---------------------------------------------------
@st.cache_data(ttl=3600)
def get_fx_rates():
    fallback = {"EUR": 1.0, "GBP": 0.88, "USD": 1.10}
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=EUR", timeout=7)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates")
        if isinstance(rates, dict):
            return rates
        return fallback
    except Exception:
        return fallback


rates = get_fx_rates()


def convert(amount, from_curr, to_curr):
    if from_curr == to_curr:
        return amount
    eur_value = amount / rates.get(from_curr, 1) if from_curr != "EUR" else amount
    return eur_value * rates.get(to_curr, 1)


def charging_time_minutes(battery_kwh, charger_kw, start_pct, end_pct, taper=True):
    if charger_kw <= 0 or end_pct <= start_pct:
        return 0.0

    mins = 0.0
    current = float(start_pct)
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
        energy = battery_kwh * segment
        mins += (energy / max(rate, 0.1)) * 60
        current = next_stop
    return mins


def resolve_offer(offer_name):
    df = st.session_state.offers_df
    row = df[df["offer_name"] == offer_name].iloc[0]

    energy = row["energy_price"]
    if pd.isna(energy):
        energy = st.number_input(
            f"Set live kWh price for '{offer_name}' ({row['currency']}/kWh)",
            min_value=0.0,
            value=0.79,
            step=0.01,
            key=f"live_kwh_{offer_name}",
        )

    return {
        "name": row["offer_name"],
        "pricing_type": row["pricing_type"],
        "energy": float(energy),
        "time": float(row["time_price"]) if not pd.isna(row["time_price"]) else 0.0,
        "session": float(row["session_fee"]) if not pd.isna(row["session_fee"]) else 0.0,
        "currency": row["currency"],
        "notes": row["notes"],
    }


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h2 style="margin:0;">EV Charge Pro UK</h2>
      <p>Compare charging networks, roaming cards, and tariffs. Add unlimited station rows and update prices any time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.image(
    "https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b?auto=format&fit=crop&w=1800&q=80",
    use_container_width=True,
    caption="Public EV charging comparison for UK drivers",
)

# ---------------------------------------------------
# SIDEBAR SETUP
# ---------------------------------------------------
with st.sidebar:
    st.header("Journey Setup")

    vehicle_names = st.session_state.vehicles_df["model"].dropna().tolist()
    vehicle = st.selectbox("Vehicle", vehicle_names)
    battery_kwh = float(
        st.session_state.vehicles_df.loc[
            st.session_state.vehicles_df["model"] == vehicle, "battery_kwh"
        ].iloc[0]
    )

    start_pct = st.slider("Current charge (%)", 0, 100, 20)
    end_pct = st.slider("Target charge (%)", 0, 100, 80)
    charger_kw = st.slider("Charger power (kW)", 7, 400, 150)

    st.divider()
    st.subheader("Advanced")
    taper = st.toggle("Apply taper model", value=True)
    efficiency_loss = st.slider("Charging loss (%)", 0, 20, 6)
    miles_per_kwh = st.number_input("Miles per kWh", min_value=1.0, max_value=6.0, value=3.5, step=0.1)
    comparison_currency = st.selectbox("Display currency", ["GBP", "EUR", "USD"], index=0)

# ---------------------------------------------------
# EDIT TABLES
# ---------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Charging Offers (Add Unlimited Rows)")
st.caption("Edit tariffs directly. Use 'variable' pricing for cards/networks where price changes by charger.")
st.session_state.offers_df = st.data_editor(
    st.session_state.offers_df,
    num_rows="dynamic",
    use_container_width=True,
    key="offers_editor",
)
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Edit UK EV Vehicle List (Top 20 preloaded)"):
    st.session_state.vehicles_df = st.data_editor(
        st.session_state.vehicles_df,
        num_rows="dynamic",
        use_container_width=True,
        key="vehicle_editor",
    )

# ---------------------------------------------------
# COMPARE
# ---------------------------------------------------
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Compare Two Offers")
offer_names = st.session_state.offers_df["offer_name"].dropna().tolist()
c1, c2 = st.columns(2)
offer_a_name = c1.selectbox("Offer A", offer_names, index=0)
offer_b_name = c2.selectbox("Offer B", offer_names, index=1 if len(offer_names) > 1 else 0)

offer_a = resolve_offer(offer_a_name)
offer_b = resolve_offer(offer_b_name)

st.caption(f"A notes: {offer_a['notes']}")
st.caption(f"B notes: {offer_b['notes']}")

run_compare = st.button("Compare Providers", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if run_compare:
    if end_pct <= start_pct:
        st.error("Target charge must be higher than current charge.")
    else:
        energy_needed = battery_kwh * ((end_pct - start_pct) / 100)
        energy_needed *= (1 + efficiency_loss / 100)
        time_minutes = charging_time_minutes(battery_kwh, charger_kw, start_pct, end_pct, taper)

        cost_a_native = (energy_needed * offer_a["energy"]) + (time_minutes * offer_a["time"]) + offer_a["session"]
        cost_b_native = (energy_needed * offer_b["energy"]) + (time_minutes * offer_b["time"]) + offer_b["session"]

        cost_a = convert(cost_a_native, offer_a["currency"], comparison_currency)
        cost_b = convert(cost_b_native, offer_b["currency"], comparison_currency)

        miles_added = energy_needed * miles_per_kwh
        per100_a = (cost_a / miles_added * 100) if miles_added > 0 else 0
        per100_b = (cost_b / miles_added * 100) if miles_added > 0 else 0

        st.subheader("Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Energy Added", f"{energy_needed:.2f} kWh")
        m2.metric("Charge Time", f"{time_minutes:.1f} min")
        m3.metric("Miles Added", f"{miles_added:.1f} mi")
        m4.metric("Vehicle Battery", f"{battery_kwh:.1f} kWh")

        r1, r2 = st.columns(2)
        r1.metric(offer_a["name"], f"{cost_a:.2f} {comparison_currency}", f"{per100_a:.2f} /100mi")
        r2.metric(offer_b["name"], f"{cost_b:.2f} {comparison_currency}", f"{per100_b:.2f} /100mi")

        pct_range = np.linspace(start_pct, 100, 24)
        curve_a, curve_b = [], []
        for pct in pct_range:
            e = battery_kwh * ((pct - start_pct) / 100) * (1 + efficiency_loss / 100)
            t = charging_time_minutes(battery_kwh, charger_kw, start_pct, pct, taper)

            c_a = convert((e * offer_a["energy"]) + (t * offer_a["time"]) + offer_a["session"], offer_a["currency"], comparison_currency)
            c_b = convert((e * offer_b["energy"]) + (t * offer_b["time"]) + offer_b["session"], offer_b["currency"], comparison_currency)
            curve_a.append(c_a)
            curve_b.append(c_b)

        chart_df = pd.DataFrame({"Charge %": pct_range, offer_a["name"]: curve_a, offer_b["name"]: curve_b})
        st.line_chart(chart_df.set_index("Charge %"), use_container_width=True)

        st.image(
            "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1600&q=80",
            use_container_width=True,
            caption="Use real network/card tariff rows to model your actual trip cost.",
        )

st.markdown(
    f'<p class="small-note">FX base EUR, cached 60 mins. Current GBP rate: {rates.get("GBP", 0):.4f}. Public tariffs change frequently: always verify in-app or on charger screen before charging.</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# SOURCES (for tariff defaults)
# ---------------------------------------------------
with st.expander("Tariff Source Links Used (check for latest updates)"):
    st.markdown(
        """
- Osprey official pricing: https://www.ospreycharging.co.uk/pricing-and-payment
- EVYVE official FAQ (80p/kWh rapid): https://evyve.co.uk/
- MFG EV Power guide (Zapmap): https://www.zapmap.com/ev-guides/public-charging-point-networks/mfg-network
- bp pulse official public charging pricing: https://www.bppulse.co.uk/public-ev-charging
- bp pulse pricing table mirror page: https://marketing.d3.pulsevision.club/public-ev-charging/pricing
- Pod Point network overview (Zapmap): https://www.zap-map.com/ev-guides/public-charging-point-networks/pod-point-network/
- Pod Point example live tariffs: https://charge.pod-point.com/
- Plugsurfing pricing model note: https://support.plugsurfing.com/hc/en-us/articles/11002150340253-Pricing-information
- Zapmap tariff/payment terms: https://www.zapmap.com/terms-of-use
- Zapmap Premium 5% discount terms: https://www.zapmap.com/sites/default/files/2024-07/Terms%20and%20conditions%20-%20Zapmap%20Premium%20charging%20discount.pdf
- Electra+ rates (country-dependent): https://intercom.help/go-electra/en/articles/10749707-electra-rates
- IZIVIA Pass overview: https://izivia.com/pass-de-recharge-voitures-electriques
- UK EV popularity reference (SMMT top 10 2025 summary): https://www.rac.co.uk/drive/electric-cars/choosing/electric-car-statistics-and-data/
"""
    )
