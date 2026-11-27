import hashlib
import os
import re
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Nigeria Property Valuation & Long-Term Forecast Advisor",
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

# (State/FCT, Region, Mid-City Reference Price, Base CAGR, Base Gross Yield, Coverage, Lat, Lon)
NIGERIA_LOCATIONS = [
    ("FCT Abuja", "North Central", 180_000_000, 0.042, 0.055, "High", 9.0765, 7.3986),
    ("Lagos", "South West", 220_000_000, 0.045, 0.062, "High", 6.5244, 3.3792),
    ("Rivers", "South South", 85_000_000, 0.025, 0.058, "Medium", 4.8156, 7.0498),
    ("Oyo", "South West", 55_000_000, 0.028, 0.056, "Medium", 8.2151, 3.5643),
    ("Ogun", "South West", 48_000_000, 0.032, 0.054, "Medium", 6.9789, 3.4389),
    ("Enugu", "South East", 65_000_000, 0.026, 0.055, "Medium", 6.5244, 7.5086),
    ("Anambra", "South East", 68_000_000, 0.027, 0.055, "Medium", 6.2183, 6.9532),
    ("Kano", "North West", 60_000_000, 0.022, 0.057, "Medium", 12.0022, 8.5920),
    ("Kaduna", "North West", 48_000_000, 0.010, 0.056, "Medium", 10.5105, 7.4165),
    ("Edo", "South South", 55_000_000, 0.024, 0.056, "Medium", 6.6077, 5.9723),
    ("Delta", "South South", 58_000_000, 0.020, 0.057, "Medium", 5.5273, 6.1784),
    ("Akwa Ibom", "South South", 52_000_000, 0.023, 0.056, "Medium", 4.9409, 7.8412),
    ("Cross River", "South South", 42_000_000, 0.016, 0.055, "Baseline", 5.8672, 8.5205),
    ("Abia", "South East", 46_000_000, 0.018, 0.056, "Baseline", 5.4541, 7.5153),
    ("Imo", "South East", 50_000_000, 0.020, 0.056, "Baseline", 5.5720, 7.0588),
    ("Ebonyi", "South East", 32_000_000, 0.014, 0.055, "Baseline", 6.1997, 8.0349),
    ("Ondo", "South West", 38_000_000, 0.016, 0.055, "Baseline", 7.0210, 5.0567),
    ("Osun", "South West", 35_000_000, 0.015, 0.054, "Baseline", 7.5484, 4.4978),
    ("Ekiti", "South West", 30_000_000, 0.013, 0.054, "Baseline", 7.7369, 5.2738),
    ("Kwara", "North Central", 40_000_000, 0.018, 0.055, "Baseline", 8.8368, 4.6688),
    ("Plateau", "North Central", 42_000_000, 0.010, 0.055, "Baseline", 9.0583, 9.6826),
    ("Niger", "North Central", 38_000_000, 0.018, 0.055, "Baseline", 9.9326, 5.6511),
    ("Kogi", "North Central", 28_000_000, -0.004, 0.055, "Baseline", 7.7950, 6.6869),
    ("Benue", "North Central", 30_000_000, -0.005, 0.055, "Baseline", 7.3506, 8.7773),
    ("Nasarawa", "North Central", 45_000_000, 0.028, 0.055, "Medium", 8.4388, 8.2383),
    ("Bauchi", "North East", 28_000_000, 0.008, 0.056, "Baseline", 10.6371, 10.0807),
    ("Borno", "North East", 25_000_000, -0.010, 0.056, "Baseline", 11.8311, 13.1510),
    ("Gombe", "North East", 27_000_000, 0.009, 0.055, "Baseline", 10.2791, 11.1731),
    ("Taraba", "North East", 24_000_000, -0.005, 0.055, "Baseline", 8.0141, 10.7376),
    ("Adamawa", "North East", 26_000_000, -0.004, 0.055, "Baseline", 9.3265, 12.3984),
    ("Yobe", "North East", 22_000_000, -0.012, 0.056, "Baseline", 12.1233, 11.5066),
    ("Sokoto", "North West", 30_000_000, 0.006, 0.056, "Baseline", 13.0611, 5.3152),
    ("Zamfara", "North West", 22_000_000, -0.015, 0.056, "Baseline", 12.0079, 6.4191),
    ("Kebbi", "North West", 24_000_000, 0.004, 0.056, "Baseline", 11.4168, 4.1075),
    ("Jigawa", "North West", 23_000_000, 0.005, 0.056, "Baseline", 12.5631, 9.3800),
    ("Katsina", "North West", 30_000_000, 0.007, 0.056, "Baseline", 12.5631, 7.6207),
    ("Bayelsa", "South South", 36_000_000, 0.010, 0.056, "Baseline", 4.7630, 6.0289),
]

