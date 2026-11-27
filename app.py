import math
import os
import re
import numpy as np
import pandas as pd
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

NIGERIA_LOCATIONS = [
    ("FCT Abuja", "North Central", 42_000_000, 0.068, 0.055, "High"),
    ("Lagos", "South West", 65_000_000, 0.075, 0.062, "High"),
    ("Rivers", "South South", 34_000_000, 0.056, 0.058, "Medium"),
    ("Oyo", "South West", 22_000_000, 0.058, 0.056, "Medium"),
    ("Ogun", "South West", 20_000_000, 0.064, 0.054, "Medium"),
    ("Enugu", "South East", 24_000_000, 0.057, 0.055, "Medium"),
    ("Anambra", "South East", 25_000_000, 0.059, 0.055, "Medium"),
    ("Kano", "North West", 21_000_000, 0.054, 0.057, "Medium"),
    ("Kaduna", "North West", 18_500_000, 0.048, 0.056, "Medium"),
    ("Edo", "South South", 21_500_000, 0.055, 0.056, "Medium"),
    ("Delta", "South South", 22_000_000, 0.053, 0.057, "Medium"),
    ("Akwa Ibom", "South South", 19_000_000, 0.054, 0.056, "Medium"),
    ("Cross River", "South South", 17_500_000, 0.050, 0.055, "Baseline"),
    ("Abia", "South East", 18_000_000, 0.052, 0.056, "Baseline"),
    ("Imo", "South East", 19_500_000, 0.053, 0.056, "Baseline"),
    ("Ebonyi", "South East", 13_500_000, 0.047, 0.055, "Baseline"),
    ("Ondo", "South West", 15_000_000, 0.049, 0.055, "Baseline"),
    ("Osun", "South West", 14_500_000, 0.048, 0.054, "Baseline"),
    ("Ekiti", "South West", 13_000_000, 0.046, 0.054, "Baseline"),
    ("Kwara", "North Central", 16_000_000, 0.050, 0.055, "Baseline"),
    ("Plateau", "North Central", 16_500_000, 0.046, 0.055, "Baseline"),
    ("Niger", "North Central", 15_500_000, 0.052, 0.055, "Baseline"),
    ("Kogi", "North Central", 12_500_000, 0.044, 0.055, "Baseline"),
    ("Benue", "North Central", 13_000_000, 0.043, 0.055, "Baseline"),
    ("Nasarawa", "North Central", 17_000_000, 0.058, 0.055, "Medium"),
    ("Bauchi", "North East", 12_500_000, 0.045, 0.056, "Baseline"),
    ("Borno", "North East", 11_500_000, 0.040, 0.056, "Baseline"),
    ("Gombe", "North East", 12_000_000, 0.044, 0.055, "Baseline"),
    ("Taraba", "North East", 11_000_000, 0.042, 0.055, "Baseline"),
    ("Adamawa", "North East", 12_000_000, 0.043, 0.055, "Baseline"),
    ("Yobe", "North East", 10_500_000, 0.039, 0.056, "Baseline"),
    ("Sokoto", "North West", 13_000_000, 0.044, 0.056, "Baseline"),
    ("Zamfara", "North West", 11_000_000, 0.038, 0.056, "Baseline"),
    ("Kebbi", "North West", 11_500_000, 0.041, 0.056, "Baseline"),
    ("Jigawa", "North West", 11_000_000, 0.042, 0.056, "Baseline"),
    ("Katsina", "North West", 13_500_000, 0.045, 0.056, "Baseline"),
    ("Bayelsa", "South South", 15_000_000, 0.046, 0.056, "Baseline"),
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
    "drop": -0.022,
    "dropping": -0.022,
    "fall": -0.020,
    "falling": -0.020,
    "crash": -0.030,
    "decline": -0.018,
    "declining": -0.018,
    "low": -0.014,
    "lower": -0.014,
    "down": -0.014,
    "decrease": -0.016,
    "decreasing": -0.016,
    "oversupply": -0.018,
    "glut": -0.018,
    "flood": -0.022,
    "flooding": -0.022,
    "insecurity": -0.025,
    "unsafe": -0.022,
    "dilapidated": -0.018,
    "decay": -0.018,
    "stagnant": -0.012,
    "stagnation": -0.012,
    "slump": -0.020,
    "recession": -0.018,
    "abandon": -0.020,
    "abandoned": -0.020,
    "poor": -0.012,
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


@st.cache_data
def load_nationwide_properties() -> pd.DataFrame:
    base_rows = []
    property_types = [
        ("3-Bedroom Detached Bungalow", 3, 0.92, 1.03),
        ("4-Bedroom Semi-Detached Duplex", 4, 1.15, 1.00),
        ("5-Bedroom Fully Detached Duplex", 5, 1.45, 0.96),
        ("2-Bedroom Apartment / Flat", 2, 0.72, 1.08),
    ]

    for state_name, region, base_price, base_cagr, base_yield, coverage in NIGERIA_LOCATIONS:
        for p_type, beds, mult, yield_mult in property_types:
            fair_val = round(base_price * mult, -3)
            asking_val = round(fair_val * 0.96, -3)
            base_rows.append(
                {
                    "state": state_name,
                    "region": region,
                    "district": f"{state_name} Central / Growth Corridor",
                    "property_type": p_type,
                    "bedrooms": beds,
                    "asking_price": asking_val,
                    "fair_value": fair_val,
                    "annual_cagr": base_cagr,
                    "gross_yield": round(base_yield * yield_mult, 4),
                    "data_coverage": coverage,
                    "source_type": "Nationwide Baseline Model",
                }
            )

    df = pd.DataFrame(base_rows)

    # Merge existing CSV data if available in the repository
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

    # Check single words and bigrams
    for tok in tokens:
        if tok in POSITIVE_TERMS:
            text_rate_delta += POSITIVE_TERMS[tok]
            matched_factors.append(f"+{tok}")
        elif tok in NEGATIVE_TERMS:
            text_rate_delta += NEGATIVE_TERMS[tok]
            matched_factors.append(f"-{tok}")

    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i + 1]}"
        if "price drop" in bigram or "prices drop" in bigram or "price fall" in bigram or "go down" in bigram:
            text_rate_delta -= 0.020
            matched_factors.append(f"-{bigram}")
        elif "price rise" in bigram or "prices rise" in bigram or "go up" in bigram or "price high" in bigram:
            text_rate_delta += 0.018
            matched_factors.append(f"+{bigram}")

    # Bound the text adjustment so a single prompt does not produce unrealistic numbers
    text_rate_delta = max(-0.065, min(0.055, text_rate_delta))

    conservative_rate = max(-0.05, min(0.18, base_cagr + text_rate_delta - 0.015))
    base_rate = max(-0.04, min(0.20, base_cagr + text_rate_delta))
    optimistic_rate = max(-0.02, min(0.22, base_cagr + text_rate_delta + 0.015))

    conservative_price = starting_price * ((1.0 + conservative_rate) ** years)
    base_price = starting_price * ((1.0 + base_rate) ** years)
    optimistic_price = starting_price * ((1.0 + optimistic_rate) ** years)

    pct_change_base = ((base_price - starting_price) / starting_price) * 100.0 if starting_price > 0 else 0.0

    if base_rate > 0.005:
        direction = "HIGH (Price Expected to Rise)"
        signal_class = "signal-rise"
        summary = (
            f"Projected to rise from {format_naira(starting_price)} to "
            f"{format_naira(base_price)} ({pct_change_base:+.1f}%) by {target_year} "
            f"under the base estimate ({base_rate * 100:.1f}% annualized rate)."
        )
    elif base_rate < -0.005:
        direction = "DROP (Price Expected to Fall)"
        signal_class = "signal-drop"
        summary = (
            f"Projected to drop from {format_naira(starting_price)} to "
            f"{format_naira(base_price)} ({pct_change_base:+.1f}%) by {target_year} "
            f"under the base estimate ({base_rate * 100:.1f}% annualized rate)."
        )
    else:
        direction = "STEADY / FLAT"
        signal_class = "signal-neutral"
        summary = (
            f"Projected to stay near {format_naira(base_price)} ({pct_change_base:+.1f}%) "
            f"by {target_year} under the base estimate."
        )

    return {
        "years": years,
        "direction": direction,
        "signal_class": signal_class,
        "summary": summary,
        "base_rate": base_rate,
        "conservative_price": conservative_price,
        "base_price": base_price,
        "optimistic_price": optimistic_price,
        "pct_change_base": pct_change_base,
        "matched_factors": matched_factors,
    }


