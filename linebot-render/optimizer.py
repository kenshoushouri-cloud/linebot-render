import json
from pyairtable import Table
import os

# ===== Airtable 設定 =====
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE = "results"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

# ===== パラメータ読み込み =====
def load_params():
    with open("params.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ===== Airtable へ書き込み =====
def save_to_airtable(data):
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE)
    table.create(data)

# ===== メイン処理 =====
def main():
    params = load_params()

    # ここにあなたの最適化ロジックを追加
    # 例としてダミー結果を作成
    result = {
        "status": "success",
        "message": "Optimizer executed",
        "params_used": json.dumps(params, ensure_ascii=False)
    }

    save_to_airtable(result)
    print("Airtable に保存しました")

if __name__ == "__main__":
    main()
