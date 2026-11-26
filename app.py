import os
import pickle
import re

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ABUJA_TOWNS = ["Gwarinpa", "Wuye", "Jahi", "Lokogoma", "Lugbe", "Kubwa"]
MODEL_PATH = "abuja_price_model.pkl"
DATA_PATH = "abuja_rental_cleaned.csv"

st.set_page_config(
    page_title="Abuja Property Valuation & Investment Advisor",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.75rem;
            padding-bottom: 2rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.55rem;
            font-weight: 600;
        }
        .section-divider {
            border: none;
            border-top: 1px solid rgba(128, 128, 128, 0.22);
            margin: 1.5rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_town(value: object) -> str:
  text = str(value or "").strip()
  for town in ABUJA_TOWNS:
    if town.lower() in text.lower():
      return town
  return text if text else "Abuja"


def classify_recommendation(diff_pct: float) -> str:
  if diff_pct <= -15.0:
    return "Strong Buy (Undervalued)"
  if diff_pct <= 5.0:
    return "Fair Value / Hold"
  return "Overpriced (Negotiate / Skip)"


@st.cache_data
def load_abuja_data(csv_path: str) -> pd.DataFrame:
  raw = pd.read_csv(csv_path)
  data = raw.copy()

  data["price"] = pd.to_numeric(data.get("price"), errors="coerce")
  data["bedrooms"] = (
      pd.to_numeric(data.get("bedrooms"), errors="coerce").fillna(3).astype(int)
  )

  for col in ["bathrooms", "toilets", "parking_space"]:
    if col in data.columns:
      data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)
    else:
      data[col] = 0

  town_col = "town_standard" if "town_standard" in data.columns else "town"
  if town_col in data.columns:
    data["town_standard"] = data[town_col].apply(normalize_town)
  else:
    data["town_standard"] = "Gwarinpa"

  title_col = "title_clean" if "title_clean" in data.columns else "title"
  if title_col in data.columns:
    data["title_clean"] = data[title_col].fillna("Residential Property").astype(str)
  else:
    data["title_clean"] = "Residential Property"

  data = data.dropna(subset=["price"])
  data = data[data["price"] > 0].copy()

  abuja_subset = data[data["town_standard"].isin(ABUJA_TOWNS)].copy()
  if not abuja_subset.empty:
    data = abuja_subset

  return data.reset_index(drop=True)


@st.cache_resource
def load_or_train_model(
    data: pd.DataFrame, model_path: str
) -> tuple[Pipeline, dict[str, float]]:
  feature_cols = [
      "town_standard",
      "title_clean",
      "bedrooms",
      "bathrooms",
      "toilets",
      "parking_space",
  ]
  for col in feature_cols:
    if col not in data.columns:
      data[col] = "Residential Property" if col == "title_clean" else 0

  X = data[feature_cols].copy()
  y_log = np.log1p(data["price"].astype(float))

  X_train, X_test, y_train, y_test = train_test_split(
      X, y_log, test_size=0.2, random_state=42
  )

  pipeline = None
  if os.path.exists(model_path):
    try:
      with open(model_path, "rb") as f:
        loaded = pickle.load(f)
      if hasattr(loaded, "predict"):
        test_pred = loaded.predict(X_test)
        if len(test_pred) == len(X_test):
          pipeline = loaded
    except Exception:
      pipeline = None

  if pipeline is None:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["town_standard", "title_clean"],
            ),
            (
                "num",
                "passthrough",
                ["bedrooms", "bathrooms", "toilets", "parking_space"],
            ),
        ]
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=4,
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    try:
      with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)
    except Exception:
      pass

  pred_log_test = pipeline.predict(X_test)
  actual_test = np.expm1(y_test)
  pred_test = np.expm1(pred_log_test)
  metrics = {
      "r2": float(r2_score(actual_test, pred_test)),
      "mae": float(mean_absolute_error(actual_test, pred_test)),
  }
  return pipeline, metrics


