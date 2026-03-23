import json
from datetime import date


def format_for_airtable(race, pred, eval_result):
    """
    Airtable に保存するための統一フォーマット（最終完成版）
    """

    # ===== 回収 =====
    return_main = eval_result["return_main"]
    return_ana = eval_result["return_ana"]

    total_bet = eval_result["total_bet"]
    total_return = eval_result["total_return"]

    # ===== スコア順位 =====
    scores = pred.get("scores", {})
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    rank1 = sorted_scores[0][0] if len(sorted_scores) > 0 else None
    rank2 = sorted_scores[1][0] if len(sorted_scores) > 1 else None
    rank3 = sorted_scores[2][0] if len(sorted_scores) > 2 else None

    return {
        # ===== 基本 =====
        "date": str(date.today()),
        "place": race.place,
        "race_number": race.number,

        # ===== 予想 =====
        "main": pred.get("main"),
        "ana": pred.get("ana"),
        "ev_main": pred.get("ev_main"),
        "ev_ana": pred.get("ev_ana"),

        # ===== 結果 =====
        "result": eval_result["result"],
        "main_hit": eval_result["main_hit"],
        "ana_hit": eval_result["ana_hit"],

        # ===== オッズ =====
        "odds_main": eval_result["odds_main"],
        "odds_ana": eval_result["odds_ana"],

        # ===== 投資 =====
        "bet_main": eval_result["bet_main"] * 100,
        "bet_ana": eval_result["bet_ana"] * 100,
        "total_bet": total_bet,

        # ===== 回収 =====
        "return_main": return_main,
        "return_ana": return_ana,
        "total_return": total_return,

        # ===== フラグ =====
        "is_bet": eval_result["is_bet"],  # ← evaluator と完全一致

        # ===== EV分析 =====
        "ev_gap_main": eval_result.get("ev_gap_main"),
        "ev_gap_ana": eval_result.get("ev_gap_ana"),

        # ===== 気象 =====
        "weather": race.weather,
        "wind_dir": race.wind_dir,
        "wind_power": race.wind_power,
        "water_condition": race.water_condition,
        "trend": race.trend,
        "is_4kado_attack": race.is_4kado_attack,

        # ===== スコア =====
        "scores": json.dumps(scores, ensure_ascii=False),
        "rank1": rank1,
        "rank2": rank2,
        "rank3": rank3,

        # ===== バージョン =====
        "version": "v2.2-EV-Final",
        "ev_threshold": 1.2
    }
