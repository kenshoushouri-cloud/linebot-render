import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ====== あなたの Airtable 情報 ======
AIRTABLE_API_KEY = "YOUR_API_KEY"  # ← pat から始まるキーをここに貼る
BASE_ID = "appK7g1LhorYnNLwg"
TABLE_NAME = "race"

# ====== LINE Bot 情報 ======
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# ====== 気象データ取得（仮のAPI：住之江・丸亀などの天気を返す） ======
def get_weather(place):
    # 実際の天気APIに置き換え可能
    dummy_weather = {
        "住之江": {"wind": 3, "wave": 0.5},
        "丸亀": {"wind": 2, "wave": 0.3},
        "唐津": {"wind": 4, "wave": 0.7},
        "大村": {"wind": 1, "wave": 0.2},
    }
    return dummy_weather.get(place, {"wind": 2, "wave": 0.3})

# ====== 予想ロジック（簡易版） ======
def predict_boatrace(place, race_no):
    weather = get_weather(place)
    wind = weather["wind"]
    wave = weather["wave"]

    # シンプル予想ロジック
    if wind <= 2:
        prediction = "1-3"
        confidence = "A"
    elif wind <= 4:
        prediction = "1-4"
        confidence = "B"
    else:
        prediction = "3-5"
        confidence = "C"

    return prediction, confidence, weather

# ====== Airtable 保存 ======
def save_to_airtable(date, place, race_no, prediction, race_id, result=""):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "records": [
            {
                "fields": {
                    "A date": date,
                    "A stadium": place,
                    "# race_no": race_no,
                    "🧠 prediction": prediction,
                    "🧠 race_id": race_id,
                    "🧠 result": result
                }
            }
        ]
    }
    requests.post(url, json=data, headers=headers)

# ====== LINE Webhook ======
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ====== メッセージ受信 ======
@handler.add(MessageEvent, MessageEvent.message_type == TextMessage)
def handle_message(event):
    text = event.message.text

    # 例：住之江5R
    place = text[:2]
    race_no = text[-2:].replace("R", "")

    # 日付（今日）
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    # race_id
    race_id = f"{date}-{place}-{race_no}"

    # 予想
    prediction, confidence, weather = predict_boatrace(place, race_no)

    # Airtable 保存
    save_to_airtable(date, place, race_no, prediction, race_id)

    # 返信
    reply = (
        f"🏁 *競艇予想*\n"
        f"【{place}{race_no}R】\n\n"
        f"🎯 予想：{prediction}\n"
        f"📊 信頼度：{confidence}\n\n"
        f"🌤 天気\n"
        f"風：{weather['wind']}m\n"
        f"波：{weather['wave']}m\n\n"
        f"🧠 race_id：{race_id}\n"
        f"（Airtable に保存しました）"
    )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
