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


def get_teppan_threshold(place):
    return 75


def get_buy_threshold(place):
    return 65


def pair_score(boat_a, boat_b):
    if boat_b.player_id in boat_a.pair_stats:
        return boat_a.pair_stats[boat_b.player_id]["score"]
    return 50


def select_best_hole_pattern(b1, b2, b3, scores):
    patterns = {
        f"5-{b1}-{b2}": scores[5] + 15,
        f"{b1}-5-{b2}": scores[5] + 10,
        f"{b1}-{b2}-5": scores[5] + 5,
    }
    return max(patterns, key=patterns.get)
