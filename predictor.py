def clamp(value, low, high):
    return max(low, min(high, value))


def predict_prop(
    player,
    prop_type,
    line,
    season_avg,
    last10_avg,
    last5_avg,
    minutes_score,
    usage_score,
    matchup_score,
    pace_score,
    roster_score,
    schedule_score,
    market_score,
    volatility_score
):
    line = float(line)

    season_avg = float(season_avg)
    last10_avg = float(last10_avg)
    last5_avg = float(last5_avg)

    minutes_score = float(minutes_score)
    usage_score = float(usage_score)
    matchup_score = float(matchup_score)
    pace_score = float(pace_score)
    roster_score = float(roster_score)
    schedule_score = float(schedule_score)
    market_score = float(market_score)
    volatility_score = float(volatility_score)

    base_projection = (
        season_avg * 0.30 +
        last10_avg * 0.30 +
        last5_avg * 0.40
    )

    factor_score = (
        minutes_score * 0.20 +
        usage_score * 0.18 +
        roster_score * 0.14 +
        matchup_score * 0.14 +
        pace_score * 0.10 +
        schedule_score * 0.06 +
        market_score * 0.08 +
        volatility_score * 0.10
    )

    adjustment = 1 + ((factor_score - 50) / 200)

    projected_stat = base_projection * adjustment

    difference = projected_stat - line

    pick = "Over" if difference > 0 else "Under"

    if line <= 0:
        edge = 0
    else:
        edge = abs(difference / line) * 100

    confidence = clamp(50 + edge, 50, 95)

    explanation = f"""
Player: {player}
Prop Type: {prop_type}
Line: {line}

Season Average: {season_avg}
Playoff / Last 10 Average: {last10_avg}
Last 5 Average: {last5_avg}

Overall Factor Score: {factor_score:.1f}/100
Projected Stat: {projected_stat:.2f}

Recommendation: {pick}
Confidence: {confidence:.1f}%

Explanation:
The model recommends the {pick} because the projected stat is {projected_stat:.2f}
compared to the line of {line}. The model uses recent performance, season average,
projected minutes, usage, matchup, pace, roster/injury context, schedule, market value,
and volatility.

This is an AI-assisted prediction model, not guaranteed betting advice.
"""

    return explanation