def score_abuja_properties(
    data: pd.DataFrame, model: Pipeline, yield_rate: float = 0.05
) -> pd.DataFrame:
  feature_cols = [
      "town_standard",
      "title_clean",
      "bedrooms",
      "bathrooms",
      "toilets",
      "parking_space",
  ]
  scored = data.copy()
  pred_log = model.predict(scored[feature_cols])
  scored["predicted_fair_price"] = np.maximum(np.expm1(pred_log), 100_000.0)
  scored["price_diff_pct"] = (
      (scored["price"] - scored["predicted_fair_price"])
      / scored["predicted_fair_price"]
  ) * 100.0
  scored["recommendation"] = scored["price_diff_pct"].apply(
      classify_recommendation
  )
  scored["est_annual_rent"] = scored["predicted_fair_price"] * yield_rate
  scored["est_gross_yield"] = (
      scored["est_annual_rent"] / scored["price"]
  ) * 100.0
  return scored


def generate_property_ai_reply(
    prompt_text: str,
    abuja_df: pd.DataFrame,
    selected_row: pd.Series,
    yield_rate: float,
) -> str:
  q = (prompt_text or "").lower().strip()
  available_towns = sorted(
      [
          t
          for t in abuja_df["town_standard"].dropna().unique().tolist()
          if t in ABUJA_TOWNS
      ]
  ) or ABUJA_TOWNS

  matched_towns = [t for t in available_towns if t.lower() in q]
  if not matched_towns and "lokogoma" in q:
    matched_towns = ["Lokogoma"]

  bed_match = re.search(r"(\d+)\s*-?\s*bed(?:room)?s?", q)
  req_beds = int(bed_match.group(1)) if bed_match else None

  budget_naira = None
  m_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|million)\b", q)
  if m_match:
    budget_naira = float(m_match.group(1)) * 1_000_000.0
  else:
    raw_num = re.search(r"₦?\s*(\d{2,3}(?:,\d{3}){2,}|\d{7,11})", q)
    if raw_num:
      budget_naira = float(raw_num.group(1).replace(",", ""))

  cur_bedrooms = int(selected_row["bedrooms"])
  cur_title = str(selected_row["title_clean"])
  cur_town = str(selected_row["town_standard"])
  cur_asking = float(selected_row["price"])
  cur_fair = float(selected_row["predicted_fair_price"])
  cur_diff_pct = float(selected_row["price_diff_pct"])
  cur_annual_rent = float(selected_row["est_annual_rent"])
  cur_gross_yield = float(selected_row["est_gross_yield"])

  # 1. How & why Abuja property prices change
  if any(
      k in q
      for k in [
          "change",
          "fluctuate",
          "rise",
          "increase",
          "drop",
          "fall",
          "inflation",
          "market",
          "why",
          "trend",
      ]
  ):
    return (
        "**How Abuja Property Prices Move**\n"
        "- **Construction and Input Costs:** Cement, steel, reinforcement, and"
        " finishing materials drive baseline replacement values across Abuja.\n"
        "- **Corridor and Infrastructure Growth:** Expansion and road"
        " upgrades around **Lugbe**, **Kubwa**, **Lokogoma**, and **Jahi**"
        " reshape buyer demand over time.\n"
        "- **Serviced Estate Standards:** Reliable power backup, security,"
        " access roads, and estate management create clear price spreads in"
        " **Wuye** and **Gwarinpa**.\n"
        "- **Asking vs. Valuation Spread:** Sellers in Abuja often price in"
        " negotiation room, making fair-value benchmarking essential before"
        " making an offer."
    )

  # 2. Compare two Abuja neighborhoods
  if len(matched_towns) >= 2 and any(
      k in q for k in ["compare", "vs", "versus", "between", "difference"]
  ):
    t1, t2 = matched_towns[0], matched_towns[1]
    d1 = abuja_df[abuja_df["town_standard"] == t1]
    d2 = abuja_df[abuja_df["town_standard"] == t2]
    if d1.empty or d2.empty:
      return (
          f"Insufficient Abuja listing records to compare **{t1}** and"
          f" **{t2}**."
      )
    lower_fair_town = (
        t1
        if d1["predicted_fair_price"].mean() < d2["predicted_fair_price"].mean()
        else t2
    )
    return (
        f"**Abuja Neighborhood Comparison: {t1} vs. {t2}**\n"
        f"- **{t1} ({len(d1)} listings):** Avg Asking"
        f" **N{d1['price'].mean():,.0f}** | Avg Fair Value"
        f" **N{d1['predicted_fair_price'].mean():,.0f}**\n"
        f"- **{t2} ({len(d2)} listings):** Avg Asking"
        f" **N{d2['price'].mean():,.0f}** | Avg Fair Value"
        f" **N{d2['predicted_fair_price'].mean():,.0f}**\n"
        f"- **Lower Average Fair Value:** **{lower_fair_town}**"
    )

  # 3. Budget lookup across Abuja
  if budget_naira is not None:
    subset = abuja_df[
        abuja_df["town_standard"].isin(available_towns)
        & (abuja_df["price"] <= budget_naira)
    ].copy()
    if matched_towns:
      subset = subset[subset["town_standard"].isin(matched_towns)]
    if req_beds:
      subset = subset[subset["bedrooms"] == req_beds]

    area_label = ", ".join(matched_towns) if matched_towns else "Abuja"
    bed_label = f", {req_beds}-bedroom" if req_beds else ""

    if subset.empty:
      return (
          f"No Abuja properties found at or below **N{budget_naira:,.0f}** in"
          f" **{area_label}**{bed_label}. Consider raising the budget or"
          " checking **Lugbe** or **Kubwa**."
      )

    top_matches = subset.sort_values("price_diff_pct").head(3)
    lines = [
        f"Found **{len(subset)}** Abuja listings at or below"
        f" **N{budget_naira:,.0f}** in **{area_label}**{bed_label}. Top"
        " matches:"
    ]
    for _, row in top_matches.iterrows():
      lines.append(
          f"- **{row['town_standard']}, Abuja** — {int(row['bedrooms'])}-bed"
          f" {row['title_clean']} | Asking: **N{row['price']:,.0f}** | Fair"
          f" Value: **N{row['predicted_fair_price']:,.0f}**"
          f" ({row['price_diff_pct']:+.1f}%)"
      )
    return "\n".join(lines)

  # 4. Negotiation / bargaining guidance
  if any(
      k in q
      for k in [
          "bargain",
          "negotiate",
          "offer",
          "counter",
          "reduce",
          "discount",
      ]
  ):
    target_low = cur_fair * 0.90
    target_mid = cur_fair * 0.95
    if cur_diff_pct > 5:
      return (
          f"**Negotiation Guide — {cur_bedrooms}-Bed {cur_title} in"
          f" {cur_town}, Abuja**\n"
          f"- **Asking vs. Fair Value:** **N{cur_asking:,.0f}** vs."
          f" **N{cur_fair:,.0f}** (**{cur_diff_pct:+.1f}%**)\n"
          f"- **Opening Counter-Offer:** **N{target_low:,.0f}** (~10% below"
          " fair value)\n"
          f"- **Target Closing Range:** **N{target_mid:,.0f}** –"
          f" **N{cur_fair:,.0f}**"
      )
    if cur_diff_pct <= -15:
      return (
          f"**Negotiation Guide — {cur_bedrooms}-Bed {cur_title} in"
          f" {cur_town}, Abuja**\n"
          f"- Listed **{abs(cur_diff_pct):.1f}% below** fair value"
          f" (**N{cur_asking:,.0f}** asking vs. **N{cur_fair:,.0f}** fair"
          " value) — **Strong Buy**.\n"
          f"- Keep your offer near **N{cur_asking * 0.96:,.0f}** to avoid"
          " losing the listing."
      )
    return (
        f"**Negotiation Guide — {cur_bedrooms}-Bed {cur_title} in"
        f" {cur_town}, Abuja**\n"
        f"- Priced close to fair value (**{cur_diff_pct:+.1f}%** vs."
        f" **N{cur_fair:,.0f}**).\n"
        f"- Aim around **N{target_mid:,.0f}** (~5% discount) to improve"
        f" gross yield above **{cur_gross_yield:.1f}%**."
    )

  # 5. Best deals / Strong Buy
  if any(
      k in q
      for k in ["strong buy", "best deal", "undervalued", "cheap", "recommend"]
  ):
    subset = abuja_df[
        abuja_df["town_standard"].isin(available_towns)
        & (abuja_df["recommendation"] == "Strong Buy (Undervalued)")
    ].copy()
    if matched_towns:
      subset = subset[subset["town_standard"].isin(matched_towns)]
    if req_beds:
      subset = subset[subset["bedrooms"] == req_beds]
    if subset.empty:
      return (
          "No **Strong Buy** Abuja listings match that exact filter. Try"
          " broadening the neighborhood or bedroom filter."
      )
    top_deals = subset.sort_values("price_diff_pct").head(3)
    area_label = ", ".join(matched_towns) if matched_towns else "Abuja"
    lines = [f"Top **Strong Buy** Abuja listings in **{area_label}**:"]
    for _, row in top_deals.iterrows():
      lines.append(
          f"- **{row['town_standard']}, Abuja** — {int(row['bedrooms'])}-bed"
          f" {row['title_clean']} | Asking: **N{row['price']:,.0f}** | Fair"
          f" Value: **N{row['predicted_fair_price']:,.0f}**"
          f" ({row['price_diff_pct']:+.1f}%)"
      )
    return "\n".join(lines)

  # 6. Specific Abuja neighborhood summary
  if matched_towns:
    town_name = matched_towns[0]
    t_df = abuja_df[abuja_df["town_standard"] == town_name]
    if req_beds:
      t_df = t_df[t_df["bedrooms"] == req_beds]
    if t_df.empty:
      return f"No matching listings found in **{town_name}, Abuja**."
    return (
        f"**{town_name}, Abuja Market Summary ({len(t_df)} listings)**\n"
        f"- **Average Asking Price:** N{t_df['price'].mean():,.0f}\n"
        f"- **Average Fair Value:**"
        f" N{t_df['predicted_fair_price'].mean():,.0f}\n"
        f"- **Price Range:** N{t_df['price'].min():,.0f} –"
        f" N{t_df['price'].max():,.0f}"
    )

  # 7. Rental yield & return
  if any(k in q for k in ["yield", "rent", "roi", "return"]):
    return (
        f"**Rental & Yield Summary — {cur_bedrooms}-Bed {cur_title} in"
        f" {cur_town}, Abuja**\n"
        f"- **Estimated Annual Rent:** **N{cur_annual_rent:,.0f}**"
        f" ({yield_rate * 100:.1f}% benchmark)\n"
        f"- **Gross Yield at Asking Price:** **{cur_gross_yield:.1f}%**"
    )

  # Default Abuja guidance
  return (
      f"Active selection: **{cur_bedrooms}-bed {cur_title} in {cur_town},"
      f" Abuja** (Asking: **N{cur_asking:,.0f}** | Fair Value:"
      f" **N{cur_fair:,.0f}**).\n\n"
      "Ask about Abuja real estate:\n"
      '- *"What can N50,000,000 buy in Lokogoma?"*\n'
      '- *"Compare Gwarinpa vs Wuye"*\n'
      '- *"How much should I bargain on this property?"*\n'
      '- *"Why do Abuja property prices change?"*'
  )


