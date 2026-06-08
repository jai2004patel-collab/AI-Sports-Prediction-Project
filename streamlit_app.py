import streamlit as st
import pandas as pd
import statistics

st.set_page_config(
    page_title="NBA AI Prop Predictor",
    page_icon="🏀",
    layout="wide"
)

CSV_FILE = "nba_props_data.csv"

# -----------------------------
# CLEAN LIGHT CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: #f8fafc;
    color: #0f172a;
}
.main-title {
    font-size: 44px;
    font-weight: 900;
    text-align: center;
    color: #0f172a;
    margin-bottom: 0px;
}
.sub-title {
    text-align: center;
    color: #475569;
    font-size: 18px;
    margin-bottom: 25px;
}
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    text-align: center;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}
.metric-label {
    color: #64748b;
    font-size: 13px;
}
.metric-value {
    color: #2563eb;
    font-size: 30px;
    font-weight: 900;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
def load_data():
    df = pd.read_csv(CSV_FILE, encoding="latin1")
    df["Line"] = pd.to_numeric(df["Line"], errors="coerce")
    df = df[df["Line"] > 0]
    return df

df = load_data()

# -----------------------------
# HELPERS
# -----------------------------
def safe_float(value, default=0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except:
        return default

def clamp(value, low, high):
    return max(low, min(high, value))

def predict_row(row):
    player = row["Player"]
    team = row["Team"]
    prop_type = row["Prop_Type"]
    line = safe_float(row["Line"])

    season_avg = safe_float(row["Season_Avg"])
    playoff_avg = safe_float(row["Playoff_Avg"])
    last5_avg = safe_float(row["Last5_Playoff_Avg"])
    last3_avg = safe_float(row["Last3_Playoff_Avg"])

    playoff_min = safe_float(row["Playoff_Min"])
    last5_min = safe_float(row["Last5_Min"])

    raw_projection = (
        season_avg * 0.20 +
        playoff_avg * 0.30 +
        last5_avg * 0.30 +
        last3_avg * 0.20
    )

    minute_ratio = last5_min / playoff_min if playoff_min > 0 else 1
    minute_adjustment = clamp(minute_ratio, 0.88, 1.08)

    trend_ratio = last5_avg / playoff_avg if playoff_avg > 0 else 1
    trend_adjustment = clamp(trend_ratio, 0.90, 1.07)

    avg_reference = (playoff_avg * 0.50) + (last5_avg * 0.50)
    line_pressure = line / avg_reference if avg_reference > 0 else 1

    if line_pressure >= 1.20:
        line_adjustment = 0.86
    elif line_pressure >= 1.10:
        line_adjustment = 0.91
    elif line_pressure >= 1.04:
        line_adjustment = 0.96
    elif line_pressure <= 0.84:
        line_adjustment = 1.07
    elif line_pressure <= 0.92:
        line_adjustment = 1.03
    else:
        line_adjustment = 1.00

    projected_stat = raw_projection * minute_adjustment * trend_adjustment * line_adjustment
    difference = projected_stat - line

    pick = "Over" if difference > 0 else "Under"
    edge = abs(difference)
    edge_percent = abs(difference / line) * 100 if line > 0 else 0

    values = [season_avg, playoff_avg, last5_avg, last3_avg]
    volatility = statistics.pstdev(values)

    confidence = 50 + (edge_percent * 0.55) - (volatility * 1.25)

    if edge < 0.75:
        confidence -= 8
    elif edge < 1.25:
        confidence -= 4

    if str(prop_type).lower() in ["assists", "rebounds"]:
        confidence -= 2

    confidence = clamp(confidence, 50, 92)

    if confidence >= 68 and edge >= 2.0:
        rating = "Strong"
    elif confidence >= 58 and edge >= 1.25:
        rating = "Lean"
    else:
        rating = "No Bet"

    explanation = f"""
Player: {player}
Team: {team}
Prop Type: {prop_type}
Line: {line}

Season Average: {season_avg}
Playoff Average: {playoff_avg}
Last 5 Playoff Average: {last5_avg}
Last 3 Playoff Average: {last3_avg}

Raw Projection: {raw_projection:.2f}
Final Projected Stat: {projected_stat:.2f}
Edge: {edge:.2f}

Recommendation: {pick}
Confidence: {confidence:.1f}%
Rating: {rating}

Explanation:
The model recommends the {pick} because the final projection is {projected_stat:.2f}
compared to the betting line of {line}.

The model uses season average, playoff average, last 5 playoff average, last 3 playoff average,
minutes trend, recent production trend, line pressure, and volatility penalty.

This is an AI-assisted decision-support model, not guaranteed betting advice.
"""

    return {
        "Player": player,
        "Team": team,
        "Prop Type": prop_type,
        "Line": line,
        "Pick": pick,
        "Projected Stat": round(projected_stat, 2),
        "Edge": round(edge, 2),
        "Confidence": round(confidence, 1),
        "Rating": rating,
        "Explanation": explanation
    }

# -----------------------------
# RUN MODEL
# -----------------------------
results = []
for _, row in df.iterrows():
    try:
        results.append(predict_row(row))
    except:
        pass

results_df = pd.DataFrame(results).sort_values(
    by=["Confidence", "Edge"],
    ascending=False
)

strong_df = results_df[results_df["Rating"] == "Strong"]

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="main-title">🏀 NBA AI Prop Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Clean dashboard for player prop projections, Over/Under recommendations, and best bets</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Props</div><div class="metric-value">{len(results_df)}</div></div>', unsafe_allow_html=True)

with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Strong Picks</div><div class="metric-value">{len(strong_df)}</div></div>', unsafe_allow_html=True)

with m3:
    over_count = len(results_df[results_df["Pick"] == "Over"])
    st.markdown(f'<div class="metric-card"><div class="metric-label">Over Picks</div><div class="metric-value">{over_count}</div></div>', unsafe_allow_html=True)

with m4:
    under_count = len(results_df[results_df["Pick"] == "Under"])
    st.markdown(f'<div class="metric-card"><div class="metric-label">Under Picks</div><div class="metric-value">{under_count}</div></div>', unsafe_allow_html=True)

st.divider()

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard",
    "🔍 Player Lookup",
    "🔥 Best Bets",
    "📊 Data Explorer",
    "🧠 Model Logic",
    "📌 Project Summary"
])

