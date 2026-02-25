import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="EV Charge Pro", page_icon="⚡", layout="wide")

# -------------------------------------------------------------------
# DESIGN SYSTEM (mobile-first + professional typography)
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #f5f7fb;
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
        max-width: 1120px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
      }

      h1, h2, h3, h4 {
        color: var(--text);
        letter-spacing: -0.01em;
      }

      .hero {
        background: linear-gradient(110deg, #0b3a66 0%, #155e75 100%);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        color: white;
        margin-bottom: 0.9rem;
        border: 1px solid rgba(255,255,255,0.08);
      }

      .hero p {
        margin: 0.3rem 0 0;
        color: #e7eef9;
      }

      .panel {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.9rem 1rem 0.5rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
      }

      div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
      }

      div[data-testid="stMetricLabel"] {
        color: var(--muted);
      }

      .small-note {
        color: var(--muted);
        font-size: 0.9rem;
      }

      /* Make controls feel better on touch devices */
      .stButton > button {
        min-height: 46px;
        font-weight: 600;
      }

      /* Responsive behavior for phones/tablets */
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

# -------------------------------------------------------------------
# DATA
# -------------------------------------------------------------------
VEHICLES = {
    "Kia EV3 Long Range": 81.1,
    "Tesla Model 3 Long Range": 75,
    "Hyundai Kona Electric 65kWh": 65,
    "VW ID.4 Pro": 77,
    "Nissan Ariya 87kWh": 87,
    "Custom": None,
}

DEFAULT_PROVIDERS = {
    "Ionity": {"energy": 0.69, "time": 0.00, "currency": "EUR"},
    "Tesla Supercharger UK": {"energy": 0.44, "time": 0.00, "currency": "GBP"},
    "Shell Recharge UK": {"energy": 0.79, "time": 0.00, "currency": "GBP"},
    "Freshmile": {"energy": 0.30, "time": 0.30, "currency": "EUR"},
    "Electroverse": {"energy": 0.80, "time": 0.00, "currency": "GBP"},
    "Custom": {"energy": 0.00, "time": 0.00, "currency": "GBP"},
}

if "providers" not in st.session_state:
    st.session_state.providers = DEFAULT_PROVIDERS.copy()

@st.cache_data(ttl=3600)
def get_fx_rates():
    fallback = {"EUR": 1.0, "GBP": 0.88, "USD": 1.10}
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=EUR", timeout=5)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates")
        if isinstance(rates, dict):
            return rates
        st.warning("Exchange API returned unexpected data. Using fallback rates.")
        return fallback
    except Exception as exc:
        st.warning(f"Could not fetch live exchange rates ({exc}). Using fallback rates.")
        return fallback

rates = get_fx_rates()

def convert(amount, from_curr, to_curr):
    if from_curr == to_curr:
        return amount
    eur_value = amount / rates.get(from_curr, 1) if from_curr != "EUR" else amount
    return eur_value * rates.get(to_curr, 1)

def charging_time(battery, charger_kw, start_pct, end_pct, taper=True):
    if charger_kw <= 0 or end_pct <= start_pct:
        return 0.0
    minutes = 0.0
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
        energy = battery * segment
        minutes += (energy / max(rate, 0.1)) * 60
        current = next_stop
    return minutes

# -------------------------------------------------------------------
# HEADER + IMAGERY
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h2 style="margin:0;">EV Charge Pro</h2>
      <p>Compare real-world charging costs by provider, time model, and currency.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.image(
    "https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b?auto=format&fit=crop&w=1800&q=80",
    use_container_width=True,
    caption="Plan charging with clearer cost visibility.",
)

# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Setup")
    vehicle = st.selectbox("Vehicle", list(VEHICLES.keys()))
    if vehicle == "Custom":
        battery_kwh = st.number_input(
            "Battery size (kWh)", min_value=10.0, max_value=200.0, value=80.0, step=0.5
        )
    else:
        battery_kwh = VEHICLES[vehicle]
        st.caption(f"Battery size: {battery_kwh} kWh")

    start_pct = st.slider("Current charge (%)", 0, 100, 50)
    end_pct = st.slider("Target charge (%)", 0, 100, 80)
    charger_kw = st.slider("Charger power (kW)", 7, 400, 75)

    st.divider()
    st.subheader("Advanced")
    efficiency_loss = st.slider("Efficiency loss (%)", 0, 15, 5)
    miles_per_kwh = st.number_input(
        "Miles per kWh", min_value=1.0, max_value=6.0, value=3.5, step=0.1
    )
    taper = st.toggle("Apply charging taper", value=True)
    comparison_currency = st.selectbox("Compare in", ["GBP", "EUR", "USD"])