def answer_advisor_question(question: str, state_name: str, forecast_info: dict) -> str:
    q = (question or "").strip()
    if not q:
        return "Enter a question about state pricing, yields, or the 2060 projection."
    return (
        f"For {state_name} over {forecast_info['years']} years (to 2060 / selected target year), "
        f"the current scenario signal is {forecast_info['direction']} with a base estimate of "
        f"{format_naira(forecast_info['base_price'])} (conservative: {format_naira(forecast_info['conservative_price'])}, "
        f"optimistic: {format_naira(forecast_info['optimistic_price'])}). "
        f"Note that multi-decade figures are modeled estimates rather than guarantees."
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
        "Ask about state prices, yields, or 2060 scenarios",
        placeholder="Example: Compare 2060 growth vs. current fair value in this state.",
        height=90,
    )
    ask_clicked = st.button("Run Advisor", use_container_width=True)

# Header banner
st.markdown(
    """
    <div class="main-header">
        <h1>Nigeria Property Valuation &amp; Long-Term Forecast Advisor</h1>
        <p>Nationwide coverage across all 36 states and the FCT with valuation benchmarks, yield estimates, and forward price projections to 2060.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top valuation metrics for selected state and property
c1, c2, c3, c4 = st.columns(4)
spread_pct = ((prop_row["asking_price"] - prop_row["fair_value"]) / prop_row["fair_value"]) * 100.0

with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reference Asking Price</div>
            <div class="metric-value">{format_naira(prop_row['asking_price'])}</div>
            <div class="metric-sub">{selected_state} ({prop_row['region']})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Estimated Fair Value</div>
            <div class="metric-value">{format_naira(prop_row['fair_value'])}</div>
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
            <div class="metric-value">{prop_row['gross_yield'] * 100:.1f}%</div>
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
            <div class="metric-value">{prop_row['data_coverage']}</div>
            <div class="metric-sub">Source: {prop_row['source_type']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Interactive 2060 text-driven prediction section
st.markdown("### 2060 Price Direction & Scenario Estimator")
st.write(
    "Type a market note, location driver, or price assumption below to see whether the model projects the price to be HIGH (rise) or DROP by 2060."
)

col_input1, col_input2, col_input3 = st.columns([2.4, 1.1, 0.9])
with col_input1:
    user_thesis = st.text_input(
        "Type market conditions, area drivers, or what you expect to happen",
        value="New road and infrastructure expansion with steady urban demand, though inflation fluctuates",
        placeholder="Type anything here, e.g. major infrastructure and growth vs. flooding, insecurity, or oversupply...",
    )
with col_input2:
    starting_amount = st.number_input(
        "Starting Purchase Price (Naira)",
        min_value=500_000.0,
        max_value=5_000_000_000.0,
        value=float(prop_row["asking_price"]),
        step=1_000_000.0,
    )
with col_input3:
    target_year = st.number_input(
        "Target Forecast Year",
        min_value=2027,
        max_value=2100,
        value=2060,
        step=1,
    )

forecast = analyze_user_text_and_forecast(
    user_text=user_thesis,
    starting_price=starting_amount,
    base_cagr=float(prop_row["annual_cagr"]),
    target_year=int(target_year),
)

st.markdown(
    f"""
    <div class="{forecast['signal_class']}">
        <div>2060 / Target Year Outlook: {forecast['direction']}</div>
        <div style="font-weight: 400; margin-top: 4px;">{forecast['summary']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if forecast["matched_factors"]:
    st.caption(f"Detected text signals: {', '.join(forecast['matched_factors'])}")

f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(
        f"""
        <div class="metric-card" style="margin-top: 12px;">
            <div class="metric-label">Conservative Estimate ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['conservative_price'])}</div>
            <div class="metric-sub">Lower-bound scenario</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with f2:
    st.markdown(
        f"""
        <div class="metric-card" style="margin-top: 12px;">
            <div class="metric-label">Base Estimate ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['base_price'])}</div>
            <div class="metric-sub">Change: {forecast['pct_change_base']:+.1f}% over {forecast['years']} yrs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with f3:
    st.markdown(
        f"""
        <div class="metric-card" style="margin-top: 12px;">
            <div class="metric-label">Optimistic Estimate ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['optimistic_price'])}</div>
            <div class="metric-sub">Upper-bound scenario</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if ask_clicked:
    st.info(answer_advisor_question(advisor_prompt, selected_state, forecast))

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

summary_df["Projected 2060 (Base)"] = summary_df.apply(
    lambda r: analyze_user_text_and_forecast(
        user_thesis, float(r["asking_price"]), float(r["annual_cagr"]), int(target_year)
    )["base_price"],
    axis=1,
)
summary_df["2060 Outlook"] = summary_df.apply(
    lambda r: "HIGH"
    if analyze_user_text_and_forecast(
        user_thesis, float(r["asking_price"]), float(r["annual_cagr"]), int(target_year)
    )["base_rate"]
    > 0.005
    else "DROP",
    axis=1,
)

display_table = summary_df[
    ["state", "region", "asking_price", "fair_value", "Projected 2060 (Base)", "2060 Outlook", "data_coverage"]
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
        Forecasts through 2060 and beyond are scenario-based estimates driven by baseline state assumptions and user-entered text signals. They are modeled projections for planning and defense discussion, not financial guarantees.
    </div>
    """,
    unsafe_allow_html=True,
)