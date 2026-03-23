def format_for_airtable(race, pred, eval_result):
    """
    Airtable に保存するための統一フォーマット
    """

    return {
        "date": str(date.today()),
        "place": race.place,
        "race_number": race.number,

        "main": pred["main"],
        "ana": pred["ana"],
        "ev_main": pred["ev_main"],
        "ev_ana": pred["ev_ana"],

        "result": eval_result["result"],
        "main_hit": eval_result["main_hit"],
        "ana_hit": eval_result["ana_hit"],

        "weather": race.weather,
        "wind_dir": race.wind_dir,
        "wind_power": race.wind_power,
        "water_condition": race.water_condition,
        "trend": race.trend,
        "is_4kado_attack": race.is_4kado_attack,

        "scores": str(pred["scores"]),  # JSON文字列として保存
        "version": "v2.0-EV"  # ← バージョン管理も可能
    }
