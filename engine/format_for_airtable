import json
from datetime import date

def format_for_airtable(race, pred, eval_result):
    """
    Airtable に保存するための統一フォーマット（強化版）
    """

    # 回収金額（的中時のみ）
    return_main = eval_result["odds_main"] * 100 if eval_result["main_hit"] else 0
    return_ana = eval_result["odds_ana"] * 100 if eval_result["ana_hit"] else 0

    return {
        # ===== 基本情報 =====
        "date": str(date.today()),
        "place": race.place,
        "race_number": race.number,

        # ===== 予想 =====
        "main": pred["main"],
        "ana": pred["ana"],
        "ev_main": pred["ev_main"],
        "ev_ana": pred["ev_ana"],

        # ===== 結果 =====
        "result": eval_result["result"],
        "main_hit": eval_result["main_hit"],
        "ana_hit": eval_result["ana_hit"],

        # ===== オッズ・回収 =====
        "odds_main": eval_result["odds_main"],
        "odds_ana": eval_result["odds_ana"],
        "bet_main": eval_result["bet_main"] * 100,  # 100円固定
        "bet_ana": eval_result["bet_ana"] * 100,
        "return_main": return_main,
        "return_ana": return_ana,

        # ===== EVギャップ（改善点） =====
        "ev_gap_main": eval_result["ev_gap_main"],
        "ev_gap_ana": eval_result["ev_gap_ana"],

        # ===== 気象・水面 =====
        "weather": race.weather,
        "wind_dir": race.wind_dir,
        "wind_power": race.wind_power,
        "water_condition": race.water_condition,
        "trend": race.trend,
        "is_4kado_attack": race.is_4kado_attack,

        # ===== スコア（JSON文字列として保存） =====
        "scores": json.dumps(pred["scores"], ensure_ascii=False),

        # ===== バージョン管理 =====
        "version": "v2.1-EV-Enhanced"
    }