# -----------------------------
# DASHBOARD
# -----------------------------
with tab1:
    st.header("🏠 Dashboard")

    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Top 10 Ranked Props")
        st.dataframe(
            results_df[[
                "Player", "Team", "Prop Type", "Line", "Pick",
                "Projected Stat", "Edge", "Confidence", "Rating"
            ]].head(10),
            width="stretch"
        )

    with c2:
        st.subheader("Pick Breakdown")
        st.bar_chart(results_df["Pick"].value_counts())

        st.subheader("Rating Breakdown")
        st.bar_chart(results_df["Rating"].value_counts())

    st.subheader("Best Overall Pick")

    best = results_df.iloc[0]

    if best["Pick"] == "Over":
        st.success(f"✅ {best['Player']} {best['Prop Type']} OVER {best['Line']}")
    else:
        st.error(f"🔻 {best['Player']} {best['Prop Type']} UNDER {best['Line']}")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Projected Stat", best["Projected Stat"])
    b2.metric("Edge", best["Edge"])
    b3.metric("Confidence", f"{best['Confidence']}%")
    b4.metric("Rating", best["Rating"])

# -----------------------------
# PLAYER LOOKUP
# -----------------------------
with tab2:
    st.header("🔍 Player Lookup")

    players = sorted(df["Player"].dropna().unique())
    selected_player = st.selectbox("Select Player", players)

    player_df = df[df["Player"] == selected_player]
    prop_types = sorted(player_df["Prop_Type"].dropna().unique())
    selected_prop = st.selectbox("Select Prop Type", prop_types)

    row = player_df[player_df["Prop_Type"] == selected_prop].iloc[0]
    output = predict_row(row)

    st.subheader("Player Data")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Line", output["Line"])
    p2.metric("Season Avg", round(safe_float(row["Season_Avg"]), 2))
    p3.metric("Playoff Avg", round(safe_float(row["Playoff_Avg"]), 2))
    p4.metric("Last 5 Avg", round(safe_float(row["Last5_Playoff_Avg"]), 2))

    p5, p6, p7, p8 = st.columns(4)
    p5.metric("Last 3 Avg", round(safe_float(row["Last3_Playoff_Avg"]), 2))
    p6.metric("Playoff Min", round(safe_float(row["Playoff_Min"]), 1))
    p7.metric("Last 5 Min", round(safe_float(row["Last5_Min"]), 1))
    p8.metric("Projected Stat", output["Projected Stat"])

    st.subheader("Average Comparison Chart")

    chart_df = pd.DataFrame({
        "Metric": [
            "Season Avg",
            "Playoff Avg",
            "Last 5 Avg",
            "Last 3 Avg",
            "Line",
            "Projection"
        ],
        "Value": [
            safe_float(row["Season_Avg"]),
            safe_float(row["Playoff_Avg"]),
            safe_float(row["Last5_Playoff_Avg"]),
            safe_float(row["Last3_Playoff_Avg"]),
            output["Line"],
            output["Projected Stat"]
        ]
    })

    st.bar_chart(chart_df.set_index("Metric"))

    if st.button("Generate AI Prediction", type="primary", width="stretch"):
        if output["Pick"] == "Over":
            st.success(f"✅ {selected_player} {selected_prop} OVER {output['Line']}")
        else:
            st.error(f"🔻 {selected_player} {selected_prop} UNDER {output['Line']}")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Projected Stat", output["Projected Stat"])
        r2.metric("Edge", output["Edge"])
        r3.metric("Confidence", f"{output['Confidence']}%")
        r4.metric("Rating", output["Rating"])

        st.code(output["Explanation"], language="text")

