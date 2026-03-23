def evaluate_prediction(pred, result, odds_dict):
    """
    pred: predict() の返り値
    result: "1-3-2"
    odds_dict: {"1-3-2": 24.5, ...}
    """

    main = pred.get("main")
    ana = pred.get("ana")

    main_hit = (main == result)
    ana_hit = (ana == result)

    odds_main = odds_dict.get(main, 0) if main else 0
    odds_ana = odds_dict.get(ana, 0) if ana else 0

    ev_main = pred.get("ev_main")
    ev_ana = pred.get("ev_ana")

    # ===== EVギャップ（期待値と実オッズの乖離） =====
    # EV > 1.0 の買い目が本当に儲かるかを検証するために重要
    ev_gap_main = None
    ev_gap_ana = None

    if ev_main and odds_main:
        ev_gap_main = odds_main - (1 / ev_main)

    if ev_ana and odds_ana:
        ev_gap_ana = odds_ana - (1 / ev_ana)

    return {
        # 的中判定
        "main_hit": main_hit,
        "ana_hit": ana_hit,

        # 賭け有無（100円固定）
        "bet_main": 1 if main else 0,
        "bet_ana": 1 if ana else 0,

        # 払戻用オッズ
        "odds_main": odds_main,
        "odds_ana": odds_ana,

        # EV（分析用）
        "ev_main": ev_main,
        "ev_ana": ev_ana,

        # EVギャップ（改善点）
        "ev_gap_main": ev_gap_main,
        "ev_gap_ana": ev_gap_ana,

        # ログ
        "pred_main": main,
        "pred_ana": ana,
        "result": result
    }
