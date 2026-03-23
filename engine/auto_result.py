from datetime import datetime
from engine.result_fetcher import fetch_race_result
from engine.predict_engine import predict
from engine.evaluator import evaluate_prediction
from engine.airtable_formatter import format_for_airtable
from engine.save_to_airtable import save_to_airtable
from engine.data_models import Race

import json
import os

# ===== 保存しておいた「対象競艇場」を読み込む =====
def load_target_place():
    if not os.path.exists("target_place.json"):
        return None
    with open("target_place.json", "r") as f:
        return json.load(f).get("place")


# ===== 今日の全レースを自動処理 =====
def auto_process_all_races():
    place = load_target_place()
    if not place:
        print("対象競艇場が設定されていません。")
        return

    print(f"対象競艇場：{place}")

    today = datetime.now().strftime("%Y%m%d")

    for race_number in range(1, 13):
        print(f"{race_number}R を処理中…")

        race = Race(place=place, number=race_number)
        pred = predict(race)

        result, odds_dict = fetch_race_result(place, race_number, today)

        if not result:
            print(f"{race_number}R の結果がまだありません。")
            continue

        eval_result = evaluate_prediction(pred, result, odds_dict)

        record = format_for_airtable(race, pred, eval_result)
        save_to_airtable(record)

        print(f"{race_number}R 保存完了：{result}")

    print("全レースの自動保存が完了しました。")


if __name__ == "__main__":
    auto_process_all_races()