# -----------------------------
# BEST BETS
# -----------------------------
with tab3:
    st.header("🔥 Best Bets")

    filter_rating = st.multiselect(
        "Filter by Rating",
        ["Strong", "Lean", "No Bet"],
        default=["Strong", "Lean"]
    )

    filter_pick = st.multiselect(
        "Filter by Pick",
        ["Over", "Under"],
        default=["Over", "Under"]
    )

    filtered = results_df[
        (results_df["Rating"].isin(filter_rating)) &
        (results_df["Pick"].isin(filter_pick))
    ]

    top_n = st.slider("Number of picks to show", 5, 50, 20)

    st.subheader("Filtered Ranked Picks")
    st.dataframe(
        filtered[[
            "Player", "Team", "Prop Type", "Line", "Pick",
            "Projected Stat", "Edge", "Confidence", "Rating"
        ]].head(top_n),
        width="stretch"
    )

    st.subheader("Truly Confident Picks")
    if len(strong_df) == 0:
        st.warning("No strong picks found.")
    else:
        st.dataframe(
            strong_df[[
                "Player", "Team", "Prop Type", "Line", "Pick",
                "Projected Stat", "Edge", "Confidence", "Rating"
            ]],
            width="stretch"
        )

# -----------------------------
# DATA EXPLORER
# -----------------------------
with tab4:
    st.header("📊 Data Explorer")

    team_filter = st.multiselect(
        "Filter by Team",
        sorted(df["Team"].dropna().unique()),
        default=sorted(df["Team"].dropna().unique())
    )

    prop_filter = st.multiselect(
        "Filter by Prop Type",
        sorted(df["Prop_Type"].dropna().unique()),
        default=sorted(df["Prop_Type"].dropna().unique())
    )

    raw_filtered = df[
        (df["Team"].isin(team_filter)) &
        (df["Prop_Type"].isin(prop_filter))
    ]

    st.dataframe(raw_filtered, width="stretch")

# -----------------------------
# MODEL LOGIC
# -----------------------------
with tab5:
    st.header("🧠 Model Logic")

    st.write("""
    The model evaluates player props using:

    - Season average
    - Playoff average
    - Last 5 playoff average
    - Last 3 playoff average
    - Minutes trend
    - Recent production trend
    - Line pressure
    - Volatility penalty

    A prop is only rated Strong when both confidence and projected edge are high.
    """)

# -----------------------------
# PROJECT SUMMARY
# -----------------------------
with tab6:
    st.header("📌 Project Summary")

    st.write("""
    This project is an AI-assisted NBA player prop prediction tool.

    The app reads a CSV file, calculates projections, compares projections against betting lines,
    recommends Over or Under, ranks the strongest picks, and explains the reasoning behind each prediction.

    It demonstrates AI-supported planning, coding, debugging, data analysis, and model refinement.
    """)
