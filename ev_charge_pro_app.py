import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="EV Charge Pro UK", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&display=swap');

      :root{
        --bg:#050a14;
        --bg-2:#0a1324;
        --card:rgba(10,18,34,.88);
        --line:rgba(139,173,240,.35);
        --text:#ffffff;
      }

      html, body, [data-testid="stAppViewContainer"] {
        -webkit-overflow-scrolling: touch;
        overscroll-behavior-y: contain;
      }

      .stApp{
        background:
          radial-gradient(1200px 460px at 10% -20%, rgba(0,173,239,.20), transparent 58%),
          radial-gradient(900px 360px at 95% -25%, rgba(33,130,255,.18), transparent 60%),
          linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
        color: var(--text);
        font-family: "Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      .block-container{max-width:1280px;padding-top:.55rem;padding-bottom:1.8rem;}
      h1,h2,h3,h4{color:#fff !important;letter-spacing:-.01em;font-weight:700;}
      .stMarkdown p, .stMarkdown li, .stMarkdown span, .stCaption, .small-note { color:#fff !important; }
      label, .stCheckbox label, .stRadio label, .stSelectbox label, .stNumberInput label { color:#fff !important; }

      div[data-testid="stSlider"], div[data-testid="stSlider"] * {
        touch-action: pan-y !important;
      }

      .top-banner{
        background: rgba(7, 13, 24, 0.86);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .75rem 1rem;
        margin-bottom: .8rem;
        color:#fff;
      }

      .hero{
        border:1px solid var(--line);
        border-radius:18px;
        overflow:hidden;
        margin-bottom:.9rem;
        min-height:190px;
        background-image:
          linear-gradient(108deg, rgba(4,9,17,.92) 16%, rgba(4,9,17,.65) 52%, rgba(4,9,17,.22) 100%),
          url('https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b?auto=format&fit=crop&w=2000&q=80');
        background-size:cover;
        background-position:center;
      }

      .hero-content{padding:1.2rem 1.15rem;max-width:760px;}
      .hero-content p{color:#fff !important;}

      .panel{
        background:var(--card);
        border:1px solid var(--line);
        border-radius:14px;
        padding:.88rem 1rem .72rem;
        margin-bottom:.85rem;
        backdrop-filter:blur(8px);
      }

      div[data-testid="stMetric"]{
        background: rgba(7,13,24,.94);
        border:1px solid var(--line);
        border-radius:12px;
        padding:.75rem .88rem;
      }
      div[data-testid="stMetricLabel"]{color:#fff !important;}
      .stButton > button{min-height:46px;font-weight:700;border-radius:10px;}

      /* ---- Force form controls to black text on light fields ---- */
      [data-testid="stSelectbox"] [data-baseweb="select"] * { color:#111 !important; }
      [data-testid="stSelectbox"] [data-baseweb="select"] { background:#fff !important; }

      /* Dropdown menu options (vehicle/provider lists) */
      div[role="listbox"] * { color:#111 !important; }
      div[role="option"] { color:#111 !important; }

      /* Number/text inputs */
      [data-testid="stNumberInput"] input,
      [data-testid="stTextInput"] input,
      [data-testid="stTextArea"] textarea {
        color:#111 !important;
        background:#fff !important;
      }

      @media (max-width: 920px){
        .block-container{padding-left:.7rem;padding-right:.7rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

VEHICLES = pd.DataFrame(
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
        {"model": "Custom", "battery_kwh": 80.0, "max_dc_kw": 150},
    ]
)

PROVIDER_PRESETS = {
    "MFG EV Power": {"energy": 0.79, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "EVYVE Charging Stations": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Osprey Charging (App)": {"energy": 0.82, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Osprey Charging (Contactless)": {"energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Electroverse": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Zapmap Zap-Pay": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Plugsurfing": {"energy": 0.80, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "IZIVIA Pass": {"energy": 0.75, "time": 0.00, "currency": "EUR", "default_kw": 150, "type": "public"},
    "Electra+": {"energy": 0.49, "time": 0.00, "currency": "EUR", "default_kw": 150, "type": "public"},
    "Pod Point": {"energy": 0.69, "time": 0.00, "currency": "GBP", "default_kw": 75, "type": "public"},
    "BP Pulse PAYG": {"energy": 0.87, "time": 0.00, "currency": "GBP", "default_kw": 150, "type": "public"},
    "Freshmile": {"energy": 0.25, "time": 0.05, "currency": "EUR", "default_kw": 50, "type": "public"},
    "Home Charging (Octopus-style)": {"energy": 0.08, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home"},
    "Home Charging (E.ON-style)": {"energy": 0.09, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home"},
    "Home Charging (EDF-style)": {"energy": 0.10, "time": 0.00, "currency": "GBP", "default_kw": 7, "type": "home"},
}

@st.cache_data(ttl=1800)
def get_fx_rates():
    fallback = {"EUR": 1.0, "GBP": 0.87, "USD": 1.10, "_date": "fallback"}
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=GBP,USD", timeout=8)
        r.raise_for_status()
        data = r.json()
        rr = data.get("rates", {})
        return {
            "EUR": 1.0,
            "GBP": float(rr.get("GBP", fallback["GBP"])),
            "USD": float(rr.get("USD", fallback["USD"])),
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

        segment = (next_stop - current) / 100.0
        energy = battery_kwh * segment
        mins += (energy / max(rate, 0.1)) * 60.0
        current = next_stop
    return mins

def numeric_or_slider(label, min_value, max_value, value, step, key, ios_safe_mode):
    if ios_safe_mode:
        return st.number_input(label, min_value=min_value, max_value=max_value, value=value, step=step, key=key)
    return st.slider(label, min_value=min_value, max_value=max_value, value=value, step=step, key=key)

def provider_controls(label, key_prefix, car_max, ios_safe_mode):
    st.markdown(f"### {label}")
    provider_name = st.selectbox(f"{label} Provider", list(PROVIDER_PRESETS.keys()), key=f"{key_prefix}_name")
    preset = PROVIDER_PRESETS[provider_name]

    currency = st.selectbox(
        f"{label} Currency",
        ["GBP", "EUR", "USD"],
        index=["GBP", "EUR", "USD"].index(preset["currency"]) if preset["currency"] in ["GBP", "EUR", "USD"] else 0,
        key=f"{key_prefix}_currency",
    )

    station_kw = numeric_or_slider(
        f"{label} Charger Capacity (kW)",
        3, 400, min(400, int(preset["default_kw"])), 1, f"{key_prefix}_kw", ios_safe_mode
    )

    if preset["type"] == "home":
        home_pence = numeric_or_slider(
            f"{label} Home Tariff (p/kWh)",
            6, 30, max(6, min(30, int(round(preset["energy"] * 100)))), 1, f"{key_prefix}_home_pence", ios_safe_mode
        )
        energy_price = float(home_pence) / 100.0
        time_price = 0.0
        session_fee = 0.0
    else:
        energy_price = numeric_or_slider(
            f"{label} Energy Price ({currency}/kWh)",
            0.00, 1.50, float(preset["energy"]), 0.01, f"{key_prefix}_energy", ios_safe_mode
        )

        use_per_min = st.checkbox(
            f"{label} Include Per-Minute Charge",
            value=bool(preset["time"] > 0),
            key=f"{key_prefix}_use_per_min",
        )

        if use_per_min:
            time_price = numeric_or_slider(
                f"{label} Time Price ({currency}/min)",
                0.00, 1.00, float(max(preset["time"], 0.01)), 0.01, f"{key_prefix}_time", ios_safe_mode
            )
        else:
            time_price = 0.0

        session_fee = numeric_or_slider(
            f"{label} Session Fee ({currency})",
            0.00, 5.00, 0.00, 0.05, f"{key_prefix}_session", ios_safe_mode
        )

    effective_kw = min(float(station_kw), float(car_max))
    st.caption(f"Effective power: min({station_kw}kW station, {int(car_max)}kW car) = {effective_kw:.0f}kW")

    return {
        "provider": provider_name,
        "currency": currency,
        "station_kw": float(station_kw),
        "effective_kw": float(effective_kw),
        "energy_price": float(energy_price),
        "time_price": float(time_price),
        "session_fee": float(session_fee),
    }

st.markdown('<div class="top-banner"><strong>EV Charge Pro UK</strong></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
      <div class="hero-content">
        <h2 style="margin:0;">Charge Cost Comparison</h2>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Vehicle & Session")

mode_col1, _ = st.columns([1.8, 4])
with mode_col1:
    ios_safe_mode = st.toggle(
        "iOS Scroll Safe Inputs",
        value=True,
        help="Uses number inputs to reduce accidental slider changes while scrolling on iPhone."
    )

top1, top2, top3, top4 = st.columns([2.2, 1.1, 1.2, 1.2])

with top1:
    vehicle_name = st.selectbox("Vehicle", VEHICLES["model"].tolist(), index=7)

row = VEHICLES[VEHICLES["model"] == vehicle_name].iloc[0]
default_battery = float(row["battery_kwh"])
default_max = float(row["max_dc_kw"])

with top2:
    if vehicle_name == "Custom":
        battery_kwh = st.number_input("Battery (kWh)", min_value=10.0, max_value=220.0, value=80.0, step=0.5)
    else:
        battery_kwh = st.number_input("Battery (kWh)", min_value=10.0, max_value=220.0, value=default_battery, step=0.1)

with top3:
    car_max_kw = numeric_or_slider("Car Max DC (kW)", 20, 400, int(default_max), 1, "car_max_kw", ios_safe_mode)

with top4:
    comparison_currency = st.selectbox("Compare In", ["GBP", "EUR", "USD"], index=0)

bottom1, bottom2, bottom3 = st.columns([1.2, 1.2, 1.6])
with bottom1:
    start_pct = numeric_or_slider("Current Charge (%)", 0, 100, 20, 1, "start_pct", ios_safe_mode)
with bottom2:
    end_pct = numeric_or_slider("Target Charge (%)", 0, 100, 80, 1, "end_pct", ios_safe_mode)
with bottom3:
    efficiency_loss = numeric_or_slider("Charging Loss (%)", 0, 20, 6, 1, "eff_loss", ios_safe_mode)

taper = st.checkbox("Apply taper model (slowdown above 80/90%)", value=True)
miles_per_kwh = st.number_input("Miles per kWh", min_value=1.0, max_value=7.0, value=3.5, step=0.1)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.subheader("Compare Providers")

p1, p2 = st.columns(2)
with p1:
    provider_a = provider_controls("Provider A", "a", car_max_kw, ios_safe_mode)
with p2:
    provider_b = provider_controls("Provider B", "b", car_max_kw, ios_safe_mode)

run_compare = st.button("Compare Providers", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if run_compare:
    if end_pct <= start_pct:
        st.error("Target Charge must be greater than Current Charge.")
    else:
        energy_needed = battery_kwh * ((end_pct - start_pct) / 100.0)
        energy_needed *= (1.0 + efficiency_loss / 100.0)

        time_a = charging_time_minutes(battery_kwh, provider_a["effective_kw"], start_pct, end_pct, taper=taper)
        time_b = charging_time_minutes(battery_kwh, provider_b["effective_kw"], start_pct, end_pct, taper=taper)

        native_a = energy_needed * provider_a["energy_price"] + time_a * provider_a["time_price"] + provider_a["session_fee"]
        native_b = energy_needed * provider_b["energy_price"] + time_b * provider_b["time_price"] + provider_b["session_fee"]

        total_a = convert(native_a, provider_a["currency"], comparison_currency)
        total_b = convert(native_b, provider_b["currency"], comparison_currency)

        miles_added = energy_needed * miles_per_kwh
        per100_a = (total_a / miles_added * 100.0) if miles_added > 0 else 0.0
        per100_b = (total_b / miles_added * 100.0) if miles_added > 0 else 0.0

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Results")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Energy Added", f"{energy_needed:.2f} kWh")
        m2.metric("Miles Added", f"{miles_added:.1f} mi")
        m3.metric("Provider A Time", f"{time_a:.1f} min")
        m4.metric("Provider B Time", f"{time_b:.1f} min")

        r1, r2 = st.columns(2)
        r1.metric(provider_a["provider"], f"{total_a:.2f} {comparison_currency}", f"{per100_a:.2f} /100mi")
        r2.metric(provider_b["provider"], f"{total_b:.2f} {comparison_currency}", f"{per100_b:.2f} /100mi")

        detail_df = pd.DataFrame(
            [
                {
                    "Provider": provider_a["provider"],
                    "Station kW": provider_a["station_kw"],
                    "Car Max kW": car_max_kw,
                    "Effective kW": provider_a["effective_kw"],
                    "kWh price": provider_a["energy_price"],
                    "Per-min price": provider_a["time_price"],
                    "Session fee": provider_a["session_fee"],
                    f"Total ({comparison_currency})": round(total_a, 2),
                },
                {
                    "Provider": provider_b["provider"],
                    "Station kW": provider_b["station_kw"],
                    "Car Max kW": car_max_kw,
                    "Effective kW": provider_b["effective_kw"],
                    "kWh price": provider_b["energy_price"],
                    "Per-min price": provider_b["time_price"],
                    "Session fee": provider_b["session_fee"],
                    f"Total ({comparison_currency})": round(total_b, 2),
                },
            ]
        )
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

        pct_range = np.linspace(start_pct, 100, 24)
        curve_a, curve_b = [], []

        for pct in pct_range:
            e = battery_kwh * ((pct - start_pct) / 100.0)
            e *= (1.0 + efficiency_loss / 100.0)

            ta = charging_time_minutes(battery_kwh, provider_a["effective_kw"], start_pct, pct, taper=taper)
            tb = charging_time_minutes(battery_kwh, provider_b["effective_kw"], start_pct, pct, taper=taper)

            na = e * provider_a["energy_price"] + ta * provider_a["time_price"] + provider_a["session_fee"]
            nb = e * provider_b["energy_price"] + tb * provider_b["time_price"] + provider_b["session_fee"]

            curve_a.append(convert(na, provider_a["currency"], comparison_currency))
            curve_b.append(convert(nb, provider_b["currency"], comparison_currency))

        chart_df = pd.DataFrame(
            {
                "Charge %": pct_range,
                f"A: {provider_a['provider']}": curve_a,
                f"B: {provider_b['provider']}": curve_b,
            }
        )
        st.line_chart(chart_df.set_index("Charge %"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f'<p class="small-note">Live FX (Frankfurter/ECB): EUR→GBP {rates["GBP"]:.5f}, EUR→USD {rates["USD"]:.5f}, date {rates["_date"]}. Tariffs vary by site/time; verify before charging.</p>',
    unsafe_allow_html=True,
)
