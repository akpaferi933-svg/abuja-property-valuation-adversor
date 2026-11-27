import hashlib
import re
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Nigeria Property Valuation & Forecast Advisor",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f2f7f4;
            color: #0e241b;
        }
        [data-testid="stSidebar"] {
            background-color: #093b25;
            border-right: 1px solid #062819;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            color: #eefaf3 !important;
        }
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background-color: #ffffff !important;
            color: #0e241b !important;
        }
        .sidebar-brand {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }
        .sidebar-brand-title {
            font-size: 1.02rem;
            font-weight: 700;
            line-height: 1.25;
            color: #ffffff;
            margin: 0;
        }
        .sidebar-brand-sub {
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #9ae6b4;
            margin-top: 6px;
        }
        .hero-banner {
            background: linear-gradient(120deg, #083823 0%, #116640 65%, #198754 100%);
            color: #ffffff;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 14px;
        }
        .hero-banner h1 {
            margin: 0 0 4px 0;
            font-size: 1.65rem;
            font-weight: 700;
            color: #ffffff;
        }
        .hero-banner p {
            margin: 0;
            font-size: 0.92rem;
            color: #d8f4e5;
        }
        .card-panel {
            background-color: #ffffff;
            border: 1px solid #d6e4dc;
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 14px;
        }
        .card-panel h4 {
            margin: 0 0 10px 0;
            color: #0e241b;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .kpi-card {
            background-color: #ffffff;
            border: 1px solid #d6e4dc;
            border-top: 3px solid #16a34a;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }
        .kpi-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #4f685d;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 1.38rem;
            font-weight: 700;
            color: #0e241b;
        }
        .kpi-sub {
            font-size: 0.8rem;
            font-weight: 600;
            color: #15803d;
            margin-top: 4px;
        }
        .kpi-sub-muted {
            font-size: 0.8rem;
            color: #5b7369;
            margin-top: 4px;
        }
        .signal-rise {
            background-color: #e6f6ec;
            border: 1px solid #86efac;
            color: #14532d;
            border-radius: 10px;
            padding: 12px 16px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .signal-drop {
            background-color: #fef2f2;
            border: 1px solid #fca5a5;
            color: #7f1d1d;
            border-radius: 10px;
            padding: 12px 16px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .signal-steady {
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            border-radius: 10px;
            padding: 12px 16px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .rank-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 4px;
            border-bottom: 1px solid #edf3ef;
            font-size: 0.88rem;
        }
        .rank-row:last-child {
            border-bottom: none;
        }
        .feature-card {
            background-color: #ffffff;
            border: 1px solid #d6e4dc;
            border-top: 3px solid #16a34a;
            border-radius: 10px;
            padding: 12px 14px;
            height: 100%;
        }
        .feature-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: #0e241b;
            margin-bottom: 4px;
        }
        .feature-desc {
            font-size: 0.78rem;
            color: #556d63;
            line-height: 1.35;
        }
        .disclaimer-box {
            background-color: #ffffff;
            border: 1px solid #d6e4dc;
            border-radius: 10px;
            padding: 12px 16px;
            color: #4f685d;
            font-size: 0.84rem;
            margin-top: 12px;
        }
        div.stButton > button {
            background-color: #16a34a;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }
        div.stButton > button:hover {
            background-color: #15803d;
            color: #ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# (State/FCT, Region, Mid-City Reference Price, Base CAGR, Base Gross Yield, Coverage, Lat, Lon, Market Note)
NIGERIA_LOCATIONS = [
    ("FCT Abuja", "North Central", 180_000_000, 0.042, 0.055, "High", 9.0765, 7.3986, "prime urban demand and infrastructure expansion"),
    ("Lagos", "South West", 220_000_000, 0.045, 0.062, "High", 6.5244, 3.3792, "prime land scarcity and strong urban demand"),
    ("Rivers", "South South", 85_000_000, 0.025, 0.058, "Medium", 4.8156, 7.0498, "commercial activity with moderate growth"),
    ("Oyo", "South West", 55_000_000, 0.028, 0.056, "Medium", 8.2151, 3.5643, "steady urban expansion and residential demand"),
    ("Ogun", "South West", 48_000_000, 0.032, 0.054, "Medium", 6.9789, 3.4389, "urban spillover and road development"),
    ("Enugu", "South East", 65_000_000, 0.026, 0.055, "Medium", 6.5244, 7.5086, "steady city demand and commercial growth"),
    ("Anambra", "South East", 68_000_000, 0.027, 0.055, "Medium", 6.2183, 6.9532, "active commercial trade and urban demand"),
    ("Kano", "North West", 60_000_000, 0.022, 0.057, "Medium", 12.0022, 8.5920, "regional commercial hub with gradual growth"),
    ("Kaduna", "North West", 48_000_000, 0.010, 0.056, "Medium", 10.5105, 7.4165, "mixed market momentum and security sensitivity"),
    ("Edo", "South South", 55_000_000, 0.024, 0.056, "Medium", 6.6077, 5.9723, "steady urban development and residential demand"),
    ("Delta", "South South", 58_000_000, 0.020, 0.057, "Medium", 5.5273, 6.1784, "moderate commercial and residential activity"),
    ("Akwa Ibom", "South South", 52_000_000, 0.023, 0.056, "Medium", 4.9409, 7.8412, "infrastructure growth and steady demand"),
    ("Cross River", "South South", 42_000_000, 0.016, 0.055, "Baseline", 5.8672, 8.5205, "gradual growth and tourism/commercial baseline"),
    ("Abia", "South East", 46_000_000, 0.018, 0.056, "Baseline", 5.4541, 7.5153, "commercial activity with gradual appreciation"),
    ("Imo", "South East", 50_000_000, 0.020, 0.056, "Baseline", 5.5720, 7.0588, "steady urban demand in city centers"),
    ("Ebonyi", "South East", 32_000_000, 0.014, 0.055, "Baseline", 6.1997, 8.0349, "gradual expansion in developing corridors"),
    ("Ondo", "South West", 38_000_000, 0.016, 0.055, "Baseline", 7.0210, 5.0567, "moderate local demand and gradual growth"),
    ("Osun", "South West", 35_000_000, 0.015, 0.054, "Baseline", 7.5484, 4.4978, "steady town demand with moderate growth"),
    ("Ekiti", "South West", 30_000_000, 0.013, 0.054, "Baseline", 7.7369, 5.2738, "gradual appreciation in core town areas"),
    ("Kwara", "North Central", 40_000_000, 0.018, 0.055, "Baseline", 8.8368, 4.6688, "steady residential demand and moderate growth"),
    ("Plateau", "North Central", 42_000_000, 0.010, 0.055, "Baseline", 9.0583, 9.6826, "mixed conditions and cautious growth"),
    ("Niger", "North Central", 38_000_000, 0.018, 0.055, "Baseline", 9.9326, 5.6511, "regional spillover and gradual growth"),
    ("Kogi", "North Central", 28_000_000, -0.004, 0.055, "Baseline", 7.7950, 6.6869, "slow market demand and price drop pressure"),
    ("Benue", "North Central", 30_000_000, -0.005, 0.055, "Baseline", 7.3506, 8.7773, "weak market momentum and price drop pressure"),
    ("Nasarawa", "North Central", 45_000_000, 0.028, 0.055, "Medium", 8.4388, 8.2383, "urban spillover and road development"),
    ("Bauchi", "North East", 28_000_000, 0.008, 0.056, "Baseline", 10.6371, 10.0807, "slow to moderate growth in core town"),
    ("Borno", "North East", 25_000_000, -0.010, 0.056, "Baseline", 11.8311, 13.1510, "insecurity and sluggish market demand"),
    ("Gombe", "North East", 27_000_000, 0.009, 0.055, "Baseline", 10.2791, 11.1731, "gradual town growth with low turnover"),
    ("Taraba", "North East", 24_000_000, -0.005, 0.055, "Baseline", 8.0141, 10.7376, "slow market demand and price drop pressure"),
    ("Adamawa", "North East", 26_000_000, -0.004, 0.055, "Baseline", 9.3265, 12.3984, "sluggish demand and downward pressure"),
    ("Yobe", "North East", 22_000_000, -0.012, 0.056, "Baseline", 12.1233, 11.5066, "weak demand and price drop pressure"),
    ("Sokoto", "North West", 30_000_000, 0.006, 0.056, "Baseline", 13.0611, 5.3152, "slow growth and limited high-value demand"),
    ("Zamfara", "North West", 22_000_000, -0.015, 0.056, "Baseline", 12.0079, 6.4191, "insecurity and price drop pressure"),
    ("Kebbi", "North West", 24_000_000, 0.004, 0.056, "Baseline", 11.4168, 4.1075, "gradual baseline growth with slow turnover"),
    ("Jigawa", "North West", 23_000_000, 0.005, 0.056, "Baseline", 12.5631, 9.3800, "slow baseline appreciation"),
    ("Katsina", "North West", 30_000_000, 0.007, 0.056, "Baseline", 12.5631, 7.6207, "slow to moderate market activity"),
    ("Bayelsa", "South South", 36_000_000, 0.010, 0.056, "Baseline", 4.7630, 6.0289, "moderate baseline growth with terrain constraints"),
]

COMMUNITY_TIERS = {
    "Prime City Core": {"price_mult": 2.40, "cagr_bonus": 0.008, "desc": "Highest prices, strong prime demand"},
    "Urban Core": {"price_mult": 1.35, "cagr_bonus": 0.003, "desc": "High activity, steady urban growth"},
    "Secondary / Suburban": {"price_mult": 1.00, "cagr_bonus": 0.000, "desc": "Moderate prices, progressive growth"},
    "Emerging": {"price_mult": 0.42, "cagr_bonus": 0.004, "desc": "Lower entry prices, expansion potential"},
}

KNOWN_AREAS = {
    "asokoro": ("FCT Abuja", 820_000_000, 0.048, 9.0479, 7.5155, "Prime City Core"),
    "maitama": ("FCT Abuja", 950_000_000, 0.048, 9.0882, 7.4934, "Prime City Core"),
    "wuse 2": ("FCT Abuja", 650_000_000, 0.045, 9.0787, 7.4793, "Prime City Core"),
    "wuse": ("FCT Abuja", 520_000_000, 0.044, 9.0765, 7.4700, "Urban Core"),
    "guzape": ("FCT Abuja", 580_000_000, 0.047, 9.0160, 7.5140, "Prime City Core"),
    "gwarinpa": ("FCT Abuja", 210_000_000, 0.042, 9.1099, 7.4042, "Urban Core"),
    "lugbe": ("FCT Abuja", 75_000_000, 0.043, 8.9868, 7.3626, "Emerging"),
    "kubwa": ("FCT Abuja", 85_000_000, 0.041, 9.1538, 7.3220, "Secondary / Suburban"),
    "banana island": ("Lagos", 2_500_000_000, 0.052, 6.4650, 3.4510, "Prime City Core"),
    "ikoyi": ("Lagos", 1_200_000_000, 0.050, 6.4549, 3.4346, "Prime City Core"),
    "victoria island": ("Lagos", 950_000_000, 0.048, 6.4281, 3.4219, "Prime City Core"),
    "lekki": ("Lagos", 340_000_000, 0.046, 6.4698, 3.5852, "Urban Core"),
    "ikeja": ("Lagos", 360_000_000, 0.044, 6.6018, 3.3515, "Urban Core"),
    "epe": ("Lagos", 45_000_000, 0.046, 6.5841, 3.9834, "Emerging"),
    "old gra": ("Rivers", 230_000_000, 0.030, 4.7890, 7.0120, "Prime City Core"),
    "gra phase 2": ("Rivers", 210_000_000, 0.030, 4.8242, 7.0036, "Prime City Core"),
    "bodija": ("Oyo", 140_000_000, 0.032, 7.4200, 3.9100, "Urban Core"),
    "independence layout": ("Enugu", 150_000_000, 0.030, 6.4402, 7.5250, "Urban Core"),
}

PROPERTY_MULTIPLIERS = {
    "Detached House": 1.25,
    "Standard Residential Plot (500-600 sqm)": 1.00,
    "4-Bedroom Semi-Detached Duplex": 1.15,
    "5-Bedroom Fully Detached Duplex": 1.55,
    "3-Bedroom Detached Bungalow": 0.85,
}

POSITIVE_TERMS = {
    "high": 0.014, "rise": 0.014, "rising": 0.014, "appreciate": 0.016,
    "appreciation": 0.016, "grow": 0.013, "growth": 0.013, "boom": 0.020,
    "demand": 0.012, "infrastructure": 0.015, "road": 0.010, "roads": 0.010,
    "development": 0.012, "commercial": 0.012, "expansion": 0.012,
    "urban": 0.010, "prime": 0.014, "scarcity": 0.012, "increase": 0.013,
}

NEGATIVE_TERMS = {
    "drop": -0.026, "dropping": -0.026, "fall": -0.022, "falling": -0.022,
    "crash": -0.035, "decline": -0.020, "declining": -0.020, "low": -0.016,
    "down": -0.018, "decrease": -0.018, "flood": -0.025, "flooding": -0.025,
    "insecurity": -0.028, "unsafe": -0.025, "stagnant": -0.015, "slump": -0.022,
}


def format_naira(amount: float) -> str:
    return f"N{amount:,.0f}"


def resolve_location_profile(place_name: str, state_name: str, tier_name: str, property_type: str) -> dict:
    clean_place = (place_name or "").strip().lower()
    state_meta = next(item for item in NIGERIA_LOCATIONS if item[0] == state_name)
    tier_meta = COMMUNITY_TIERS[tier_name]
    prop_mult = PROPERTY_MULTIPLIERS.get(property_type, 1.0)

    matched = None
    for key, val in KNOWN_AREAS.items():
        if key in clean_place and val[0] == state_name:
            matched = val
            break

    if matched:
        _, area_price, area_cagr, lat, lon, resolved_tier = matched
        auto_price = round(area_price * prop_mult, -5)
        effective_cagr = area_cagr
    else:
        auto_price = round(state_meta[2] * tier_meta["price_mult"] * prop_mult, -5)
        effective_cagr = state_meta[3] + tier_meta["cagr_bonus"]
        resolved_tier = tier_name
        base_lat, base_lon = float(state_meta[6]), float(state_meta[7])
        if clean_place:
            digest = hashlib.md5(f"{state_name}::{clean_place}".encode("utf-8")).hexdigest()
            lat = round(base_lat + (((int(digest[:8], 16) / 0xFFFFFFFF) - 0.5) * 0.22), 5)
            lon = round(base_lon + (((int(digest[8:16], 16) / 0xFFFFFFFF) - 0.5) * 0.22), 5)
        else:
            lat, lon = base_lat, base_lon

    return {
        "automatic_price": float(max(2_000_000, auto_price)),
        "effective_cagr": effective_cagr,
        "tier": resolved_tier,
        "region": state_meta[1],
        "gross_yield": state_meta[4],
        "coverage": state_meta[5],
        "lat": lat,
        "lon": lon,
        "market_note": state_meta[8],
    }


def compute_forecast(
    market_text: str,
    automatic_price: float,
    base_cagr: float,
    target_year: int,
    current_year: int = 2026,
    realistic_ceiling: float = 10_000_000_000.0,
) -> dict:
    years = max(1, target_year - current_year)
    tokens = re.findall(r"[a-z0-9]+", (market_text or "").strip().lower())
    delta = 0.0
    for tok in tokens:
        if tok in POSITIVE_TERMS:
            delta += POSITIVE_TERMS[tok]
        elif tok in NEGATIVE_TERMS:
            delta += NEGATIVE_TERMS[tok]
    delta = max(-0.080, min(0.060, delta))

    c_rate = max(-0.06, min(0.16, base_cagr + delta - 0.012))
    b_rate = max(-0.05, min(0.18, base_cagr + delta))
    o_rate = max(-0.03, min(0.20, base_cagr + delta + 0.012))

    c_price = automatic_price * ((1.0 + c_rate) ** years)
    b_price = automatic_price * ((1.0 + b_rate) ** years)
    o_price = automatic_price * ((1.0 + o_rate) ** years)

    pct_change = ((b_price - automatic_price) / automatic_price) * 100.0 if automatic_price else 0.0
    exceeds_cap = b_price >= realistic_ceiling

    if b_rate > 0.005:
        verdict = "HIGH"
        direction_text = "HIGH (Price Expected to Rise)"
        signal_cls = "signal-rise"
    elif b_rate < -0.005:
        verdict = "DROP"
        direction_text = "DROP (Price Expected to Fall)"
        signal_cls = "signal-drop"
    else:
        verdict = "STEADY"
        direction_text = "STEADY / FLAT"
        signal_cls = "signal-steady"

    series_rows = []
    for yr in range(current_year, target_year + 1):
        dt = yr - current_year
        series_rows.append(
            {
                "Year": yr,
                "Conservative": round(automatic_price * ((1.0 + c_rate) ** dt), 0),
                "Base Estimate": round(automatic_price * ((1.0 + b_rate) ** dt), 0),
                "Optimistic": round(automatic_price * ((1.0 + o_rate) ** dt), 0),
            }
        )

    return {
        "years": years,
        "verdict": verdict,
        "direction_text": direction_text,
        "signal_cls": signal_cls,
        "base_rate": b_rate,
        "conservative_price": c_price,
        "base_price": b_price,
        "optimistic_price": o_price,
        "pct_change": pct_change,
        "exceeds_cap": exceeds_cap,
        "series_df": pd.DataFrame(series_rows).set_index("Year"),
    }


def render_map(place_label: str, state_name: str, profile: dict, forecast: dict, auto_price: float, height: int = 360):
    state_bubbles = [
        {
            "place": st_name,
            "state": st_name,
            "tier": reg,
            "lat": s_lat,
            "lon": s_lon,
            "verdict": "HIGH" if b_cagr > 0.005 else ("DROP" if b_cagr < -0.005 else "STEADY"),
            "auto_price": format_naira(b_price),
            "projected_price": format_naira(b_price * ((1 + b_cagr) ** forecast["years"])),
        }
        for st_name, reg, b_price, b_cagr, _, _, s_lat, s_lon, _ in NIGERIA_LOCATIONS
    ]
    all_states_df = pd.DataFrame(state_bubbles)

    pin_df = pd.DataFrame(
        [
            {
                "place": place_label,
                "state": state_name,
                "tier": profile["tier"],
                "lat": profile["lat"],
                "lon": profile["lon"],
                "verdict": forecast["verdict"],
                "auto_price": format_naira(auto_price),
                "projected_price": format_naira(forecast["base_price"]),
            }
        ]
    )

    regional_green_layer = pdk.Layer(
        "ScatterplotLayer",
        data=all_states_df,
        get_position="[lon, lat]",
        get_color="[22, 163, 74, 52]",
        get_radius=45000,
        radius_min_pixels=10,
        radius_max_pixels=26,
        pickable=True,
    )
    outer_ring = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color="[220, 38, 38, 70]",
        get_radius=42000,
        radius_min_pixels=26,
        radius_max_pixels=68,
        pickable=False,
    )
    red_dot = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color="[220, 38, 38, 245]",
        get_radius=22000,
        radius_min_pixels=15,
        radius_max_pixels=38,
        stroked=True,
        get_line_color="[255, 255, 255, 255]",
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
    )
    core_color = [255, 0, 45, 255] if forecast["exceeds_cap"] else [153, 27, 27, 255]
    center_core = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color=core_color,
        get_radius=9000,
        radius_min_pixels=6,
        radius_max_pixels=15,
        stroked=True,
        get_line_color="[255, 255, 255, 255]",
        line_width_min_pixels=1.5,
        pickable=False,
    )
    view_state = pdk.ViewState(latitude=profile["lat"], longitude=profile["lon"], zoom=6.2, pitch=0)
    deck = pdk.Deck(
        layers=[regional_green_layer, outer_ring, red_dot, center_core],
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": (
                "<b>Location:</b> {place} ({tier})<br/>"
                "<b>State:</b> {state}<br/>"
                "<b>Current Price (Auto):</b> {auto_price}<br/>"
                "<b>Direction:</b> {verdict}<br/>"
                "<b>Projected:</b> {projected_price}"
            ),
            "style": {"backgroundColor": "#ffffff", "color": "#0e241b"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True, height=height)


all_states = [s[0] for s in NIGERIA_LOCATIONS]
tier_names = list(COMMUNITY_TIERS.keys())
prop_names = list(PROPERTY_MULTIPLIERS.keys())

if "state_choice" not in st.session_state:
    st.session_state["state_choice"] = "FCT Abuja"
if "area_choice" not in st.session_state:
    st.session_state["area_choice"] = "Asokoro"
if "prop_choice" not in st.session_state:
    st.session_state["prop_choice"] = prop_names[0]
if "tier_choice" not in st.session_state:
    st.session_state["tier_choice"] = tier_names[0]
if "year_choice" not in st.session_state:
    st.session_state["year_choice"] = 2040
if "saved_analyses" not in st.session_state:
    st.session_state["saved_analyses"] = []
if "moderator_log" not in st.session_state:
    st.session_state["moderator_log"] = []

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Nigeria Property Valuation &amp; Forecast Advisor</div>
            <div class="sidebar-brand-sub">Property Intelligence Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nav_section = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Estimate Property",
            "Forecast Value",
            "Location Map",
            "Compare Locations",
            "Saved Analysis",
        ],
        index=0,
    )

