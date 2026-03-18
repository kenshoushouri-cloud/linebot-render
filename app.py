import requests
import datetime
import random

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ===== Google Sheets 用 =====
import gspread
from google.oauth2.service_account import Credentials

# Flask アプリ
app = Flask(__name__)

# ===== LINE チャネル設定 =====
LINE_CHANNEL_ACCESS_TOKEN = "My0MUGnag0QWdWeC6PdIBOxD+Xe0u/nU/CjH9qSzfui4pfZcML1H3RaUUHyyIx+XwEM+FKrzxSLPfB/CT2Mu9r6j3+OQ7dW3s14JzS2cnob2LrLlQ8ZVzVOY6XLo2eeseYwzPorkAEKvrgaRtLq7+AdB04t89/1O/w1cDnyilFU="   # ← あなたのトークンを貼る
LINE_CHANNEL_SECRET = "a550cf4c2a8c3d2342efa2be2415b017"         # ← あなたのシークレットを貼る

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== Google Sheets 設定 =====
SPREADSHEET_ID = "1-DXbAAyhKS2ZRrDVGN-FBp4_b4LkXmm22AqxHBdQFIQ"
SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1


# ===== Render のヘルスチェック =====
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# ===== LINE Webhook 受信 =====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ===== メッセージ受信時の処理 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    reply_text = get_prediction(user_text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


# ===== OpenWeatherMap APIキー =====
OWM_API_KEY = "75752756f94430194a9f26ef4e0518db"

# ===== 競艇場データ =====
BOAT_LATLON = {
    "桐生": {"lat": 36.4028, "lon": 139.3344},
    "戸田": {"lat": 35.8153, "lon": 139.6425},
    "江戸川": {"lat": 35.6925, "lon": 139.8681},
    "平和島": {"lat": 35.5878, "lon": 139.7422},
    "多摩川": {"lat": 35.6267, "lon": 139.4881},
    "浜名湖": {"lat": 34.7189, "lon": 137.6033},
    "蒲郡": {"lat": 34.8264, "lon": 137.2478},
    "常滑": {"lat": 34.8864, "lon": 136.8283},
    "津": {"lat": 34.7192, "lon": 136.5142},
    "三国": {"lat": 36.2211, "lon": 136.1692},
    "びわこ": {"lat": 35.0878, "lon": 135.9442},
    "住之江": {"lat": 34.6122, "lon": 135.4842},
    "尼崎": {"lat": 34.7311, "lon": 135.4175},
    "鳴門": {"lat": 34.1736, "lon": 134.6203},
    "丸亀": {"lat": 34.2731, "lon": 133.7981},
    "児島": {"lat": 34.4572, "lon": 133.7461},
    "宮島": {"lat": 34.2953, "lon": 132.3292},
    "徳山": {"lat": 34.0481, "lon": 131.8061},
    "下関": {"lat": 33.9511, "lon": 130.9411},
    "若松": {"lat": 33.9056, "lon": 130.8111},
    "芦屋": {"lat": 33.8892, "lon": 130.6639},
    "福岡": {"lat": 33.6344, "lon": 130.4442},
    "唐津": {"lat": 33.4503, "lon": 129.9933},
    "大村": {"lat": 32.9311, "lon": 129.9531},
}

COURSE_HEADING = {
    "桐生": 180, "戸田": 0, "江戸川": 180, "平和島": 0, "多摩川": 0,
    "浜名湖": 180, "蒲郡": 180, "常滑": 0, "津": 0, "三国": 180,
    "びわこ": 0, "住之江": 45, "尼崎": 0, "鳴門": 180, "丸亀": 180,
    "児島": 0, "宮島": 180, "徳山": 225, "下関": 0, "若松": 180,
    "芦屋": 0, "福岡": 180, "唐津": 0, "大村": 180,
}

COURSE_DATA = {
    "丸亀": {
        "1コース1着率": 55,
        "2コース差し率": 28,
        "3コースまくり率": 22,
        "4コースまくり差し率": 30,
        "風向き補正": {
            "追い風": {"1": 5, "3": 3},
            "向かい風": {"2": 4, "4": 2},
            "右横風": {"1": -3},
            "左横風": {"4": 3}
        }
    }
}

# ===== 気象キャッシュ =====
DAILY_WEATHER = {}
LAST_WEATHER_DAY = None

def _weather_day(now):
    return now.date() if now.hour >= 7 else now.date() - datetime.timedelta(days=1)

def fetch_weather(place):
    info = BOAT_LATLON.get(place)
    if not info:
        return None, None, None

    try:
        res = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": info["lat"],
                "lon": info["lon"],
                "appid": OWM_API_KEY,
                "units": "metric",
                "lang": "ja"
            },
            timeout=4
        )
        data = res.json()
        wind = data.get("wind", {})
        return wind.get("deg"), wind.get("speed"), data["weather"][0]["description"]
    except:
        return None, None, None