# --- Main Application Flow ---
if not os.path.exists(DATA_PATH):
  st.error(f"Dataset not found: `{DATA_PATH}`")
  st.stop()

base_df = load_abuja_data(DATA_PATH)
model, model_metrics = load_or_train_model(base_df, MODEL_PATH)

st.title("Abuja Property Valuation & Investment Advisor")
st.caption(
    "Property valuation, pricing spread analysis, and investment guidance"
    " across Gwarinpa, Wuye, Jahi, Lokogoma, Lugbe, and Kubwa."
)

# Sidebar: Valuation assumptions + Abuja AI Property Advisor
with st.sidebar:
  st.header("Valuation Settings")
  yield_pct_input = st.slider(
      "Benchmark Annual Yield (%)",
      min_value=3.0,
      max_value=12.0,
      value=5.0,
      step=0.5,
  )
  yield_rate = yield_pct_input / 100.0

  df = score_abuja_properties(base_df, model, yield_rate=yield_rate)

  st.markdown("---")
  st.header("Abuja Property Advisor")
  st.caption(
      "Ask about Abuja budgets, counter-offers, yields, neighborhood"
      " comparisons, or market drivers."
  )

  if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{
        "role": "assistant",
        "content": (
            "Ask me about Abuja property budgets, bargaining targets, yields,"
            " or comparisons across Gwarinpa, Wuye, Jahi, Lokogoma, Lugbe, and"
            " Kubwa."
        ),
    }]

  for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])

