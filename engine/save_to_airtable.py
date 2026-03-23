import requests

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
    Airtable に1件保存
    """

    payload = {
        "records": [
            {"fields": record}
        ]
    }

    try:
        response = requests.post(
            AIRTABLE_URL,
            headers=HEADERS,
            json=payload  # ←重要（json指定）
        )

        if response.status_code in (200, 201):
            return {
                "success": True,
                "status": response.status_code,
                "id": response.json().get("records", [{}])[0].get("id")
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


def save_batch_to_airtable(records):
    """
    複数レコード一括保存（最大10件/回）
    """

    results = []

    for i in range(0, len(records), 10):
        chunk = records[i:i + 10]

        payload = {
            "records": [{"fields": r} for r in chunk]
        }

        try:
            response = requests.post(
                AIRTABLE_URL,
                headers=HEADERS,
                json=payload
            )

            results.append({
                "status": response.status_code,
                "success": response.status_code in (200, 201)
            })

        except Exception as e:
            results.append({
                "success": False,
                "error": str(e)
            })

    return results
