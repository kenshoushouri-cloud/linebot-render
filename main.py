# ============================================
#  A5型複合スコア算出（あなたのロジック）
# ============================================
def calc_scores(race):
    scores = {}

    for boat in race.boats:
        base = boat.motor_score + boat.tenji_score + boat.player_score
        base += race.weather_bonus(boat.number)
        base += race.trend_bonus(boat.number)
        scores[boat.number] = base

    return scores


# ============================================
#  場ごとの鉄板・買い基準（自動調整）
# ============================================
def get_teppan_threshold(place):
    strong_in = ["徳山", "芦屋", "下関", "大村"]
    weak_in = ["戸田", "江戸川", "平和島"]

    if place in strong_in:
        return 70
    if place in weak_in:
        return 80
    return 75


def get_buy_threshold(place):
    strong_in = ["徳山", "芦屋", "下関", "大村"]
    weak_in = ["戸田", "江戸川", "平和島"]

    if place in strong_in:
        return 60
    if place in weak_in:
        return 70
    return 65


# ============================================
#  穴の最適パターン選択
# ============================================
def select_best_hole_pattern(b1, b2, b3, scores):
    # 5号艇の位置ごとにスコアを評価
    patterns = {
        f"5-{b1}-{b2}": scores[5] + 15,  # 5頭
        f"{b1}-5-{b2}": scores[5] + 10,  # 2着
        f"{b1}-{b2}-5": scores[5] + 5,   # 3着
    }
    return max(patterns, key=patterns.get)


# ============================================
#  predict()（レース単体予想）
# ============================================
def predict(race):

    # STEP1：スコア算出
    scores = calc_scores(race)
    sorted_boats = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    b1, s1 = sorted_boats[0]
    b2, s2 = sorted_boats[1]
    b3, s3 = sorted_boats[2]

    # STEP2：2点固定
    pick1 = f"{b1}-{b2}-{b3}"
    pick2 = f"{b2}-{b1}-{b3}"

    # STEP3：分類
    teppan_th = get_teppan_threshold(race.place)
    buy_th = get_buy_threshold(race.place)

    label1 = "鉄板" if s1 >= teppan_th else "スルー"
    label2 = "買い" if s2 >= buy_th else "スルー"

    # STEP4：穴判定
    hole_score = scores.get(5, 0)

    if race.is_4kado_attack: hole_score += 20
    if race.wind_dir == "向かい風": hole_score += 10
    if race.water_condition == "荒れ": hole_score += 10
    if race.motor_eval[5] == "良い": hole_score += 10
    if race.tenji_eval[5] == "良い": hole_score += 10
    if race.trend == "まくりデー": hole_score += 15

    hole = None
    if hole_score >= 70:
        hole = select_best_hole_pattern(b1, b2, b3, scores)

    # STEP5：出力整形
    teppan_out = pick1 if label1 == "鉄板" else None
    kai_out = pick2 if label2 == "買い" else None

    suru_list = []
    if label1 == "スルー":
        suru_list.append(pick1)
    if label2 == "スルー":
        suru_list.append(pick2)
    suru_out = suru_list if suru_list else None

    return {
        "teppan": teppan_out,
        "kai": kai_out,
        "suru": suru_out,
        "ana": hole
    }


# ============================================
#  predict_all()（全レース → 買うべきレース一覧）
# ============================================
def predict_all(races):

    results = []
    summary = []

    for race in races:
        pred = predict(race)

        race_output = {
            "race_name": race.place,
            "race_number": race.number,
            "teppan": pred["teppan"],
            "kai": pred["kai"],
            "suru": pred["suru"],
            "ana": pred["ana"]
        }

        results.append(race_output)

        # 買うべきレースだけ抽出
        if pred["teppan"] or pred["kai"] or pred["ana"]:
            summary.append(race_output)

    # レース番号順
    summary = sorted(summary, key=lambda x: x["race_number"])

    return results, summary


# ============================================
#  まとめ表示（文章生成）
# ============================================
def format_summary(summary):

    if len(summary) == 0:
        return "【本日買うべきレースはありません】"

    lines = []
    lines.append("【本日買うべきレース一覧】\n")

    for r in summary:

        lines.append(f"{r['race_name']} {r['race_number']}R")

        if r["teppan"]:
            lines.append(f"鉄板：{r['teppan']}")

        if r["kai"]:
            lines.append(f"買い：{r['kai']}")

        if r["ana"]:
            lines.append(f"穴：{r['ana']}")

        lines.append("")

    return "\n".join(lines)