# Ensure `df` is defined even if sidebar rendering order changes
if "df" not in locals():
  df = score_abuja_properties(base_df, model, yield_rate=0.05)

# Property Selector & Valuation Metrics
selected_idx = st.selectbox(
    "Select an Abuja Property to Evaluate",
    options=df.index.tolist(),
    format_func=lambda idx: (
        f"{df.loc[idx, 'town_standard']} — {int(df.loc[idx, 'bedrooms'])}-Bed"
        f" {df.loc[idx, 'title_clean']} (Asking:"
        f" N{df.loc[idx, 'price']:,.0f})"
    ),
)
selected_property = df.loc[selected_idx]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Asking Price", f"N{selected_property['price']:,.0f}")
m2.metric(
    "Predicted Fair Value", f"N{selected_property['predicted_fair_price']:,.0f}"
)
m3.metric("Asking vs. Fair Value", f"{selected_property['price_diff_pct']:+.1f}%")
m4.metric("Est. Annual Rent", f"N{selected_property['est_annual_rent']:,.0f}")

st.markdown(
    f"**Investment Recommendation:** {selected_property['recommendation']}  \n"
    f"**Estimated Gross Yield at Asking Price:**"
    f" {selected_property['est_gross_yield']:.2f}% (based on"
    f" {yield_pct_input:.1f}% benchmark yield)"
)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# Scored Listings Explorer
st.subheader("Scored Abuja Listings Explorer")