def get_weather(place):
    global DAILY_WEATHER, LAST_WEATHER_DAY

    now = datetime.datetime.now()
    today = _weather_day(now)

    if LAST_WEATHER_DAY != today:
        DAILY_WEATHER = {}
        LAST_WEATHER_DAY = today

    if place not in DAILY_WEATHER:
        deg, speed, desc = fetch_weather(place)
        DAILY_WEATHER[place] = {"deg": deg, "speed": speed, "desc": desc}

    w = DAILY_WEATHER[place]
    return w["deg"], w["speed"], w["desc"]

def normalize_angle_diff(a, b):
    return (a - b + 180) % 360 - 180

def classify_relative_wind(place, wind_deg):
    if wind_deg is None:
        return "不明"

    heading = COURSE_HEADING.get(place)
    if heading is None:
        return "不明"

    diff_tail = normalize_angle_diff(wind_deg, heading)
    diff_head = normalize_angle_diff(wind_deg, (heading + 180) % 360)

    if abs(diff_tail) <= 30:
        return "追い風"
    if abs(diff_head) <= 30:
        return "向かい風"

    rel = normalize_angle_diff(wind_deg, heading)
    return "右横風" if 0 < rel < 180 else "左横風"

def get_mock_race_data():
    return [{
        "艇番": i,
        "全国勝率": round(random.uniform(4.0, 7.5), 2),
        "当地勝率": round(random.uniform(4.0, 7.5), 2),
        "モーター": random.randint(20, 80),
        "ボート": random.randint(20, 80),
        "ST": round(random.uniform(0.10, 0.20), 2)
    } for i in range(1, 7)]

def calculate_score(racer, place, wind_type, wind_speed):
    score = (
        racer["全国勝率"] * 8 +
        racer["当地勝率"] * 6 +
        racer["モーター"] * 0.4 +
        racer["ボート"] * 0.3 +
        (0.20 - racer["ST"]) * 100
    )

    if wind_type == "追い風":
        score += (wind_speed or 0) * 1.5
    elif wind_type == "向かい風":
        score -= (wind_speed or 0) * 1.2
    else:
        score -= (wind_speed or 0) * 0.5

    course = COURSE_DATA.get(place)
    if course:
        lane = racer["艇番"]
        if lane == 1:
            score += course["1コース1着率"] * 0.3
        if lane == 2:
            score += course["2コース差し率"] * 0.2
        if lane == 3:
            score += course["3コースまくり率"] * 0.2
        if lane == 4:
            score += course["4コースまくり差し率"] * 0.2

        score += course["風向き補正"].get(wind_type, {}).get(str(lane), 0)

    return score

# ===== Sheets 書き込み関数 =====
def save_prediction_to_sheet(place, race_name, top3, wind_type, wind_speed, confidence):
    row = [
        datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        place,
        race_name,
        top3[0]["艇番"],
        top3[1]["艇番"],
        top3[2]["艇番"],
        wind_type,
        wind_speed,
        confidence
    ]
    sheet.append_row(row)


def get_prediction(race_name):
    place = race_name[:2]
    today = datetime.datetime.now().strftime("%Y/%m/%d")

    wind_deg, wind_speed, weather_desc = get_weather(place)
    wind_type = classify_relative_wind(place, wind_deg)

    racers = get_mock_race_data()
    scores = [{"艇番": r["艇番"], "スコア": calculate_score(r, place, wind_type, wind_speed)} for r in racers]
    top3 = sorted(scores, key=lambda x: x["スコア"], reverse=True)[:3]

    text = f"""
📅 {today}
🏁【{race_name}】

【気象（1日固定）】
天気：{weather_desc}
風向：{wind_type}（{wind_deg}°）
風速：{wind_speed}m/s

【スコア順位】
1位：{top3[0]["艇番"]}号艇
2位：{top3[1]["艇番"]}号艇
3位：{top3[2]["艇番"]}号艇
"""

    first, second, third = top3[0]["艇番"], top3[1]["艇番"], top3[2]["艇番"]
    confidence = round((top3[0]["スコア"] - top3[1]["スコア"]) / 10, 1)

    text += f"""

【本命 3連単】
{first}-{second}-{third}（確信度：{confidence}）

【中穴】
{second}-{first}-{third}
"""

    # ===== Sheets に保存 =====
    save_prediction_to_sheet(place, race_name, top3, wind_type, wind_speed, confidence)

    return text

BOAT_RACES = list(BOAT_LATLON.keys())

# ===== ローカル実行用 =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
