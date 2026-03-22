from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# --- 環境変数からキーを取得（GitHub には書かない） ---
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# --- Airtable 保存 ---
def save_to_airtable(race_id, prediction):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "records": [
            {
                "fields": {
                    "race_id": race_id,
                    "prediction": prediction
                }
            }
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.status_code == 200 or response.status_code == 201

# --- LINE 返信 ---
def reply_to_line(reply_token, message):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, json=body, headers=headers)

# --- 予想ロジック（仮） ---
def predict(race_id):
    # ここにあなたの予想ロジックを入れる
    return f"レース {race_id} の予想結果：1-2-3"

# --- Webhook 受信 ---
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json

    try:
        event = body["events"][0]
        reply_token = event["replyToken"]
        user_message = event["message"]["text"]

        race_id = user_message.strip()
        prediction = predict(race_id)

        save_to_airtable(race_id, prediction)
        reply_to_line(reply_token, prediction)

    except Exception as e:
        print("Error:", e)

    return "OK"

# --- Render 用ポート設定 ---
@app.route("/")
def home():
    return "Bot is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