# Community / Area tiers to differentiate prime city centers, developing cities, and satellite communities
COMMUNITY_TIERS = {
    "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)": {
        "price_mult": 2.40,
        "cagr_bonus": 0.008,
        "label": "Prime City Core",
    },
    "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)": {
        "price_mult": 1.00,
        "cagr_bonus": 0.000,
        "label": "Mid-Tier City",
    },
    "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)": {
        "price_mult": 0.35,
        "cagr_bonus": 0.004,
        "label": "Satellite Community",
    },
}

# Known high-value & satellite district overrides + exact coordinates for accurate map pinning
KNOWN_AREAS = {
    "asokoro": ("FCT Abuja", 820_000_000, 0.048, 9.0479, 7.5155, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "maitama": ("FCT Abuja", 900_000_000, 0.048, 9.0882, 7.4934, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "wuse 2": ("FCT Abuja", 650_000_000, 0.045, 9.0787, 7.4793, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "wuse": ("FCT Abuja", 520_000_000, 0.044, 9.0765, 7.4700, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "guzape": ("FCT Abuja", 580_000_000, 0.047, 9.0160, 7.5140, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "katampe": ("FCT Abuja", 340_000_000, 0.045, 9.1040, 7.4560, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "jahi": ("FCT Abuja", 280_000_000, 0.044, 9.0942, 7.4310, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "gwarinpa": ("FCT Abuja", 210_000_000, 0.042, 9.1099, 7.4042, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "wuye": ("FCT Abuja", 230_000_000, 0.043, 9.0480, 7.4430, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "utako": ("FCT Abuja", 240_000_000, 0.042, 9.0670, 7.4420, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "lokogoma": ("FCT Abuja", 110_000_000, 0.040, 8.9790, 7.4750, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "lugbe": ("FCT Abuja", 75_000_000, 0.043, 8.9868, 7.3626, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "kubwa": ("FCT Abuja", 85_000_000, 0.041, 9.1538, 7.3220, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "kuje": ("FCT Abuja", 35_000_000, 0.038, 8.8795, 7.2276, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "gwagwalada": ("FCT Abuja", 30_000_000, 0.035, 8.9408, 7.0818, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "ikoyi": ("Lagos", 950_000_000, 0.050, 6.4549, 3.4346, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "banana island": ("Lagos", 1_400_000_000, 0.052, 6.4650, 3.4510, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "victoria island": ("Lagos", 780_000_000, 0.048, 6.4281, 3.4219, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "lekki": ("Lagos", 320_000_000, 0.046, 6.4698, 3.5852, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "ikeja": ("Lagos", 350_000_000, 0.044, 6.6018, 3.3515, "Developing / Mid-Tier City District (e.g., Gwarinpa, Wuye, Lekki, Ikeja)"),
    "ajah": ("Lagos", 130_000_000, 0.043, 6.4667, 3.5667, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "epe": ("Lagos", 45_000_000, 0.046, 6.5841, 3.9834, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "ikorodu": ("Lagos", 50_000_000, 0.040, 6.6194, 3.5105, "Outskirt / Satellite Community & Rural LGA (e.g., Lugbe, Kubwa, Kuje, Epe)"),
    "gra phase 2": ("Rivers", 210_000_000, 0.030, 4.8242, 7.0036, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "old gra": ("Rivers", 230_000_000, 0.030, 4.7890, 7.0120, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "bodija": ("Oyo", 140_000_000, 0.032, 7.4200, 3.9100, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
    "independence layout": ("Enugu", 150_000_000, 0.030, 6.4402, 7.5250, "Prime / Major City Core (e.g., Asokoro, Maitama, Ikoyi, VI, GRA)"),
}

POSITIVE_TERMS = {
    "high": 0.014,
    "rise": 0.014,
    "rising": 0.014,
    "appreciate": 0.016,
    "appreciation": 0.016,
    "grow": 0.013,
    "growth": 0.013,
    "boom": 0.020,
    "demand": 0.012,
    "infrastructure": 0.015,
    "road": 0.010,
    "roads": 0.010,
    "rail": 0.014,
    "metro": 0.014,
    "airport": 0.013,
    "development": 0.012,
    "commercial": 0.012,
    "expansion": 0.012,
    "urban": 0.010,
    "prime": 0.014,
    "scarce": 0.012,
    "scarcity": 0.012,
    "up": 0.011,
    "increase": 0.013,
    "increasing": 0.013,
}

NEGATIVE_TERMS = {
    "drop": -0.026,
    "dropping": -0.026,
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


def resolve_location_profile(
    place_name: str,
    state_name: str,
    community_tier_key: str,
    property_multiplier: float,
) -> dict:
    clean_place = (place_name or "").strip().lower()
    state_meta = next(item for item in NIGERIA_LOCATIONS if item[0] == state_name)
    tier_meta = COMMUNITY_TIERS[community_tier_key]

    # Check if typed area matches a known district/community in that state
    matched_known = None
    for key, val in KNOWN_AREAS.items():
        if key in clean_place and val[0] == state_name:
            matched_known = val
            break

    if matched_known:
        _, area_base_price, area_cagr, lat, lon, matched_tier = matched_known
        estimated_now = round(area_base_price * property_multiplier, -5)
        effective_cagr = area_cagr
        tier_label = COMMUNITY_TIERS[matched_tier]["label"]
    else:
        estimated_now = round(state_meta[2] * tier_meta["price_mult"] * property_multiplier, -5)
        effective_cagr = state_meta[3] + tier_meta["cagr_bonus"]
        base_lat, base_lon = float(state_meta[6]), float(state_meta[7])
        if clean_place:
            digest = hashlib.md5(f"{state_name}::{clean_place}".encode("utf-8")).hexdigest()
            lat = round(base_lat + (((int(digest[:8], 16) / 0xFFFFFFFF) - 0.5) * 0.22), 5)
            lon = round(base_lon + (((int(digest[8:16], 16) / 0xFFFFFFFF) - 0.5) * 0.22), 5)
        else:
            lat, lon = base_lat, base_lon
        tier_label = tier_meta["label"]

    return {
        "estimated_now": float(max(2_000_000, estimated_now)),
        "effective_cagr": effective_cagr,
        "lat": lat,
        "lon": lon,
        "tier_label": tier_label,
        "region": state_meta[1],
        "gross_yield": state_meta[4],
        "coverage": state_meta[5],
    }


@st.cache_data
def load_nationwide_properties() -> pd.DataFrame:
    base_rows = []
    property_types = [
        ("Standard Residential Plot (500–600 sqm)", 0, 1.00, 0.045),
        ("4-Bedroom Semi-Detached Duplex", 4, 1.25, 0.056),
        ("5-Bedroom Fully Detached Duplex", 5, 1.65, 0.052),
        ("3-Bedroom Detached Bungalow", 3, 0.85, 0.060),
    ]

    for state_name, region, base_price, base_cagr, base_yield, coverage, lat, lon in NIGERIA_LOCATIONS:
        for p_type, beds, mult, y_val in property_types:
            fair_val = round(base_price * mult, -5)
            asking_val = round(fair_val * 0.97, -5)
            base_rows.append(
                {
                    "state": state_name,
                    "region": region,
                    "property_type": p_type,
                    "property_mult": mult,
                    "bedrooms": beds,
                    "asking_price": asking_val,
                    "fair_value": fair_val,
                    "annual_cagr": base_cagr,
                    "gross_yield": y_val,
                    "data_coverage": coverage,
                    "lat": lat,
                    "lon": lon,
                }
            )
    return pd.DataFrame(base_rows)


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

    text_rate_delta = max(-0.080, min(0.060, text_rate_delta))

    conservative_rate = max(-0.06, min(0.16, base_cagr + text_rate_delta - 0.012))
    base_rate = max(-0.05, min(0.18, base_cagr + text_rate_delta))
    optimistic_rate = max(-0.03, min(0.20, base_cagr + text_rate_delta + 0.012))

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
            f"Projected to remain steady near {format_naira(base_price)} ({pct_change_base:+.1f}%) "
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
        return "Enter a question about location pricing, community tiers, or future projections."
    return (
        f"For {place_label} in {state_name} over {forecast_info['years']} years (to {2026 + forecast_info['years']}), "
        f"the projected direction is {forecast_info['direction']} with a base estimate of "
        f"{format_naira(forecast_info['base_price'])} (conservative: {format_naira(forecast_info['conservative_price'])}, "
        f"optimistic: {format_naira(forecast_info['optimistic_price'])}). "
        f"These figures are modeled estimates, not guarantees."
    )


df = load_nationwide_properties()
all_states = [s[0] for s in NIGERIA_LOCATIONS]
tier_options = list(COMMUNITY_TIERS.keys())
property_options = df["property_type"].unique().tolist()

# Sidebar: Property profile + Advisor
with st.sidebar:
    st.markdown("### Property & Benchmark Settings")
    selected_property = st.selectbox("Property Type / Land Option", property_options, index=0)
    prop_mult = float(df[df["property_type"] == selected_property]["property_mult"].iloc[0])

    st.markdown("---")
    st.markdown("### Property Advisor")
    advisor_prompt = st.text_area(
        "Ask about city vs. community pricing or future outlook",
        placeholder="Example: Compare Asokoro vs. Lugbe land value by 2040.",
        height=90,
    )
    ask_clicked = st.button("Run Advisor", use_container_width=True)

# Header banner
st.markdown(
    """
    <div class="main-header">
        <h1>Nigeria Property Valuation &amp; Long-Term Forecast Advisor</h1>
        <p>Nationwide valuation across all 36 states, FCT, major cities, and local communities with red-dot mapping and balanced HIGH/DROP forecasting.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Location, community tier, and target year inputs
st.markdown("### Location, Community Tier & Future Price Forecast")
c_loc1, c_loc2, c_loc3 = st.columns([1.2, 1.0, 1.5])
with c_loc1:
    typed_place = st.text_input(
        "Type Place, District, or Community Name",
        value="Asokoro",
        placeholder="e.g., Asokoro, Gwarinpa, Lugbe, Ikoyi, Lekki, GRA...",
    )
with c_loc2:
    chosen_state = st.selectbox(
        "Select State / FCT",
        all_states,
        index=0,
    )
with c_loc3:
    chosen_tier = st.selectbox(
        "Area / Community Category",
        tier_options,
        index=0,
    )

loc_profile = resolve_location_profile(
    place_name=typed_place,
    state_name=chosen_state,
    community_tier_key=chosen_tier,
    property_multiplier=prop_mult,
)

# Auto-sync starting price when location/state/tier/property changes
location_signature = f"{typed_place.strip().lower()}|{chosen_state}|{chosen_tier}|{selected_property}"
if st.session_state.get("last_loc_sig") != location_signature:
    st.session_state["last_loc_sig"] = location_signature
    st.session_state["starting_price_input"] = loc_profile["estimated_now"]

c_val1, c_val2, c_val3 = st.columns([1.1, 0.8, 1.8])
with c_val1:
    starting_amount = st.number_input(
        "Current Market Price Today (Naira)",
        min_value=1_000_000.0,
        max_value=20_000_000_000.0,
        step=5_000_000.0,
        key="starting_price_input",
    )
with c_val2:
    target_year = st.number_input(
        "Target Forecast Year",
        min_value=2027,
        max_value=2100,
        value=2040,
        step=1,
    )
with c_val3:
    user_thesis = st.text_input(
        "Type market conditions or risk factors (optional)",
        value="Steady urban demand and prime land scarcity",
        placeholder="Type factors such as infrastructure and demand, or flooding, insecurity, and price drop...",
    )

display_place_name = typed_place.strip() if typed_place.strip() else chosen_state

forecast = analyze_user_text_and_forecast(
    user_text=user_thesis,
    starting_price=starting_amount,
    base_cagr=float(loc_profile["effective_cagr"]),
    target_year=int(target_year),
)

# Direction banner (HIGH / DROP / STEADY)
st.markdown(
    f"""
    <div class="{forecast['signal_class']}">
        <div>{target_year} Direction for {display_place_name}, {chosen_state} ({loc_profile['tier_label']}): {forecast['direction']}</div>
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
    st.markdown("#### Location Map")
    pin_df = pd.DataFrame(
        [
            {
                "place": display_place_name,
                "state": chosen_state,
                "tier": loc_profile["tier_label"],
                "lat": loc_profile["lat"],
                "lon": loc_profile["lon"],
                "verdict": forecast["short_verdict"],
                "current_price": format_naira(starting_amount),
                "projected_price": format_naira(forecast["base_price"]),
            }
        ]
    )

    outer_ring_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color="[220, 38, 38, 65]",
        get_radius=35000,
        radius_min_pixels=24,
        radius_max_pixels=65,
        pickable=False,
    )

    red_dot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pin_df,
        get_position="[lon, lat]",
        get_color="[220, 38, 38, 240]",
        get_radius=20000,
        radius_min_pixels=14,
        radius_max_pixels=36,
        stroked=True,
        get_line_color="[255, 255, 255, 255]",
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=loc_profile["lat"],
        longitude=loc_profile["lon"],
        zoom=9.2,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[outer_ring_layer, red_dot_layer],
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": (
                "<b>Place:</b> {place} ({tier})<br/>"
                "<b>State:</b> {state}<br/>"
                "<b>Today:</b> {current_price}<br/>"
                "<b>Direction:</b> {verdict}<br/>"
                "<b>Projected:</b> {projected_price}"
            ),
            "style": {"backgroundColor": "#ffffff", "color": "#0f2942"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True, height=345)
    st.caption(
        f"Pinned at {display_place_name}, {chosen_state} ({loc_profile['lat']}, {loc_profile['lon']})."
    )

with info_col:
    st.markdown(f"#### {target_year} Valuation Scenarios")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Conservative ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['conservative_price'])}</div>
            <div class="metric-sub">Lower-bound scenario</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Base Estimate ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['base_price'])}</div>
            <div class="metric-sub">Net change: {forecast['pct_change_base']:+.1f}% over {forecast['years']} yrs</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Optimistic ({target_year})</div>
            <div class="metric-value">{format_naira(forecast['optimistic_price'])}</div>
            <div class="metric-sub">Upper-bound scenario</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Summary metrics for the selected community tier
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Community Benchmark Today</div>
            <div class="metric-value">{format_naira(loc_profile['estimated_now'])}</div>
            <div class="metric-sub">{loc_profile['tier_label']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">State &amp; Region</div>
            <div class="metric-value">{chosen_state}</div>
            <div class="metric-sub">{loc_profile['region']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Est. Gross Rental Yield</div>
            <div class="metric-value">{loc_profile['gross_yield'] * 100:.1f}%</div>
            <div class="metric-sub">Annual yield benchmark</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Data Coverage Tier</div>
            <div class="metric-value">{loc_profile['coverage']}</div>
            <div class="metric-sub">36-State + FCT Model</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if ask_clicked:
    st.info(answer_advisor_question(advisor_prompt, display_place_name, chosen_state, forecast))

# Nationwide summary table across all 36 states + FCT for the chosen community tier
st.markdown(f"### All 36 States & FCT Comparison ({COMMUNITY_TIERS[chosen_tier]['label']})")
region_filter = st.selectbox(
    "Filter Table by Geopolitical Zone",
    ["All Regions", "North Central", "North East", "North West", "South East", "South South", "South West"],
    index=0,
)

tier_mult = COMMUNITY_TIERS[chosen_tier]["price_mult"]
tier_cagr_bonus = COMMUNITY_TIERS[chosen_tier]["cagr_bonus"]

summary_rows = []
for state_name, region, base_price, base_cagr, base_yield, coverage, _, _ in NIGERIA_LOCATIONS:
    if region_filter != "All Regions" and region != region_filter:
        continue
    now_est = round(base_price * tier_mult * prop_mult, -5)
    fc = analyze_user_text_and_forecast(
        user_text=user_thesis,
        starting_price=float(now_est),
        base_cagr=float(base_cagr + tier_cagr_bonus),
        target_year=int(target_year),
    )
    summary_rows.append(
        {
            "State / FCT": state_name,
            "Region": region,
            "Community Tier": COMMUNITY_TIERS[chosen_tier]["label"],
            "Current Est. (N)": now_est,
            f"Projected {target_year} (N)": round(fc["base_price"], -5),
            "Direction": fc["short_verdict"],
            "Coverage": coverage,
        }
    )

st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

st.markdown(
    """
    <div class="disclaimer-box">
        Valuations and future projections reflect city-core, mid-tier, and satellite-community benchmarks across Nigeria's 36 states and FCT. Future prices and HIGH/DROP signals are scenario-based estimates for planning and defense discussion, not guarantees.
    </div>
    """,
    unsafe_allow_html=True,
)