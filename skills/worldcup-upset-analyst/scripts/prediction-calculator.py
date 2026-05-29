#!/usr/bin/env python3
"""
World Cup Upset Prediction Calculator

This script implements all 4 models from the worldcup-upset-analyst skill.
It reads data from the assets/ directory and outputs predictions.

Usage:
    python prediction-calculator.py predict --team-a Japan --team-b Germany --year 2026 --stage group
    python prediction-calculator.py batch --file matches.csv
    python prediction-calculator.py backtest
"""

import json
import math
import os
import argparse
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"


def load_json(filename):
    with open(ASSETS_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data():
    return {
        "matches_2014": load_json("matches-2014.json"),
        "matches_2018": load_json("matches-2018.json"),
        "matches_2022": load_json("matches-2022.json"),
        "rankings": load_json("rankings.json"),
        "upset_defs": load_json("upset-definitions.json"),
        "format_rules": load_json("format-rules.json"),
        "model_params": load_json("model-parameters.json"),
    }


def ranking_gap_model(rank_lower, rank_higher, params):
    """Model 1: Ranking Gap / Elo-Style Probability"""
    gap = rank_lower - rank_higher
    k = params["ranking_gap_model"]["k"]
    threshold = params["ranking_gap_model"]["threshold"]
    prob = 1.0 / (1.0 + math.exp(-k * (gap - threshold)))
    return {"probability": prob, "gap": gap, "formula": f"P = 1/(1+e^(-{k}*({gap}-{threshold})))"}


def logistic_regression(factors, params):
    """Model 2: Multi-Factor Logistic Regression"""
    lr = params["logistic_regression"]
    logit = lr["intercept"]
    active_factors = []
    for factor_name, coefficient in lr["coefficients"].items():
        value = factors.get(factor_name, 0)
        logit += value * coefficient
        if value != 0:
            active_factors.append(f"{factor_name}={value}")
    prob = 1.0 / (1.0 + math.exp(-logit))
    return {"probability": prob, "logit": logit, "active_factors": active_factors}


def rule_based_engine(match_context, params):
    """Model 3: Rule-Based Inference Engine"""
    base_rate = params["rule_based_engine"]["base_upset_rate"]
    rules = params["rule_based_engine"]["rules"]

    prob = base_rate
    active_rules = []

    for rule in rules:
        condition_met = evaluate_rule(rule, match_context)
        if condition_met:
            prob += rule["probability_boost"]
            active_rules.append({
                "id": rule["id"],
                "name_cn": rule["name_cn"],
                "name_en": rule["name_en"],
                "boost": rule["probability_boost"]
            })

    prob = max(0.05, min(0.95, prob))
    return {"probability": prob, "base_rate": base_rate, "active_rules": active_rules}


def evaluate_rule(rule, context):
    """Evaluate whether a rule condition is met based on match context."""
    rule_id = rule["id"]

    if rule_id == "defending_champion_curse":
        return context.get("is_defending_champion", False) and context.get("stage") == "group"

    elif rule_id == "asian_rise":
        return (context.get("lower_ranked_confederation") == "AFC"
                and context.get("higher_ranked_rank", 999) <= 10
                and context.get("stage") == "group")

    elif rule_id == "five_sub_effect":
        return context.get("year", 0) >= 2022 and context.get("underdog_has_depth", False)

    elif rule_id == "cluster_effect":
        return context.get("same_group_prior_upset", False)

    elif rule_id == "home_continent_advantage":
        return (context.get("is_home_continent", False)
                and context.get("strong_football_tradition", False))

    elif rule_id == "knockout_stability":
        return context.get("stage") in ("round_of_16", "quarter_final", "semi_final", "final", "third_place")

    elif rule_id == "var_effect":
        return context.get("year", 0) >= 2018 and context.get("stage") == "group"

    return False


def trend_extrapolation(year, params):
    """Model 4: Trend Extrapolation"""
    trend = params["trend_extrapolation"]
    year_index = {"2014": 0, "2018": 1, "2022": 2}.get(str(year), None)

    if year_index is not None:
        # Historical year -> return actual count
        count = trend["historical_counts"].get(str(year), 0)
        rate = count / 64  # 64 matches per tournament
        return {"projected_upsets": count, "upset_rate": rate, "type": "historical"}

    if str(year) == "2026":
        base = trend["base_2026_projection"]
        adj = trend["adjusted_2026_projection"]
        ci = trend["confidence_interval"]
        return {
            "projected_upsets": adj,
            "base_projection": base,
            "confidence_interval": ci,
            "upset_rate": adj / 104,  # 104 matches in 2026
            "type": "projection",
            "adjustments": trend["2026_adjustments"]
        }

    # Generic formula for any other year
    # Map year to index: 2014=0, 2018=1, 2022=2, 2026=3, 2030=4, etc.
    idx = (int(year) - 2014) // 4
    slope = trend["linear_regression"]["slope"]
    intercept = trend["linear_regression"]["intercept"]
    count = slope * idx + intercept
    return {"projected_upsets": count, "type": "extrapolation"}


def ensemble_consensus(model_results, params):
    """Combine all 4 models with calibrated weights."""
    weights = params["model_ensemble_weights"]

    weighted_sum = 0
    total_weight = 0
    breakdown = {}

    mapping = {
        "ranking_gap": "ranking_gap_model",
        "logistic": "logistic_regression",
        "rule_based": "rule_based_engine",
        "trend": "trend_extrapolation",
    }

    for key, model_key in mapping.items():
        if key in model_results:
            weight = weights[model_key]
            prob = model_results[key].get("probability",
                   model_results[key].get("projected_upsets", 0) / 104 if key == "trend" else 0)

            if key == "trend":
                # Convert upset count to probability
                total_matches = 104 if str(model_results[key].get("year", 2026)) == "2026" else 64
                prob = model_results[key].get("projected_upsets", 0) / total_matches

            weighted_sum += weight * prob
            total_weight += weight
            breakdown[key] = {
                "weight": weight,
                "probability": prob,
                "contribution": weight * prob
            }

    consensus = weighted_sum / total_weight if total_weight > 0 else 0
    return {"consensus_probability": consensus, "breakdown": breakdown}


def predict_match(team_a, team_b, year, stage, data):
    """Full prediction pipeline for a single match."""
    rankings = data["rankings"]["rankings"]
    params = data["model_params"]

    # Get rankings for the given year (fallback to 2026_estimated if needed)
    year_key = str(year) if str(year) in rankings else "2026_estimated"
    year_rankings = rankings.get(year_key, rankings["2026_estimated"])

    # Look up team rankings
    rank_a = year_rankings.get(team_a, 50)
    rank_b = year_rankings.get(team_b, 50)

    # Determine higher/lower ranked team and gap
    if rank_a < rank_b:
        higher_ranked, lower_ranked = team_a, team_b
        higher_rank, lower_rank = rank_a, rank_b
    else:
        higher_ranked, lower_ranked = team_b, team_a
        higher_rank, lower_rank = rank_b, rank_a

    gap = lower_rank - higher_rank

    # Determine confederation
    conf_map = data["rankings"]["confederation_map"]
    conf_a = next((c for c, teams in conf_map.items() if team_a in teams), "UEFA")
    conf_b = next((c for c, teams in conf_map.items() if team_b in teams), "UEFA")

    # Build match context
    match_context = {
        "stage": stage,
        "year": year,
        "is_defending_champion": False,  # Would need to know who defending champion is
        "lower_ranked_confederation": conf_b if rank_b > rank_a else conf_a,
        "higher_ranked_rank": higher_rank,
        "lower_rank": lower_rank,
        "higher_rank": higher_rank,
        "gap": gap,
        "underdog_has_depth": True,  # Conservative default
        "same_group_prior_upset": False,  # Would need tournament context
        "is_home_continent": False,  # Would need to know host
        "strong_football_tradition": False,
    }

    # Model 1: Ranking Gap
    m1 = ranking_gap_model(lower_rank, higher_rank, params)

    # Model 2: Logistic Regression
    factors = {
        "ranking_gap": gap,
        "is_group_stage": 1.0 if stage == "group" else 0.0,
        "is_defending_champion": 0.0,  # Simplified
        "is_5_sub_era": 1.0 if year >= 2022 else 0.0,
        "is_home_continent": 0.0,
        "year_trend": {"2014": 0, "2018": 1, "2022": 2}.get(str(year), 3),
        "cluster_effect": 0.0,
    }
    m2 = logistic_regression(factors, params)

    # Model 3: Rule-Based
    m3 = rule_based_engine(match_context, params)

    # Model 4: Trend
    m4 = trend_extrapolation(year, params)

    results = {
        "ranking_gap": {**m1, "year": year},
        "logistic": {**m2, "year": year},
        "rule_based": {**m3, "year": year},
        "trend": {**m4, "year": year},
    }

    consensus = ensemble_consensus(results, params)

    return {
        "match": f"{team_a} vs {team_b}",
        "year": year,
        "stage": stage,
        "rankings": {team_a: rank_a, team_b: rank_b},
        "gap": gap,
        "models": results,
        "consensus": consensus
    }


def main():
    parser = argparse.ArgumentParser(description="World Cup Upset Prediction Calculator")
    subparsers = parser.add_subparsers(dest="command")

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Predict upset probability for a match")
    predict_parser.add_argument("--team-a", required=True)
    predict_parser.add_argument("--team-b", required=True)
    predict_parser.add_argument("--year", type=int, default=2026)
    predict_parser.add_argument("--stage", default="group", choices=["group", "round_of_16", "quarter_final", "semi_final", "final", "third_place"])

    # Backtest command
    subparsers.add_parser("backtest", help="Run historical backtest on all 192 matches")

    args = parser.parse_args()
    data = load_all_data()

    if args.command == "predict":
        result = predict_match(args.team_a, args.team_b, args.year, args.stage, data)

        print(f"\n{'='*60}")
        print(f"Upset Analysis: {result['match']}")
        print(f"Tournament: {result['year']} World Cup - {result['stage']}")
        print(f"Rankings: {result['rankings']}")
        print(f"Ranking Gap: {result['gap']} positions")
        print(f"{'='*60}")

        print(f"\nModel Breakdown:")
        for model_name, model_result in result['models'].items():
            if model_name == 'trend':
                print(f"  {model_name}: {model_result.get('projected_upsets', 'N/A')} upsets projected")
            else:
                print(f"  {model_name}: {model_result['probability']*100:.1f}%")

        print(f"\nConsensus Upset Probability: {result['consensus']['consensus_probability']*100:.1f}%")
        print(f"Breakdown:")
        for model_name, breakdown in result['consensus']['breakdown'].items():
            print(f"  {model_name}: weight={breakdown['weight']}, prob={breakdown['probability']*100:.1f}%, contrib={breakdown['contribution']*100:.2f}%")

    elif args.command == "backtest":
        print("Running backtest on 192 matches...")
        all_matches = data["matches_2014"] + data["matches_2018"] + data["matches_2022"]

        correct = 0
        total = 0
        upset_correct = 0
        upset_total = 0

        for match in all_matches:
            if match["is_draw"]:
                continue  # Skip draws for this simple accuracy check

            team_a, team_b = match["team_a"], match["team_b"]
            year = match["match_id"].split("-")[0]

            result = predict_match(team_a, team_b, int(year), match["stage"], data)
            prob = result["consensus"]["consensus_probability"]

            lower_ranked = team_a if match["rank_a"] > match["rank_b"] else team_b
            actual_winner = match["winner"]

            if prob > 0.5:
                predicted_upset = True
            else:
                predicted_upset = False

            actual_upset = match["is_upset"]

            if predicted_upset == actual_upset:
                correct += 1
            total += 1

            if actual_upset:
                upset_total += 1
                if predicted_upset:
                    upset_correct += 1

        print(f"\nBacktest Results (192 matches, excluding draws):")
        print(f"  Overall accuracy: {correct}/{total} = {correct/total*100:.1f}%")
        print(f"  Upset detection rate: {upset_correct}/{upset_total} = {upset_correct/upset_total*100:.1f}%")


if __name__ == "__main__":
    main()