f_col1, f_col2 = st.columns(2)
with f_col1:
  selected_towns = st.multiselect(
      "Filter by Neighborhood",
      options=ABUJA_TOWNS,
      default=ABUJA_TOWNS,
  )
with f_col2:
  rec_options = [
      "Strong Buy (Undervalued)",
      "Fair Value / Hold",
      "Overpriced (Negotiate / Skip)",
  ]
  selected_recs = st.multiselect(
      "Filter by Recommendation",
      options=rec_options,
      default=rec_options,
  )

filtered_df = df[
    df["town_standard"].isin(selected_towns if selected_towns else ABUJA_TOWNS)
    & df["recommendation"].isin(selected_recs if selected_recs else rec_options)
].copy()

st.caption(
    f"Showing {len(filtered_df)} of {len(df)} scored Abuja properties | Model"
    f" R2: {model_metrics['r2']:.3f} | Test MAE: N{model_metrics['mae']:,.0f}"
)

display_cols = [
    "town_standard",
    "title_clean",
    "bedrooms",
    "price",
    "predicted_fair_price",
    "price_diff_pct",
    "est_gross_yield",
    "recommendation",
]
available_display_cols = [c for c in display_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[available_display_cols].rename(
        columns={
            "town_standard": "Neighborhood",
            "title_clean": "Property Type",
            "bedrooms": "Bedrooms",
            "price": "Asking Price (N)",
            "predicted_fair_price": "Fair Value (N)",
            "price_diff_pct": "Spread (%)",
            "est_gross_yield": "Gross Yield (%)",
            "recommendation": "Recommendation",
        }
    ),
    width="stretch",
    hide_index=True,
)

# Sidebar Chat Input (renders pinned at bottom of sidebar)
if user_prompt := st.sidebar.chat_input(
    "Ask about Abuja prices, budgets, or areas..."
):
  st.session_state.chat_messages.append(
      {"role": "user", "content": user_prompt}
  )
  reply = generate_property_ai_reply(
      prompt_text=user_prompt,
      abuja_df=df,
      selected_row=selected_property,
      yield_rate=yield_rate,
  )
  st.session_state.chat_messages.append(
      {"role": "assistant", "content": reply}
  )
  st.rerun()