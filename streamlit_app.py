import streamlit as st
import pandas as pd
import statistics

st.set_page_config(
    page_title="NBA AI Prop Predictor",
    page_icon="🏀",
    layout="wide"
)

CSV_FILE = "nba_props_data.csv"

st.title("🏀 NBA AI Prop Predictor")
st.subheader("Strict CSV-powered Over/Under model for Knicks vs Spurs props")
st.caption("This stricter version only highlights truly confident prop edges.")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_FILE, encoding="latin1")
    df["Line"] = pd.to_numeric(df["Line"], errors="coerce")
    df = df[df["Line"] > 0]
    return df

df = load_data()

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
    last3_min = safe_float(row["Last3_Min"])

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

    # stricter confidence model
    confidence = 50
    confidence += edge_percent * 0.55
    confidence -= volatility * 1.25

    # punish tiny edges
    if edge < 0.75:
        confidence -= 8
    elif edge < 1.25:
        confidence -= 4

    # high-variance props need bigger edge
    if str(prop_type).lower() in ["assists", "rebounds"]:
        confidence -= 2

    confidence = clamp(confidence, 50, 92)

    # stricter rating thresholds
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

This stricter version lowers confidence unless the model finds a clear gap between
the projection and the line. It also penalizes volatility, small edges, and props
that are naturally harder to predict. Strong picks require both high confidence
and a meaningful numerical edge.

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

tab1, tab2, tab3 = st.tabs([
    "🔍 Player Lookup",
    "🔥 Best Bets",
    "🧠 How It Works"
])

with tab1:
    st.header("🔍 Player Lookup")

    players = sorted(df["Player"].dropna().unique())
    selected_player = st.selectbox("Select Player", players)

    player_df = df[df["Player"] == selected_player]
    prop_types = sorted(player_df["Prop_Type"].dropna().unique())
    selected_prop = st.selectbox("Select Prop Type", prop_types)

    row = player_df[player_df["Prop_Type"] == selected_prop].iloc[0]
    output = predict_row(row)

    st.subheader("Auto-Loaded Data")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Line", output["Line"])
    c2.metric("Season Avg", round(safe_float(row["Season_Avg"]), 2))
    c3.metric("Playoff Avg", round(safe_float(row["Playoff_Avg"]), 2))
    c4.metric("Last 5 Avg", round(safe_float(row["Last5_Playoff_Avg"]), 2))

    if st.button("Generate AI Prediction", type="primary", use_container_width=True):
        if output["Pick"] == "Over":
            st.success(f"✅ {selected_player} {selected_prop} OVER {output['Line']}")
        else:
            st.error(f"🔻 {selected_player} {selected_prop} UNDER {output['Line']}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Projected Stat", output["Projected Stat"])
        m2.metric("Edge", output["Edge"])
        m3.metric("Confidence", f"{output['Confidence']}%")
        m4.metric("Rating", output["Rating"])

        st.code(output["Explanation"], language="text")

with tab2:
    st.header("🔥 AI Best Bets")

    results = []
    for _, row in df.iterrows():
        try:
            results.append(predict_row(row))
        except:
            pass

    results_df = pd.DataFrame(results)

    strong_df = results_df[results_df["Rating"] == "Strong"].sort_values(
        by=["Confidence", "Edge"],
        ascending=False
    )

    lean_df = results_df[results_df["Rating"] == "Lean"].sort_values(
        by=["Confidence", "Edge"],
        ascending=False
    )

    st.subheader("Truly Confident Picks")
    if len(strong_df) == 0:
        st.warning("No Strong picks found. The model does not see any high-confidence edges.")
    else:
        st.dataframe(
            strong_df[[
                "Player",
                "Team",
                "Prop Type",
                "Line",
                "Pick",
                "Projected Stat",
                "Edge",
                "Confidence",
                "Rating"
            ]],
            use_container_width=True
        )

        best = strong_df.iloc[0]

        st.subheader("Best Overall Pick")
        if best["Pick"] == "Over":
            st.success(f"✅ {best['Player']} {best['Prop Type']} OVER {best['Line']}")
        else:
            st.error(f"🔻 {best['Player']} {best['Prop Type']} UNDER {best['Line']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projected Stat", best["Projected Stat"])
        c2.metric("Edge", best["Edge"])
        c3.metric("Confidence", f"{best['Confidence']}%")
        c4.metric("Rating", best["Rating"])

        st.code(best["Explanation"], language="text")

    st.subheader("Lean Picks")
    st.dataframe(
        lean_df[[
            "Player",
            "Team",
            "Prop Type",
            "Line",
            "Pick",
            "Projected Stat",
            "Edge",
            "Confidence",
            "Rating"
        ]],
        use_container_width=True
    )

    st.subheader("Pick Breakdown")
    st.write(results_df["Rating"].value_counts())

with tab3:
    st.header("🧠 How It Works")

    st.write("""
    This stricter version is designed to avoid showing too many high-confidence picks.

    Improvements:

    - Confidence grows slower
    - Volatility is punished harder
    - Small edges are downgraded
    - Strong picks require both confidence and edge
    - Best Bets only highlights truly confident plays

    Strong Pick Requirements:

    - Confidence must be at least 68%
    - Edge must be at least 2.0 units

    Lean Pick Requirements:

    - Confidence must be at least 58%
    - Edge must be at least 1.25 units

    Everything else is treated as No Bet.
    """)

    st.info("For class, explain that the model became stricter after testing because the first version produced too many high-confidence recommendations.")