# -------------------------------------------------------------------
# PROVIDERS
# -------------------------------------------------------------------
def provider_inputs(name, col):
    p = st.session_state.providers[name]
    with col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader(name)
        energy = st.number_input(
            f"Energy ({p['currency']}/kWh)",
            min_value=0.0,
            value=float(p["energy"]),
            step=0.01,
            key=f"{name}_energy",
        )
        time_cost = st.number_input(
            f"Time ({p['currency']}/min)",
            min_value=0.0,
            value=float(p["time"]),
            step=0.01,
            key=f"{name}_time",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    return energy, time_cost, p["currency"]

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Providers")
provider_names = list(st.session_state.providers.keys())

pcol1, pcol2 = st.columns(2)
prov_a = pcol1.selectbox("Provider A", provider_names, index=0)
prov_b = pcol2.selectbox("Provider B", provider_names, index=1 if len(provider_names) > 1 else 0)

c1, c2 = st.columns(2)
energy_a, time_a, curr_a = provider_inputs(prov_a, c1)
energy_b, time_b, curr_b = provider_inputs(prov_b, c2)
st.markdown("</div>", unsafe_allow_html=True)

run_compare = st.button("Compare Providers", type="primary", use_container_width=True)

# -------------------------------------------------------------------
# RESULTS
# -------------------------------------------------------------------
if run_compare:
    if end_pct <= start_pct:
        st.error("Target charge must be higher than current charge.")
    else:
        energy_needed = battery_kwh * ((end_pct - start_pct) / 100)
        energy_needed *= 1 + (efficiency_loss / 100)

        time_minutes = charging_time(battery_kwh, charger_kw, start_pct, end_pct, taper)

        cost_a = (energy_needed * energy_a) + (time_minutes * time_a)
        cost_b = (energy_needed * energy_b) + (time_minutes * time_b)

        cost_a_conv = convert(cost_a, curr_a, comparison_currency)
        cost_b_conv = convert(cost_b, curr_b, comparison_currency)

        miles_added = energy_needed * miles_per_kwh
        per_100_a = (cost_a_conv / miles_added * 100) if miles_added > 0 else 0
        per_100_b = (cost_b_conv / miles_added * 100) if miles_added > 0 else 0

        st.subheader("Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Energy Added", f"{energy_needed:.2f} kWh")
        m2.metric("Charge Time", f"{time_minutes:.1f} min")
        m3.metric("Miles Added", f"{miles_added:.1f} mi")
        m4.metric("Currency", comparison_currency)

        r1, r2 = st.columns(2)
        r1.metric(prov_a, f"{cost_a_conv:.2f} {comparison_currency}", f"{per_100_a:.2f} /100mi")
        r2.metric(prov_b, f"{cost_b_conv:.2f} {comparison_currency}", f"{per_100_b:.2f} /100mi")

        pct_range = np.linspace(start_pct, 100, 24)
        cost_curve_a = []
        cost_curve_b = []

        for pct in pct_range:
            e = battery_kwh * ((pct - start_pct) / 100)
            e *= 1 + (efficiency_loss / 100)
            t = charging_time(battery_kwh, charger_kw, start_pct, pct, taper)
            c_a = convert((e * energy_a) + (t * time_a), curr_a, comparison_currency)
            c_b = convert((e * energy_b) + (t * time_b), curr_b, comparison_currency)
            cost_curve_a.append(c_a)
            cost_curve_b.append(c_b)

        df = pd.DataFrame({"Charge %": pct_range, prov_a: cost_curve_a, prov_b: cost_curve_b})
        st.line_chart(df.set_index("Charge %"), use_container_width=True)

        # Contextual image to improve UX narrative
        if charger_kw >= 50:
            st.image(
                "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1600&q=80",
                use_container_width=True,
                caption="Rapid/DC charging profile context.",
            )
        else:
            st.image(
                "https://images.unsplash.com/photo-1558389186-438424b00a6c?auto=format&fit=crop&w=1600&q=80",
                use_container_width=True,
                caption="Home/AC charging profile context.",
            )

        st.markdown(
            f'<p class="small-note">FX base: EUR. Rates refresh every 60 minutes. Current GBP rate: {rates.get("GBP", 0):.4f}</p>',
            unsafe_allow_html=True,
        )
