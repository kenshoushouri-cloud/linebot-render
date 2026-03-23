from datetime import date

from .scoring import (
    calc_scores,
    pair_score,
    select_best_hole_pattern
)

# ===== 競艇場補正 =====
PLACE_CONFIG = {
    "大村":  {"teppan": -5, "buy": -3, "ana": -10},
    "下関":  {"teppan": 0,  "buy": 0,  "ana": 0},
    "徳山":  {"teppan": +3, "buy": +2, "ana": +5},
    "芦屋":  {"teppan": +2, "buy": +2, "ana": +5},
    "唐津":  {"teppan": +4, "buy": +3, "ana": +7},
    "平和島": {"teppan": +6, "buy": +4, "ana": +10},
    "江戸川": {"teppan": +8, "buy": +5, "ana": +15},
}

BASE_TEPPAN_TH = 75
BASE_BUY_TH = 65

# ===== 擬似オッズ（超重要） =====
def pseudo_odds_by_rank(rank):
    table = {
        1: 1.8,
        2: 2.5,
        3: 4.0,
        4: 8.0,
        5: 15.0,
        6: 30.0
    }
    return table.get(rank, 10.0)


def score_to_prob(score):
    """スコア → 的中率（簡易変換）"""
    return min(max(score / 100, 0.05), 0.9)


def calc_ev(score, rank):
    prob = score_to_prob(score)
    odds = pseudo_odds_by_rank(rank)
    return prob * odds


def apply_pair_adjust(base_score, pair_score_val):
    return base_score * (1 + (pair_score_val - 50) / 200)


def get_thresholds(race):
    cfg = PLACE_CONFIG.get(race.place, {"teppan": 0, "buy": 0, "ana": 0})

    teppan_th = BASE_TEPPAN_TH + cfg["teppan"]
    buy_th = BASE_BUY_TH + cfg["buy"]
    ana_th = 70 + cfg["ana"]

    if race.trend == "荒れ":
        teppan_th += 5
        buy_th += 3
    elif race.trend == "安定":
        teppan_th -= 3

    return teppan_th, buy_th, ana_th


def predict(race):
    scores = calc_scores(race)
    sorted_boats = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 順位マップ
    rank_map = {boat: i+1 for i, (boat, _) in enumerate(sorted_boats)}

    top = sorted_boats[:4]
    b1, s1 = top[0]

    # ===== 対抗 =====
    kai = None
    ev2 = calc_ev(s2, rank_map[b2])

    if s2 >= buy_th and ev2 >= 1.0:
        kai = f"{b1}-{b3}-{b2}"

    # ===== 穴（EV重視） =====
    hole = None
    best_ev = 0

    for num in [4, 5, 6]:
        B = boat_dict.get(num)
        if not B:
            continue

        h_score = scores.get(num, 0)

        # 展開加点
        if num == 4 and race.is_4kado_attack:
            h_score += 20
        if race.wind_dir == "向かい風":
            h_score += 10
        if race.water_condition == "荒れ":
            h_score += 10
        if race.trend == "まくりデー":
            h_score += 15

        if B.motor_score >= 70:
            h_score += 10

        ps1 = pair_score(B, B1)
        ps2 = pair_score(B, B2)

        if ps1 >= 60 or ps2 >= 60:
            h_score += 10
        elif ps1 <= 30:
            h_score -= 10

        # 重み
        if num == 4:
            h_score *= 1.1
        elif num == 5:
            h_score *= 1.2
        elif num == 6:
            h_score *= 0.9

        ev = calc_ev(h_score, rank_map.get(num, 6))

        if ev > best_ev and ev >= 1.2:
            best_ev = ev
            hole = select_best_hole_pattern(b1, b2, b3, scores)

    # ===== 最終2点 =====
    final_main = teppan or kai
    final_ana = hole

    return {
        "main": final_main,
        "ana": final_ana,
        "scores": scores,
        "ev_main": ev1 if final_main else None,
        "ev_ana": best_ev if final_ana else None
    }


def predict_all(races):
    results = []
    summary = []

    for race in races:
        pred = predict(race)

        race_output = {
            "race_name": race.place,
            "race_number": race.number,
            "main": pred["main"],
            "ana": pred["ana"],
            "ev_main": pred["ev_main"],
            "ev_ana": pred["ev_ana"],
        }

        results.append(race_output)

        if pred["main"] or pred["ana"]:
            summary.append(race_output)

    summary = sorted(summary, key=lambda x: x["race_number"])
    return results, summary


def format_summary(summary):
    if not summary:
        return "【本日買うべきレースはありません】"

    lines = ["【本日狙いレース（期待値フィルター済）】\n"]

    for r in summary:
        lines.append(f"{r['race_name']} {r['race_number']}R")

        if r["main"]:
            lines.append(f"本線：{r['main']} (EV:{round(r['ev_main'],2)})")
        if r["ana"]:
            lines.append(f"穴：{r['ana']} (EV:{round(r['ev_ana'],2)})")

        lines.append("")

    return "\n".join(lines)
