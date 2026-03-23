import json
import statistics
from airtable import Airtable

# ===== Airtable 設定 =====
AIRTABLE_BASE_ID = "YOUR_BASE_ID"
AIRTABLE_TABLE = "results"
AIRTABLE_API_KEY = "YOUR_API_KEY"

# ===== パラメータ読み込み =====
def load_params():
    with open("params.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ===== パラメータ保存 =====
def save_params(params):
    with open("params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

# ===== 自動学習 =====
def optimize():
    print("=== Optimizer started ===")

    params = load_params()
    at = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE, AIRTABLE_API_KEY)

    records = at.get_all()

    if not records:
        print("No records found. Abort.")
        return

    # ===== 場ごとの回収率を集計 =====
    place_stats = {}

    for r in records:
        fields = r.get("fields", {})
        place = fields.get("place")
        ret = fields.get("return")
        bet = fields.get("bet")

        if place is None or ret is None or bet is None:
            continue

        if place not in place_stats:
            place_stats[place] = []

        place_stats[place].append(ret / bet)

    # ===== 場補正の自動調整 =====
    for place, arr in place_stats.items():
        avg = statistics.mean(arr)

        # 回収率が高い → 本線を強める、穴を緩める
        if avg > 1.2:
            params["place_adj"][place]["main_adj"] -= 1
            params["place_adj"][place]["ana_adj"] += 1

        # 回収率が低い → 本線を弱める、穴を厳しくする
        elif avg < 0.8:
            params["place_adj"][place]["main_adj"] += 1
            params["place_adj"][place]["ana_adj"] -= 1

    # ===== 保存 =====
    save_params(params)
    print("=== Optimizer finished. params.json updated ===")


if __name__ == "__main__":
    optimize()
