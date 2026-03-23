import json
import math
from engine.scoring import score_boat

# ===== パラメータ読み込み =====
with open("params.json", "r", encoding="utf-8") as f:
    PARAMS = json.load(f)

PLACE_ADJ = PARAMS["place_adj"]
HOLE_ADJ = PARAMS["hole_adj"]
OUTER_MUL = {int(k): v for k, v in PARAMS["outer_multiplier"].items()}

MAIN_TH_BASE = PARAMS["main_th_base"]
ANA_TH_BASE  = PARAMS["ana_th_base"]

ODDS_BY_RANK = {1: 1.8, 2: 2.5, 3: 4.0, 4: 8.0, 5: 15.0, 6: 30.0}


# ===== Softmax（安全版）=====
def softmax(scores: dict[int, float], temperature: float = 15.0) -> dict[int, float]:
    max_v = max(scores.values())
    exps = {k: math.exp((v - max_v) / temperature) for k, v in scores.items()}
    total = sum(exps.values())
    if total <= 0:
        n = len(scores)
        return {k: 1 / n for k in scores}
    return {k: v / total for k, v in exps.items()}


# ===== 単艇EV =====
def single_ev(prob: float, rank: int) -> float:
    return prob * ODDS_BY_RANK.get(rank, 10.0)


# ===== 3連単EV（条件付き確率）=====
def trifecta_ev(pattern: tuple[int, int, int],
                probs: dict[int, float],
                trifecta_odds: float) -> float:
    b1, b2, b3 = pattern

    p1 = probs[b1]

    rem1 = {k: v for k, v in probs.items() if k != b1}
    s1 = sum(rem1.values())
    if s1 <= 0:
        return 0.0
    p2 = rem1[b2] / s1

    rem2 = {k: v for k, v in rem1.items() if k != b2}
    s2 = sum(rem2.values())
    if s2 <= 0:
        return 0.0
    p3 = rem2[b3] / s2

    return p1 * p2 * p3 * trifecta_odds


# ===== 3連単オッズ推定（弱め）=====
def estimate_trifecta_odds(pattern: tuple[int, int, int],
                           rank_map: dict[int, int]) -> float:
    o1 = ODDS_BY_RANK.get(rank_map.get(pattern[0], 6), 30.0)
    o2 = ODDS_BY_RANK.get(rank_map.get(pattern[1], 6), 30.0)
    o3 = ODDS_BY_RANK.get(rank_map.get(pattern[2], 6), 30.0)
    return o1 * o2 * o3 * 0.15


def predict(race) -> dict:
    """
    回収率重視＋本線的中率を少し底上げした2点最適化モデル（完全版）
    """

    # ===== スコア =====
    scores: dict[int, float] = {
        i: score_boat(race.place, race.number, i) for i in range(1, 7)
    }
    probs = softmax(scores)

    sorted_boats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    b1, b2, b3 = [x[0] for x in sorted_boats[:3]]
    s1, s2, s3 = scores[b1], scores[b2], scores[b3]
    rank_map: dict[int, int] = {boat: i + 1 for i, (boat, _) in enumerate(sorted_boats)}

    # ===== 場補正 =====
    cfg = PLACE_ADJ.get(race.place, {"main_adj": 0, "ana_adj": 0})
    main_adj: int = cfg["main_adj"]
    ana_adj: int = cfg["ana_adj"]

    wind = getattr(race, "wind_dir", "")
    water = getattr(race, "water_condition", "")
    trend = getattr(race, "trend", "")
    boats = getattr(race, "boats", [])

    # ===== 本線 =====
    main = None
    ev_main = 0.0

    main_th = MAIN_TH_BASE + main_adj
    if wind == "追い風":
        main_th -= 3
    if water == "安定":
        main_th -= 2

    # ★ 本線の当たりやすさを少し強化
    if s1 >= (main_th - 2) and (s1 - s2) >= 4:
        p = (b1, b2, b3)
        ev = trifecta_ev(p, probs, estimate_trifecta_odds(p, rank_map))
        if ev >= 0.02:
            main = f"{b1}-{b2}-{b3}"
            ev_main = ev

    # ===== 対抗 =====
    alt = None
    if main is None and (s2 - s3) >= 5:
        p = (b1, b3, b2)
        ev = trifecta_ev(p, probs, estimate_trifecta_odds(p, rank_map))
        if ev >= 0.02:
            alt = f"{b1}-{b3}-{b2}"
            ev_main = ev

    # ===== 穴補正後の再Softmax =====
    hole_scores: dict[int, float] = dict(scores)

    for num in [4, 5, 6]:
        h = scores[num]

        if num == 4 and getattr(race, "is_4kado_attack", False):
            h += HOLE_ADJ["base"]
        if wind == "向かい風":
            h += HOLE_ADJ["wind"]
        if water == "荒れ":
            h += HOLE_ADJ["water"]
        if trend == "まくりデー":
            h += HOLE_ADJ["trend"]

        boat_obj = next((b for b in boats if getattr(b, "number", None) == num), None)
        if boat_obj and getattr(boat_obj, "motor_score", 0) >= 70:
            h += HOLE_ADJ["motor"]

        h *= OUTER_MUL.get(num, 1.0)
        hole_scores[num] = h

    hole_probs = softmax(hole_scores)
    hole_sorted = sorted(hole_scores.items(), key=lambda x: x[1], reverse=True)
    hole_rank_map: dict[int, int] = {boat: i + 1 for i, (boat, _) in enumerate(hole_sorted)}

    # ===== 穴艇選定 =====
    hole = None
    best_ev = 0.0
    ana_th = ANA_TH_BASE + (ana_adj / 20)

    for num in [4, 5, 6]:
        ev = single_ev(hole_probs[num], hole_rank_map[num])
        if ev >= ana_th and ev > best_ev:
            best_ev = ev
            hole = num

    # ===== 穴買い目（3パターン比較）=====
    ana = None
    ev_ana = 0.0

    if hole is not None:
        patterns = [
            (b1, b2, hole),
            (b1, hole, b2),
            (b2, b1, hole),
        ]
        for p in patterns:
            ev = trifecta_ev(p, hole_probs, estimate_trifecta_odds(p, hole_rank_map))
            if ev > ev_ana:
                ev_ana = ev
                ana = f"{p[0]}-{p[1]}-{p[2]}"

    return {
        "main": main or alt,
        "ana": ana,
        "ev_main": round(ev_main, 4) if (main or alt) else None,
        "ev_ana": round(ev_ana, 4) if ana else None,
        "scores": scores,
        "probs": {k: round(v, 4) for k, v in hole_probs.items()},
    }
