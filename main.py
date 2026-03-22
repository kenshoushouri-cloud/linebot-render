# ============================================
#  Boatクラス（選手データ）
# ============================================
class Boat:
    def __init__(
        self,
        number,
        player_id,
        player_name,
        avg_st,
        win_rate,
        local_win_rate,
        course_stats,
        f_count,
        accident_rate,
        motor_score,
        comment,
        pair_stats
    ):
        self.number = number
        self.player_id = player_id
        self.player_name = player_name
        self.avg_st = avg_st
        self.win_rate = win_rate
        self.local_win_rate = local_win_rate
        self.course_stats = course_stats
        self.f_count = f_count
        self.accident_rate = accident_rate
        self.motor_score = motor_score
        self.comment = comment
        self.pair_stats = pair_stats


# ============================================
#  Raceクラス（レースデータ）
# ============================================
class Race:
    def __init__(
        self,
        place,
        number,
        boats,
        wind_dir,
        wind_power,
        water_condition,
        trend,
        is_4kado_attack
    ):
        self.place = place
        self.number = number
        self.boats = boats
        self.wind_dir = wind_dir
        self.wind_power = wind_power
        self.water_condition = water_condition
        self.trend = trend
        self.is_4kado_attack = is_4kado_attack


# ============================================
#  スコア計算（簡易版）
# ============================================
def calc_scores(race):
    scores = {}
    for b in race.boats:
        base = (
            b.win_rate * 10 +
            b.local_win_rate * 8 +
            (1 - b.accident_rate) * 10 +
            b.motor_score +
            (1 - b.avg_st) * 50
        )
        scores[b.number] = base
    return scores


# ============================================
#  場ごとの基準
# ============================================
def get_teppan_threshold(place):
    return 75

def get_buy_threshold(place):
    return 65


# ============================================
#  相性スコア取得
# ============================================
def pair_score(boat_a, boat_b):
    if boat_b.player_id in boat_a.pair_stats:
        return boat_a.pair_stats[boat_b.player_id]["score"]
    return 50


# ============================================
#  穴パターン選択
# ============================================
def select_best_hole_pattern(b1, b2, b3, scores):
    patterns = {
        f"5-{b1}-{b2}": scores[5] + 15,
        f"{b1}-5-{b2}": scores[5] + 10,
        f"{b1}-{b2}-5": scores[5] + 5,
    }
    return max(patterns, key=patterns.get)


# ============================================
#  predict()（相性対応版）
# ============================================
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
    if ps_12 >= 60: s1 += 5
    elif ps_12 <= 30: s1 -= 5

    ps_23 = pair_score(B2, B3)
    if ps_23 >= 60: s2 += 5
    elif ps_23 <= 30: s2 -= 5

    label1 = "鉄板" if s1 >= teppan_th else "スルー"
    label2 = "買い" if s2 >= buy_th else "スルー"

    # 穴判定
    hole = None
    hole_score = scores.get(5, 0)
    B5 = boat_dict.get(5)

    if B5:
        if race.is_4kado_attack: hole_score += 20
        if race.wind_dir == "向かい風": hole_score += 10
        if race.water_condition == "荒れ": hole_score += 10
        if B5.motor_score >= 70: hole_score += 10
        if race.trend == "まくりデー": hole_score += 15

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
    if label1 == "スルー": suru_list.append(pick1)
    if label2 == "スルー": suru_list.append(pick2)
    suru_out = suru_list if suru_list else None

    return {
        "teppan": teppan_out,
        "kai": kai_out,
        "suru": suru_out,
        "ana": hole
    }


# ============================================
#  predict_all()
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

        if pred["teppan"] or pred["kai"] or pred["ana"]:
            summary.append(race_output)

    summary = sorted(summary, key=lambda x: x["race_number"])
    return results, summary


# ============================================
#  まとめ表示
# ============================================
def format_summary(summary):
    if len(summary) == 0:
        return "【本日買うべきレースはありません】"

    lines = ["【本日買うべきレース一覧】\n"]
    for r in summary:
        lines.append(f"{r['race_name']} {r['race_number']}R")
        if r["teppan"]: lines.append(f"鉄板：{r['teppan']}")
        if r["kai"]: lines.append(f"買い：{r['kai']}")
        if r["ana"]: lines.append(f"穴：{r['ana']}")
        lines.append("")
    return "\n".join(lines)


# ============================================
#  サンプルデータ（丸亀5R）
# ============================================
boat1 = Boat(
    1,101,"A選手",0.13,7.2,7.5,{1:85},0,0.2,78,"出足が良い",
    {102:{"together":12,"hit":7,"score":58}}
)
boat2 = Boat(
    2,102,"B選手",0.14,6.5,6.8,{2:60},0,0.3,72,"悪くない",
    {101:{"together":12,"hit":7,"score":58}}
)
boat3 = Boat(
    3,103,"C選手",0.16,5.8,5.9,{3:55},1,0.5,65,"普通",
    {}
)
boat4 = Boat(4,104,"D選手",0.15,6.0,6.2,{4:60},0,0.4,70,"悪くない",{})
boat5 = Boat(
    5,105,"E選手",0.15,5.5,5.7,{5:55},0,0.3,75,"伸びが良い",
    {101:{"together":5,"hit":3,"score":60}}
)
boat6 = Boat(6,106,"F選手",0.17,4.8,4.9,{6:40},0,0.6,60,"普通",{})

race = Race(
    "丸亀",5,
    [boat1,boat2,boat3,boat4,boat5,boat6],
    "向かい風",4,"普通","まくりデー",True
)


# ============================================
#  実行テスト
# ============================================
result = predict(race)
print("▼ レース単体予想")
print(result)

results, summary = predict_all([race])
print("\n▼ まとめ表示")
print(format_summary(summary))
