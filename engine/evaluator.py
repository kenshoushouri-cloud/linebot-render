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

    # ===== 賭け有無 =====
    bet_main = 1 if main else 0
    bet_ana = 1 if ana else 0

    # ===== オッズ取得 =====
    odds_main = odds_dict.get(main, 0) if main else 0
    odds_ana = odds_dict.get(ana, 0) if ana else 0

    # ===== 払戻計算（100円固定） =====
    return_main = odds_main * 100 if main_hit else 0
    return_ana = odds_ana * 100 if ana_hit else 0

    # ===== EV =====
    ev_main = pred.get("ev_main")
    ev_ana = pred.get("ev_ana")

    # ===== 正しいEVギャップ =====
    # EV = P × オッズ → P = EV / オッズ
    # EVギャップ = 実オッズ - (1 / P) = オッズ - (オッズ / EV)
    ev_gap_main = None
    ev_gap_ana = None

    if ev_main and odds_main:
        ev_gap_main = odds_main * (1 - 1/ev_main)

    if ev_ana and odds_ana:
        ev_gap_ana = odds_ana * (1 - 1/ev_ana)

    return {
        # ===== 的中 =====
        "main_hit": main_hit,
        "ana_hit": ana_hit,
        "no_hit": not (main_hit or ana_hit),

        # ===== 賭け =====
        "bet_main": bet_main,
        "bet_ana": bet_ana,

        # ===== オッズ =====
        "odds_main": odds_main,
        "odds_ana": odds_ana,

        # ===== 回収 =====
        "return_main": return_main,
        "return_ana": return_ana,
        "total_return": return_main + return_ana,
        "total_bet": (bet_main + bet_ana) * 100,

        # ===== EV =====
        "ev_main": ev_main,
        "ev_ana": ev_ana,
        "ev_gap_main": ev_gap_main,
        "ev_gap_ana": ev_gap_ana,

        # ===== ログ =====
        "pred_main": main,
        "pred_ana": ana,
        "result": result,

        # ===== フラグ =====
        "is_bet": 1 if (bet_main or bet_ana) else 0
    }