st.markdown(
    """
    <div class="hero-banner">
        <h1>Nigeria Property Valuation &amp; Forecast Advisor</h1>
        <p>Estimate. Forecast. Invest Smarter — Automatic current prices, multi-year future forecasts, and market intelligence across all 36 states and the FCT.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="card-panel"><h4>Quick Property Estimate &amp; Future Forecast</h4>', unsafe_allow_html=True)
q1, q2, q3, q4, q5 = st.columns([1.1, 1.1, 1.25, 1.0, 0.75])
with q1:
    selected_state = st.selectbox("State / FCT", all_states, key="state_choice")
with q2:
    typed_area = st.text_input("Area / Community", key="area_choice")
with q3:
    selected_prop = st.selectbox("Property Type", prop_names, key="prop_choice")
with q4:
    selected_tier = st.selectbox("Market Tier", tier_names, key="tier_choice")
with q5:
    target_year = st.number_input("Forecast Year", min_value=2027, max_value=2100, step=1, key="year_choice")
st.markdown("</div>", unsafe_allow_html=True)

profile = resolve_location_profile(typed_area, selected_state, selected_tier, selected_prop)
auto_price = profile["automatic_price"]
place_label = typed_area.strip() if typed_area.strip() else selected_state
forecast = compute_forecast(profile["market_note"], auto_price, profile["effective_cagr"], int(target_year))

snapshot_key = (
    f"{place_label}|{selected_state}|{profile['tier']}|{selected_prop}|"
    f"{int(target_year)}|{round(auto_price, 0)}|{round(forecast['base_price'], 0)}|{forecast['verdict']}"
)
if st.session_state.get("last_snapshot_key") != snapshot_key:
    prev_val = st.session_state.get("last_base_price")
    if prev_val is not None and prev_val > 0:
        shift_pct = ((forecast["base_price"] - prev_val) / prev_val) * 100.0
        if shift_pct > 0.5:
            market_change = f"SHIFT UP ({shift_pct:+.1f}%)"
        elif shift_pct < -0.5:
            market_change = f"SHIFT DOWN ({shift_pct:+.1f}%)"
        else:
            market_change = "STEADY (0.0%)"
    else:
        market_change = f"ACTIVE ({forecast['verdict']})"

    st.session_state["last_snapshot_key"] = snapshot_key
    st.session_state["last_base_price"] = forecast["base_price"]
    st.session_state["moderator_log"].insert(
        0,
        {
            "Location": f"{place_label}, {selected_state}",
            "Tier": profile["tier"],
            "Property": selected_prop,
            "Target Year": int(target_year),
            "Auto Price Today": format_naira(auto_price),
            f"Projected {target_year}": format_naira(forecast["base_price"]),
            "Direction": forecast["verdict"],
            "Market Change": market_change,
        },
    )
    st.session_state["moderator_log"] = st.session_state["moderator_log"][:25]

st.markdown(
    f"""
    <div class="{forecast['signal_cls']}">
        {target_year} Direction for {place_label}, {selected_state} ({profile['tier']}): {forecast['direction_text']} —
        Automatic Price Today: {format_naira(auto_price)} to {format_naira(forecast['base_price'])} ({forecast['pct_change']:+.1f}%).
    </div>
    """,
    unsafe_allow_html=True,
)

if forecast["exceeds_cap"]:
    st.markdown(
        f"""
        <div class="signal-drop">
            Overstretched {target_year} Target Alert: {format_naira(forecast['base_price'])} exceeds the N10,000,000,000 reachability cap for {place_label} by {target_year}.
        </div>
        """,
        unsafe_allow_html=True,
    )

if nav_section == "Dashboard":
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Average Price ({profile['tier']})</div>
                <div class="kpi-value">{format_naira(auto_price)}</div>
                <div class="kpi-sub">{forecast['base_rate'] * 100:+.1f}% annualized rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Est. Rental Yield</div>
                <div class="kpi-value">{profile['gross_yield'] * 100:.1f}%</div>
                <div class="kpi-sub-muted">Annual yield benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Market Tier &amp; Coverage</div>
                <div class="kpi-value">{profile['coverage']}</div>
                <div class="kpi-sub-muted">36 States + FCT</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Top Growth / Horizon</div>
                <div class="kpi-value">{place_label} ({target_year})</div>
                <div class="kpi-sub">{forecast['verdict']} signal ({forecast['years']} yrs)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left_col, right_col = st.columns([1.2, 1.0])
    with left_col:
        st.markdown('<div class="card-panel"><h4>Nigeria Property Price Trend &amp; Forecast</h4>', unsafe_allow_html=True)
        st.line_chart(forecast["series_df"], height=260)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card-panel"><h4>Top Growth Locations (YoY Benchmark)</h4>', unsafe_allow_html=True)
        top_locs = sorted(NIGERIA_LOCATIONS, key=lambda x: x[3], reverse=True)[:5]
        for st_name, reg, b_price, b_cagr, *_ in top_locs:
            st.markdown(
                f"""
                <div class="rank-row">
                    <span><b>{st_name}</b> ({reg}) — {format_naira(b_price)}</span>
                    <span style="color:#15803d; font-weight:700;">{b_cagr * 100:+.1f}%/yr</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown(f'<div class="card-panel"><h4>Price by Location — {place_label}, {selected_state}</h4>', unsafe_allow_html=True)
        render_map(place_label, selected_state, profile, forecast, auto_price, height=390)
        st.caption(f"Current (Auto): {format_naira(auto_price)} | {target_year} Base: {format_naira(forecast['base_price'])} | Signal: {forecast['verdict']}")
        if st.button("Save Current Analysis", use_container_width=True):
            st.session_state["saved_analyses"].append(
                {
                    "Location": f"{place_label}, {selected_state}",
                    "Tier": profile["tier"],
                    "Property Type": selected_prop,
                    "Current Price (Auto)": auto_price,
                    "Target Year": target_year,
                    "Projected Base": round(forecast["base_price"], -5),
                    "Direction": forecast["verdict"],
                }
            )
            st.success(f"Saved {place_label}, {selected_state} ({target_year}) to Saved Analysis.")
        st.markdown("</div>", unsafe_allow_html=True)

elif nav_section == "Estimate Property":
    st.markdown('<div class="card-panel"><h4>Property Price Estimate</h4>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    with e1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Estimated Property Value (Current)</div>
                <div class="kpi-value">{format_naira(auto_price)}</div>
                <div class="kpi-sub">{profile['tier']} - {place_label}, {selected_state}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with e2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Est. Rental Yield</div>
                <div class="kpi-value">{profile['gross_yield'] * 100:.1f}%</div>
                <div class="kpi-sub-muted">{selected_prop}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with e3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Confidence Level</div>
                <div class="kpi-value">{profile['coverage']}</div>
                <div class="kpi-sub-muted">{profile['region']} Region</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption(f"Automatic market profile: {profile['market_note']}")
    st.markdown("</div>", unsafe_allow_html=True)

elif nav_section == "Forecast Value":
    scenario_choice = st.selectbox("Select Highlighted Scenario", ["Base Estimate", "Optimistic", "Conservative"], index=0)
    chosen_val = (
        forecast["optimistic_price"]
        if scenario_choice == "Optimistic"
        else (forecast["conservative_price"] if scenario_choice == "Conservative" else forecast["base_price"])
    )
    f_left, f_right = st.columns([1.6, 1.0])
    with f_left:
        st.markdown(f'<div class="card-panel"><h4>Value Projection ({place_label}, {selected_state} to {target_year})</h4>', unsafe_allow_html=True)
        st.line_chart(forecast["series_df"], height=310)
        st.markdown("</div>", unsafe_allow_html=True)
    with f_right:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Selected Scenario ({scenario_choice} - {target_year})</div>
                <div class="kpi-value">{format_naira(chosen_val)}</div>
                <div class="kpi-sub">{forecast['verdict']} signal over {forecast['years']} years</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Optimistic ({target_year})</div>
                <div class="kpi-value">{format_naira(forecast['optimistic_price'])}</div>
                <div class="kpi-sub">Upper automatic bound</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Conservative ({target_year})</div>
                <div class="kpi-value">{format_naira(forecast['conservative_price'])}</div>
                <div class="kpi-sub-muted">Lower automatic bound</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif nav_section == "Location Map":
    m_left, m_right = st.columns([1.6, 1.0])
    with m_left:
        st.markdown(f'<div class="card-panel"><h4>Location Insights &amp; Map — {place_label}, {selected_state}</h4>', unsafe_allow_html=True)
        render_map(place_label, selected_state, profile, forecast, auto_price, height=360)
        st.caption(f"Pinned at ({profile['lat']}, {profile['lon']}) | Current: {format_naira(auto_price)} | {target_year}: {format_naira(forecast['base_price'])}")
        st.markdown("</div>", unsafe_allow_html=True)
    with m_right:
        st.markdown('<div class="card-panel"><h4>Market Tier Legend</h4>', unsafe_allow_html=True)
        for t_name, t_info in COMMUNITY_TIERS.items():
            st.markdown(
                f"""
                <div class="rank-row">
                    <div><b>{t_name}</b><br/><span style="color:#556d63; font-size:0.8rem;">{t_info['desc']}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

elif nav_section == "Compare Locations":
    st.markdown(f'<div class="card-panel"><h4>Compare All 36 States &amp; FCT ({selected_tier} - {target_year})</h4>', unsafe_allow_html=True)
    table_rows = []
    for st_name, reg, b_price, b_cagr, b_yield, cov, _, _, note in NIGERIA_LOCATIONS:
        p_now = round(b_price * COMMUNITY_TIERS[selected_tier]["price_mult"] * PROPERTY_MULTIPLIERS[selected_prop], -5)
        fc_row = compute_forecast(note, float(p_now), float(b_cagr + COMMUNITY_TIERS[selected_tier]["cagr_bonus"]), int(target_year))
        table_rows.append(
            {
                "Location": st_name,
                "Region": reg,
                "Current Price (Auto)": p_now,
                f"Projected {target_year} (Base)": round(fc_row["base_price"], -5),
                "Growth (%)": round(fc_row["pct_change"], 1),
                "Direction": fc_row["verdict"],
                "Rental Yield (%)": round(b_yield * 100, 1),
                "Market Tier": selected_tier,
            }
        )
    comp_df = pd.DataFrame(table_rows)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    st.download_button(
        label="Export Report (CSV)",
        data=comp_df.to_csv(index=False).encode("utf-8"),
        file_name=f"nigeria_property_report_{target_year}.csv",
        mime="text/csv",
    )
    st.markdown("</div>", unsafe_allow_html=True)

elif nav_section == "Saved Analysis":
    st.markdown('<div class="card-panel"><h4>Saved Property Analyses</h4>', unsafe_allow_html=True)
    if st.session_state["saved_analyses"]:
        saved_df = pd.DataFrame(st.session_state["saved_analyses"])
        st.dataframe(saved_df, use_container_width=True, hide_index=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.download_button(
                label="Download Saved Report (CSV)",
                data=saved_df.to_csv(index=False).encode("utf-8"),
                file_name="saved_nigeria_property_analyses.csv",
                mime="text/csv",
            )
        with col_s2:
            if st.button("Clear Saved Analyses"):
                st.session_state["saved_analyses"] = []
                st.rerun()
    else:
        st.info("No saved analyses yet. Click 'Save Current Analysis' on the Dashboard to store properties here.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card-panel"><h4>Moderator Market Change &amp; Forecast Log</h4>', unsafe_allow_html=True)
mod_df = pd.DataFrame(st.session_state["moderator_log"])
st.dataframe(mod_df, use_container_width=True, hide_index=True)
st.download_button(
    label="Export Moderator Log (CSV)",
    data=mod_df.to_csv(index=False).encode("utf-8"),
    file_name=f"moderator_market_log_{target_year}.csv",
    mime="text/csv",
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("#### Key Platform Features")
f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    st.markdown(
        '<div class="feature-card"><div class="feature-title">Accurate Price Estimation</div><div class="feature-desc">Automatic market values from location and tier baselines.</div></div>',
        unsafe_allow_html=True,
    )
with f2:
    st.markdown(
        '<div class="feature-card"><div class="feature-title">Flexible Forecasting</div><div class="feature-desc">Multi-scenario growth paths to any target year.</div></div>',
        unsafe_allow_html=True,
    )
with f3:
    st.markdown(
        '<div class="feature-card"><div class="feature-title">Interactive Map</div><div class="feature-desc">Statewide green coverage with red-dot pin and N10B alert.</div></div>',
        unsafe_allow_html=True,
    )
with f4:
    st.markdown(
        '<div class="feature-card"><div class="feature-title">Market Insights</div><div class="feature-desc">Rental yields, HIGH/DROP signals, and moderator change log.</div></div>',
        unsafe_allow_html=True,
    )
with f5:
    st.markdown(
        '<div class="feature-card"><div class="feature-title">Compare &amp; Export</div><div class="feature-desc">Side-by-side 36-state comparison and downloadable CSV reports.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="disclaimer-box">
        Valuations and multi-year forecasts are automatically modeled across all 36 states and the FCT for planning and presentation purposes, not financial guarantees.
    </div>
    """,
    unsafe_allow_html=True,
)