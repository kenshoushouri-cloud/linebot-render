def calc_stats(records):
    total_races = len(records)

    total_bet = 0
    total_return = 0

    main_hits = 0
    ana_hits = 0

    main_bet_count = 0
    ana_bet_count = 0

    # ===== EV分析 =====
    ev_main_list = []
    ev_ana_list = []

    # ===== EVギャップ分析 =====
    ev_gap_main_list = []
    ev_gap_ana_list = []

    # ===== 高EV穴の精度 =====
    high_ev_ana_hits = 0
    high_ev_ana_count = 0

    for r in records:
        # ===== 本線 =====
        if r["bet_main"]:
            total_bet += 100
            main_bet_count += 1

            if r["main_hit"]:
                main_hits += 1
                total_return += r["odds_main"] * 100

            if r["ev_main"] is not None:
                ev_main_list.append(r["ev_main"])

            if r["ev_gap_main"] is not None:
                ev_gap_main_list.append(r["ev_gap_main"])

        # ===== 穴 =====
        if r["bet_ana"]:
            total_bet += 100
            ana_bet_count += 1

            if r["ana_hit"]:
                ana_hits += 1
                total_return += r["odds_ana"] * 100

            if r["ev_ana"] is not None:
                ev_ana_list.append(r["ev_ana"])

            if r["ev_gap_ana"] is not None:
                ev_gap_ana_list.append(r["ev_gap_ana"])

            # ===== 高EV穴の検証 =====
            if r["ev_ana"] and r["ev_ana"] >= 1.2:
                high_ev_ana_count += 1
                if r["ana_hit"]:
                    high_ev_ana_hits += 1

    # ===== 回収率 =====
    roi = total_return / total_bet if total_bet else 0

    # ===== 的中率 =====
    hit_rate_main = main_hits / main_bet_count if main_bet_count else 0
    hit_rate_ana = ana_hits / ana_bet_count if ana_bet_count else 0

    # ===== EV平均 =====
    avg_ev_main = sum(ev_main_list) / len(ev_main_list) if ev_main_list else 0
    avg_ev_ana = sum(ev_ana_list) / len(ev_ana_list) if ev_ana_list else 0

    # ===== EVギャップ平均 =====
    avg_ev_gap_main = sum(ev_gap_main_list) / len(ev_gap_main_list) if ev_gap_main_list else 0
    avg_ev_gap_ana = sum(ev_gap_ana_list) / len(ev_gap_ana_list) if ev_gap_ana_list else 0

    # ===== 高EV穴の精度 =====
    high_ev_ana_hit_rate = (
        high_ev_ana_hits / high_ev_ana_count if high_ev_ana_count else 0
    )

    return {
        "total_races": total_races,

        # ===== 投資・回収 =====
        "total_bet": total_bet,
        "total_return": total_return,
        "roi": round(roi, 3),

        # ===== 的中 =====
        "main_hits": main_hits,
        "ana_hits": ana_hits,
        "hit_rate_main": round(hit_rate_main, 3),
        "hit_rate_ana": round(hit_rate_ana, 3),

        # ===== EV分析 =====
        "avg_ev_main": round(avg_ev_main, 3),
        "avg_ev_ana": round(avg_ev_ana, 3),

        # ===== EVギャップ分析 =====
        "avg_ev_gap_main": round(avg_ev_gap_main, 3),
        "avg_ev_gap_ana": round(avg_ev_gap_ana, 3),

        # ===== 高EV穴の精度 =====
        "high_ev_ana_count": high_ev_ana_count,
        "high_ev_ana_hit_rate": round(high_ev_ana_hit_rate, 3),

        # ===== 参考 =====
        "main_bet_count": main_bet_count,
        "ana_bet_count": ana_bet_count
    }
