def calc_stats(records):
    """
    records: Airtable から取得した検証データのリスト
    例：
    [
        {"main_hit": True, "ev_main": 1.12, "ev_ana": None},
        {"main_hit": False, "ana_hit": True, "ev_ana": 2.45},
        ...
    ]
    """

    total = len(records)
    main_hits = sum(1 for r in records if r["main_hit"])
    ana_hits = sum(1 for r in records if r["ana_hit"])

    # 回収率（EVベース）
    total_ev = 0
    for r in records:
        if r["main_hit"] and r["ev_main"]:
            total_ev += r["ev_main"]
        if r["ana_hit"] and r["ev_ana"]:
            total_ev += r["ev_ana"]

    return {
        "total": total,
        "main_hits": main_hits,
        "ana_hits": ana_hits,
        "hit_rate_main": main_hits / total if total else 0,
        "hit_rate_ana": ana_hits / total if total else 0,
        "ev_return": total_ev / total if total else 0
    }
