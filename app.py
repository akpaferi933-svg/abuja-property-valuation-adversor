import hashlib
import os
import re
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Nigeria Property Valuation & 2060 Forecast Advisor",
    layout="wide",
)

# Light blue and white styling (no emojis)
st.markdown(
    """
    <style>
        .stApp {
            background-color: #eef6ff;
            color: #0f2942;
        }
        [data-testid="stSidebar"] {
            background-color: #f7fbff;
            border-right: 1px solid #cfe3f7;
        }
        .main-header {
            background-color: #ffffff;
            border: 1px solid #cfe3f7;
            border-left: 6px solid #1d6fa5;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 18px;
        }
        .main-header h1 {
            margin: 0 0 6px 0;
            color: #0f2942;
            font-size: 1.85rem;
            font-weight: 700;
        }
        .main-header p {
            margin: 0;
            color: #3b5b78;
            font-size: 0.98rem;
        }
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #cfe3f7;
            border-radius: 10px;
            padding: 16px 18px;
            margin-bottom: 12px;
        }
        .metric-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #4a6b88;
            margin-bottom: 4px;
            font-weight: 600;
        }
        .metric-value {
            font-size: 1.45rem;
            font-weight: 700;
            color: #0f2942;
        }
        .metric-sub {
            font-size: 0.85rem;
            color: #3b5b78;
            margin-top: 4px;
        }
        .signal-rise {
            background-color: #e6f4ea;
            border: 1px solid #8ec5a0;
            color: #135329;
            border-radius: 8px;
            padding: 14px 18px;
            font-weight: 600;
        }
        .signal-drop {
            background-color: #fdecea;
            border: 1px solid #e69b93;
            color: #7a1c14;
            border-radius: 8px;
            padding: 14px 18px;
            font-weight: 600;
        }
        .signal-neutral {
            background-color: #f0f7ff;
            border: 1px solid #9ec5eb;
            color: #184975;
            border-radius: 8px;
            padding: 14px 18px;
            font-weight: 600;
        }
        .disclaimer-box {
            background-color: #f7fbff;
            border: 1px solid #cfe3f7;
            border-radius: 8px;
            padding: 12px 16px;
            color: #3b5b78;
            font-size: 0.86rem;
            margin-top: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# (State/FCT, Region, Base Price, Base CAGR, Base Gross Yield, Coverage, Lat, Lon)
NIGERIA_LOCATIONS = [
    ("FCT Abuja", "North Central", 42_000_000, 0.035, 0.055, "High", 9.0765, 7.3986),
    ("Lagos", "South West", 65_000_000, 0.040, 0.062, "High", 6.5244, 3.3792),
    ("Rivers", "South South", 34_000_000, 0.020, 0.058, "Medium", 4.8156, 7.0498),
    ("Oyo", "South West", 22_000_000, 0.025, 0.056, "Medium", 8.2151, 3.5643),
    ("Ogun", "South West", 20_000_000, 0.030, 0.054, "Medium", 6.9789, 3.4389),
    ("Enugu", "South East", 24_000_000, 0.022, 0.055, "Medium", 6.5244, 7.5086),
    ("Anambra", "South East", 25_000_000, 0.024, 0.055, "Medium", 6.2183, 6.9532),
    ("Kano", "North West", 21_000_000, 0.018, 0.057, "Medium", 12.0022, 8.5920),
    ("Kaduna", "North West", 18_500_000, 0.005, 0.056, "Medium", 10.5105, 7.4165),
    ("Edo", "South South", 21_500_000, 0.020, 0.056, "Medium", 6.6077, 5.9723),
    ("Delta", "South South", 22_000_000, 0.015, 0.057, "Medium", 5.5273, 6.1784),
    ("Akwa Ibom", "South South", 19_000_000, 0.020, 0.056, "Medium", 4.9409, 7.8412),
    ("Cross River", "South South", 17_500_000, 0.012, 0.055, "Baseline", 5.8672, 8.5205),
    ("Abia", "South East", 18_000_000, 0.015, 0.056, "Baseline", 5.4541, 7.5153),
    ("Imo", "South East", 19_500_000, 0.016, 0.056, "Baseline", 5.5720, 7.0588),
    ("Ebonyi", "South East", 13_500_000, 0.008, 0.055, "Baseline", 6.1997, 8.0349),
    ("Ondo", "South West", 15_000_000, 0.012, 0.055, "Baseline", 7.0210, 5.0567),
    ("Osun", "South West", 14_500_000, 0.010, 0.054, "Baseline", 7.5484, 4.4978),
    ("Ekiti", "South West", 13_000_000, 0.008, 0.054, "Baseline", 7.7369, 5.2738),
    ("Kwara", "North Central", 16_000_000, 0.014, 0.055, "Baseline", 8.8368, 4.6688),
    ("Plateau", "North Central", 16_500_000, 0.004, 0.055, "Baseline", 9.0583, 9.6826),
    ("Niger", "North Central", 15_500_000, 0.015, 0.055, "Baseline", 9.9326, 5.6511),
    ("Kogi", "North Central", 12_500_000, -0.004, 0.055, "Baseline", 7.7950, 6.6869),
    ("Benue", "North Central", 13_000_000, -0.006, 0.055, "Baseline", 7.3506, 8.7773),
    ("Nasarawa", "North Central", 17_000_000, 0.025, 0.055, "Medium", 8.4388, 8.2383),
    ("Bauchi", "North East", 12_500_000, 0.003, 0.056, "Baseline", 10.6371, 10.0807),
    ("Borno", "North East", 11_500_000, -0.010, 0.056, "Baseline", 11.8311, 13.1510),
    ("Gombe", "North East", 12_000_000, 0.004, 0.055, "Baseline", 10.2791, 11.1731),
    ("Taraba", "North East", 11_000_000, -0.005, 0.055, "Baseline", 8.0141, 10.7376),
    ("Adamawa", "North East", 12_000_000, -0.004, 0.055, "Baseline", 9.3265, 12.3984),
    ("Yobe", "North East", 10_500_000, -0.012, 0.056, "Baseline", 12.1233, 11.5066),
    ("Sokoto", "North West", 13_000_000, 0.002, 0.056, "Baseline", 13.0611, 5.3152),
    ("Zamfara", "North West", 11_000_000, -0.015, 0.056, "Baseline", 12.0079, 6.4191),
    ("Kebbi", "North West", 11_500_000, 0.000, 0.056, "Baseline", 11.4168, 4.1075),
    ("Jigawa", "North West", 11_000_000, 0.001, 0.056, "Baseline", 12.5631, 9.3800),
    ("Katsina", "North West", 13_500_000, 0.003, 0.056, "Baseline", 12.5631, 7.6207),
    ("Bayelsa", "South South", 15_000_000, 0.005, 0.056, "Baseline", 4.7630, 6.0289),
]

POSITIVE_TERMS = {
    "high": 0.015,
    "rise": 0.015,
    "rising": 0.015,
    "appreciate": 0.018,
    "appreciation": 0.018,
    "grow": 0.014,
    "growth": 0.014,
    "boom": 0.022,
    "demand": 0.012,
    "infrastructure": 0.016,
    "road": 0.010,
    "roads": 0.010,
    "rail": 0.015,
    "metro": 0.015,
    "airport": 0.014,
    "development": 0.013,
    "commercial": 0.012,
    "expansion": 0.012,
    "urban": 0.010,
    "renovated": 0.010,
    "prime": 0.014,
    "scarce": 0.012,
    "scarcity": 0.012,
    "up": 0.012,
    "increase": 0.014,
    "increasing": 0.014,
}

NEGATIVE_TERMS = {
    "drop": -0.025,
    "dropping": -0.025,
    "fall": -0.022,
    "falling": -0.022,
    "crash": -0.035,
    "decline": -0.020,
    "declining": -0.020,
    "low": -0.016,
    "lower": -0.016,
    "down": -0.018,
    "decrease": -0.018,
    "decreasing": -0.018,
    "oversupply": -0.020,
    "glut": -0.020,
    "flood": -0.025,
    "flooding": -0.025,
    "insecurity": -0.028,
    "unsafe": -0.025,
    "dilapidated": -0.020,
    "decay": -0.020,
    "stagnant": -0.015,
    "stagnation": -0.015,
    "slump": -0.022,
    "recession": -0.020,
    "abandon": -0.022,
    "abandoned": -0.022,
    "poor": -0.014,
}


def format_naira(amount: float) -> str:
    return f"N{amount:,.0f}"


def normalize_state_name(raw_value: str) -> str:
    if not isinstance(raw_value, str):
        return "FCT Abuja"
    cleaned = raw_value.strip().lower()
    if "abuja" in cleaned or "fct" in cleaned or "federal capital" in cleaned:
        return "FCT Abuja"
    for state_name, *_ in NIGERIA_LOCATIONS:
        if state_name.lower() in cleaned:
            return state_name
    return "FCT Abuja"


def get_place_coordinates(place_name: str, state_name: str) -> tuple[float, float]:
    meta = next(item for item in NIGERIA_LOCATIONS if item[0] == state_name)
    base_lat, base_lon = float(meta[6]), float(meta[7])
    clean_place = (place_name or "").strip().lower()
    if not clean_place:
        return base_lat, base_lon

    digest = hashlib.md5(f"{state_name}::{clean_place}".encode("utf-8")).hexdigest()
    lat_offset = ((int(digest[:8], 16) / 0xFFFFFFFF) - 0.5) * 0.24
    lon_offset = ((int(digest[8:16], 16) / 0xFFFFFFFF) - 0.5) * 0.24
    return round(base_lat + lat_offset, 5), round(base_lon + lon_offset, 5)


@st.cache_data
def load_nationwide_properties() -> pd.DataFrame:
    base_rows = []
    property_types = [
        ("3-Bedroom Detached Bungalow", 3, 0.92, 1.03),
        ("4-Bedroom Semi-Detached Duplex", 4, 1.15, 1.00),
        ("5-Bedroom Fully Detached Duplex", 5, 1.45, 0.96),
        ("2-Bedroom Apartment / Flat", 2, 0.72, 1.08),
    ]

    for state_name, region, base_price, base_cagr, base_yield, coverage, lat, lon in NIGERIA_LOCATIONS:
        for p_type, beds, mult, yield_mult in property_types:
            fair_val = round(base_price * mult, -3)
            asking_val = round(fair_val * 0.96, -3)
            base_rows.append(
                {
                    "state": state_name,
                    "region": region,
                    "district": f"{state_name} Central Corridor",
                    "property_type": p_type,
                    "bedrooms": beds,
                    "asking_price": asking_val,
                    "fair_value": fair_val,
                    "annual_cagr": base_cagr,
                    "gross_yield": round(base_yield * yield_mult, 4),
                    "data_coverage": coverage,
                    "source_type": "Nationwide Baseline Model",
                    "lat": lat,
                    "lon": lon,
                }
            )

    df = pd.DataFrame(base_rows)

    csv_candidates = [
        "abuja_rental_cleaned.csv",
        "nigeria_properties.csv",
        "properties.csv",
    ]
    for path in csv_candidates:
        if os.path.exists(path):
            try:
                ext = pd.read_csv(path)
                cols = {c.lower().strip(): c for c in ext.columns}
                price_col = next(
                    (cols[k] for k in ["price", "asking_price", "amount"] if k in cols),
                    None,
                )
                if price_col:
                    state_col = next(
                        (cols[k] for k in ["state", "city", "location"] if k in cols),
                        None,
                    )
                    area_col = next(
                        (
                            cols[k]
                            for k in ["neighborhood", "area", "district", "suburb", "title"]
                            if k in cols
                        ),
                        None,
                    )
                    bed_col = next(
                        (cols[k] for k in ["bedrooms", "beds", "bedroom"] if k in cols),
                        None,
                    )
                    type_col = next(
                        (cols[k] for k in ["property_type", "type", "category"] if k in cols),
                        None,
                    )

                    parsed_rows = []
                    for idx, r in ext.iterrows():
                        raw_price = pd.to_numeric(r[price_col], errors="coerce")
                        if pd.isna(raw_price) or raw_price <= 1_000_000:
                            continue
                        st_name = normalize_state_name(r[state_col]) if state_col else "FCT Abuja"
                        st_meta = next(item for item in NIGERIA_LOCATIONS if item[0] == st_name)
                        beds = int(pd.to_numeric(r[bed_col], errors="coerce")) if bed_col else 4
                        if beds <= 0 or beds > 12:
                            beds = 4
                        p_type = (
                            str(r[type_col]).strip()
                            if type_col and pd.notna(r[type_col])
                            else f"{beds}-Bedroom Residential Property"
                        )
                        district = (
                            str(r[area_col]).strip()[:60]
                            if area_col and pd.notna(r[area_col])
                            else f"{st_name} Listing #{idx + 1}"
                        )
                        fair_val = float(raw_price) * 1.05
                        parsed_rows.append(
                            {
                                "state": st_name,
                                "region": st_meta[1],
                                "district": district,
                                "property_type": p_type,
                                "bedrooms": beds,
                                "asking_price": float(raw_price),
                                "fair_value": fair_val,
                                "annual_cagr": st_meta[3],
                                "gross_yield": st_meta[4],
                                "data_coverage": "Observed + Baseline",
                                "source_type": os.path.basename(path),
                                "lat": float(st_meta[6]),
                                "lon": float(st_meta[7]),
                            }
                        )
                    if parsed_rows:
                        parsed_df = pd.DataFrame(parsed_rows)
                        df = pd.concat([parsed_df, df], ignore_index=True)
            except Exception:
                pass

    return df


def analyze_user_text_and_forecast(
    user_text: str,
    starting_price: float,
    base_cagr: float,
    target_year: int,
    current_year: int = 2026,
) -> dict:
    years = max(1, target_year - current_year)
    text_clean = (user_text or "").strip().lower()
    tokens = re.findall(r"[a-z0-9]+", text_clean)

    text_rate_delta = 0.0
    matched_factors = []

    for tok in tokens:
        if tok in POSITIVE_TERMS:
            text_rate_delta += POSITIVE_TERMS[tok]
            matched_factors.append(f"+{tok}")
        elif tok in NEGATIVE_TERMS:
            text_rate_delta += NEGATIVE_TERMS[tok]
            matched_factors.append(f"-{tok}")

    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i + 1]}"
        if any(p in bigram for p in ["price drop", "prices drop", "price fall", "go down", "will drop", "going drop"]):
            text_rate_delta -= 0.025
            matched_factors.append(f"-{bigram}")
        elif any(p in bigram for p in ["price rise", "prices rise", "go up", "price high", "will rise", "going high"]):
            text_rate_delta += 0.018
            matched_factors.append(f"+{bigram}")

    text_rate_delta = max(-0.075, min(0.060, text_rate_delta))

    conservative_rate = max(-0.06, min(0.18, base_cagr + text_rate_delta - 0.015))
    base_rate = max(-0.05, min(0.20, base_cagr + text_rate_delta))
    optimistic_rate = max(-0.03, min(0.22, base_cagr + text_rate_delta + 0.015))

    conservative_price = starting_price * ((1.0 + conservative_rate) ** years)
    base_price = starting_price * ((1.0 + base_rate) ** years)
    optimistic_price = starting_price * ((1.0 + optimistic_rate) ** years)

    pct_change_base = ((base_price - starting_price) / starting_price) * 100.0 if starting_price > 0 else 0.0

    if base_rate > 0.005:
        direction = "HIGH (Price Expected to Rise)"
        short_verdict = "HIGH"
        signal_class = "signal-rise"
        summary = (
            f"Projected to rise from {format_naira(starting_price)} to "
            f"{format_naira(base_price)} ({pct_change_base:+.1f}%) by {target_year} "
            f"under the base estimate ({base_rate * 100:.1f}% annualized rate)."
        )
    elif base_rate < -0.005:
        direction = "DROP (Price Expected to Fall)"
        short_verdict = "DROP"
        signal_class = "signal-drop"
        summary = (
            f"Projected to drop from {format_naira(starting_price)} to "
            f"{format_naira(base_price)} ({pct_change_base:+.1f}%) by {target_year} "
            f"under the base estimate ({base_rate * 100:.1f}% annualized rate)."
        )
    else:
        direction = "STEADY / FLAT"
        short_verdict = "STEADY"
        signal_class = "signal-neutral"
        summary = (
            f"Projected to stay near {format_naira(base_price)} ({pct_change_base:+.1f}%) "
            f"by {target_year} under the base estimate ({base_rate * 100:.1f}% annualized rate)."
        )

    return {
        "years": years,
        "direction": direction,
        "short_verdict": short_verdict,
        "signal_class": signal_class,
        "summary": summary,
        "base_rate": base_rate,
        "conservative_price": conservative_price,
        "base_price": base_price,
        "optimistic_price": optimistic_price,
        "pct_change_base": pct_change_base,
        "matched_factors": matched_factors,
    }


def answer_advisor_question(question: str, place_label: str, state_name: str, forecast_info: dict) -> str:
    q = (question or "").strip()
    if not q:
        return "Enter a question about location pricing, yields, or the 2060 projection."
    return (
        f"For {place_label} in {state_name} over {forecast_info['years']} years (to {2026 + forecast_info['years']}), "
        f"the projected direction is {forecast_info['direction']} with a base estimate of "
        f"{format_naira(forecast_info['base_price'])} (conservative: {format_naira(forecast_info['conservative_price'])}, "
        f"optimistic: {format_naira(forecast_info['optimistic_price'])}). "
        f"These figures are modeled estimates, not guarantees."
    )


df = load_nationwide_properties()

# Sidebar: State selection + Property Advisor
with st.sidebar:
    st.markdown("### Nationwide Controls")
    all_states = [s[0] for s in NIGERIA_LOCATIONS]
    selected_state = st.selectbox("State or FCT (All 36 + FCT)", all_states, index=0)

    state_df = df[df["state"] == selected_state].copy()
    property_options = state_df["property_type"].unique().tolist()
    selected_property = st.selectbox("Property Profile", property_options, index=0)

    prop_row = state_df[state_df["property_type"] == selected_property].iloc[0]

    st.markdown("---")
    st.markdown("### Property Advisor")
    advisor_prompt = st.text_area(
        "Ask about location prices, yields, or future scenarios",
        placeholder="Example: Will this area rise or drop in value by 2060?",
        height=90,
    )
    ask_clicked = st.button("Run Advisor", use_container_width=True)

# Header banner
st.markdown(
    """
    <div class="main-header">
        <h1>Nigeria Property Valuation &amp; Long-Term Forecast Advisor</h1>
        <p>Nationwide coverage across all 36 states and the FCT with red-dot location mapping, valuation benchmarks, and balanced HIGH/DROP price projections.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Location & forecast inputs (including place name + state for red dot map)
st.markdown("### Location Pin & Future Price Forecast")
loc_col1, loc_col2, loc_col3, loc_col4 = st.columns([1.4, 1.1, 1.2, 0.8])
with loc_col1:
    typed_place = st.text_input(
        "Type Place / Area / Estate Name",
        value="Lugbe",
        placeholder="Type a town, estate, or area name in the selected state",
    )
with loc_col2:
    chosen_state = st.selectbox(
        "Confirm State / FCT",
        all_states,
        index=all_states.index(selected_state),
    )
with loc_col3:
    starting_amount = st.number_input(
        "Starting Purchase Price (Naira)",
        min_value=500_000.0,
        max_value=5_000_000_000.0,
        value=float(prop_row["asking_price"]),
        step=1_000_000.0,
    )
with loc_col4:
    target_year = st.number_input(
        "Target Year",
        min_value=2027,
        max_value=2100,
        value=2060,
        step=1,
    )

user_thesis = st.text_input(
    "Type market factors or expectations (positive or negative)",
    value="Mixed market conditions with gradual growth and occasional price drops",
    placeholder="Example: major road expansion and demand vs. flooding, insecurity, or price drop",
)

active_state_row = df[(df["state"] == chosen_state) & (df["property_type"] == selected_property)].iloc[0]
pin_lat, pin_lon = get_place_coordinates(typed_place, chosen_state)
display_place_name = typed_place.strip() if typed_place.strip() else chosen_state

forecast = analyze_user_text_and_forecast(
    user_text=user_thesis,
    starting_price=starting_amount,
    base_cagr=float(active_state_row["annual_cagr"]),
    target_year=int(target_year),
)

# Direction banner (HIGH / DROP / STEADY)
st.markdown(
    f"""
    <div class="{forecast['signal_class']}">
        <div>{target_year} Direction for {display_place_name}, {chosen_state}: {forecast['direction']}</div>
        <div style="font-weight: 400; margin-top: 4px;">{forecast['summary']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if forecast["matched_factors"]:
    st.caption(f"Detected text signals: {', '.join(forecast['matched_factors'])}")

# Red dot map + future value summary side by side
map_col, info_col = st.columns([1.65, 1.0])

with map_col:
    st.markdown("#### Red Dot Location Map")
    pin_df = pd.DataFrame(
        [
            {
                "place": display_place_name,
                "state": chosen_state,
                "lat": pin_lat,
                "lon": pin_lon,
                "verdict": forecast["short_verdict"],
                "projected_price": format_naira(forecast["base_price"]),
            }
        ]
    )

    red_dot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color="[220, 38, 38, 225]",
        get_radius=14000,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=pin_lat,
        longitude=pin_lon,
        zoom=8.5,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[red_dot_layer],
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": "<b>Place:</b> {place}<br/><b>State:</b> {state}<br/><b>Direction:</b> {verdict}<br/><b>Projected Value:</b> {projected_price}",
            "style": {"backgroundColor": "#ffffff", "color": "#0f2942"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True, height=340)
    st.caption(f"Red dot pinned at {display_place_name}, {chosen_state} ({pin_lat}, {pin_lon}).")

with info_col:
    st.markdown("#### Future Price Breakdown")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Conservative ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['conservative_price'])}</div>
            <div class="metric-sub">Lower-bound estimate</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Base Estimate ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['base_price'])}</div>
            <div class="metric-sub">Net change: {forecast['pct_change_base']:+.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Optimistic ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['optimistic_price'])}</div>
            <div class="metric-sub">Upper-bound estimate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Top valuation metrics for selected state and property
c1, c2, c3, c4 = st.columns(4)
spread_pct = (
    (active_state_row["asking_price"] - active_state_row["fair_value"])
    / active_state_row["fair_value"]
) * 100.0

with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reference Asking Price</div>
            <div class="metric-value">{format_naira(active_state_row['asking_price'])}</div>
            <div class="metric-sub">{chosen_state} ({active_state_row['region']})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Estimated Fair Value</div>
            <div class="metric-value">{format_naira(active_state_row['fair_value'])}</div>
            <div class="metric-sub">Spread vs. Asking: {spread_pct:+.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Est. Gross Rental Yield</div>
            <div class="metric-value">{active_state_row['gross_yield'] * 100:.1f}%</div>
            <div class="metric-sub">Baseline annual benchmark</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Data Coverage Tier</div>
            <div class="metric-value">{active_state_row['data_coverage']}</div>
            <div class="metric-sub">Source: {active_state_row['source_type']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if ask_clicked:
    st.info(answer_advisor_question(advisor_prompt, display_place_name, chosen_state, forecast))

# Nationwide summary table across states
st.markdown("### Nationwide State & FCT Comparison")
region_filter = st.selectbox(
    "Filter Table by Region",
    ["All Regions", "North Central", "North East", "North West", "South East", "South South", "South West"],
    index=0,
)

summary_df = df[df["property_type"] == property_options[0]].copy()
if region_filter != "All Regions":
    summary_df = summary_df[summary_df["region"] == region_filter]

summary_df["Projected Value (Base)"] = summary_df.apply(
    lambda r: analyze_user_text_and_forecast(
        user_thesis, float(r["asking_price"]), float(r["annual_cagr"]), int(target_year)
    )["base_price"],
    axis=1,
)
summary_df["Direction"] = summary_df.apply(
    lambda r: analyze_user_text_and_forecast(
        user_thesis, float(r["asking_price"]), float(r["annual_cagr"]), int(target_year)
    )["short_verdict"],
    axis=1,
)

display_table = summary_df[
    ["state", "region", "asking_price", "fair_value", "Projected Value (Base)", "Direction", "data_coverage"]
].rename(
    columns={
        "state": "State / FCT",
        "region": "Region",
        "asking_price": "Reference Price (N)",
        "fair_value": "Est. Fair Value (N)",
        "data_coverage": "Coverage",
    }
)

st.dataframe(display_table, use_container_width=True, hide_index=True)

st.markdown(
    """
    <div class="disclaimer-box">
        Future prices and HIGH/DROP signals are scenario-based estimates derived from location baselines, user-entered factors, and holding horizons. They are modeled estimates for planning and defense discussion, not guarantees.
    </div>
    """,
    unsafe_allow_html=True,
)