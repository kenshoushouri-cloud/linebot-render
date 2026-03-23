import requests
import json

# ===== Airtable 設定 =====
AIRTABLE_API_KEY = "YOUR_API_KEY"
AIRTABLE_BASE_ID = "YOUR_BASE_ID"
AIRTABLE_TABLE_NAME = "predictions"

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}


def save_to_airtable(record):
    """
    Airtable に1件のレコードを保存する
    record: airtable_formatter.format_for_airtable() の返り値
    """

    payload = {
        "records": [
            {"fields": record}
        ]
    }

    try:
        response = requests.post(AIRTABLE_URL, headers=HEADERS, data=json.dumps(payload))

        if response.status_code in (200, 201):
            return {
                "success": True,
                "status": response.status_code,
                "response": response.json()
            }
        else:
            return {
                "success": False,
                "status": response.status_code,
                "error": response.text
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
