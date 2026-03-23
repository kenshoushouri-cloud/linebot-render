def evaluate_prediction(pred, result):
    """
    予想結果を検証するロジック
    pred: predict() の返り値
    result: "1-3-2" のような着順文字列
    """

    main_hit = (pred["main"] == result)
    ana_hit = (pred["ana"] == result)

    # どちらも当たらない場合
    no_hit = not main_hit and not ana_hit

    return {
        "main_hit": main_hit,
        "ana_hit": ana_hit,
        "no_hit": no_hit,
        "ev_main": pred["ev_main"],
        "ev_ana": pred["ev_ana"],
        "pred_main": pred["main"],
        "pred_ana": pred["ana"],
        "result": result
    }
