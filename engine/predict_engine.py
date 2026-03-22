from .scoring import (
    calc_scores,
    get_teppan_threshold,
    get_buy_threshold,
    pair_score,
    select_best_hole_pattern
)


def predict(race):

    scores = calc_scores(race)
    sorted_boats = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    b1_num, s1 = sorted_boats[0]
    b2_num, s2 = sorted_boats[1]
    b3_num, s3 = sorted_boats[2]

    boat_dict = {b.number: b for b in race.boats}
    B1 = boat_dict[b1_num]
    B2 = boat_dict[b2_num]
    B3 = boat_dict[b3_num]

    pick1 = f"{b1_num}-{b2_num}-{b3_num}"
    pick2 = f"{b2_num}-{b1_num}-{b3_num}"

    teppan_th = get_teppan_threshold(race.place)
    buy_th = get_buy_threshold(race.place)

    # 相性補正
    ps_12 = pair_score(B1, B2)
    if ps_12 >= 60:
        s1 += 5
    elif ps_12 <= 30:
        s1 -= 5

    ps_23 = pair_score(B2, B3)
    if ps_23 >= 60:
        s2 += 5
    elif ps_23 <= 30:
        s2 -= 5

    label1 = "鉄板" if s1 >= teppan_th else "スルー"
    label2 = "買い" if s2 >= buy_th else "スルー"

    # 穴判定
    hole = None
    hole_score = scores.get(5, 0)
    B5 = boat_dict.get(5)

    if B5:
        if race.is_4kado_attack:
            hole_score += 20
        if race.wind_dir == "向かい風":
            hole_score += 10
        if race.water_condition == "荒れ":
            hole_score += 10
        if B5.motor_score >= 70:
            hole_score += 10
        if race.trend == "まくりデー":
            hole_score += 15

        ps_51 = pair_score(B5, B1)
        ps_52 = pair_score(B5, B2)

        if ps_51 >= 60 or ps_52 >= 60:
            hole_score += 10
        elif ps_51 <= 30:
            hole_score -= 10

        if hole_score >= 70:
            hole = select_best_hole_pattern(b1_num, b2_num, b3_num, scores)

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

        if pred["teppan"] or pred["kai"] or pred["ana"]:
            summary.append(race_output)

    summary = sorted(summary, key=lambda x: x["race_number"])
    return results, summary


def format_summary(summary):
    if len(summary) == 0:
        return "【本日買うべきレースはありません】"

    lines = ["【本日買うべきレース一覧】\n"]
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

def format_full_output(results, summary):
    lines = ["【全レース詳細】\n"]

    for r in results:
        lines.append(f"{r['race_name']} {r['race_number']}R")

        if r["teppan"]:
            lines.append(f"鉄板：{r['teppan']}")
        if r["kai"]:
            lines.append(f"買い：{r['kai']}")
        if r["suru"]:
            lines.append(f"スルー：{', '.join(r['suru'])}")
        if r["ana"]:
            lines.append(f"穴：{r['ana']}")

        lines.append("")

    # 最後に買うべきレース一覧
    lines.append("【買うべきレース一覧】\n")
    if len(summary) == 0:
        lines.append("本日買うべきレースはありません")
    else:
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

