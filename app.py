from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'My0MUGnag0QWdWeC6PdIBOxD+Xe0u/nU/CjH9qSzfui4pfZcML1H3RaUUHyyIx+XwEM+FKrzxSLPfB/CT2Mu9r6j3+OQ7dW3s14JzS2cnob2LrLlQ8ZVzVOY6XLo2eeseYwzPorkAEKvrgaRtLq7+AdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'a550cf4c2a8c3d2342efa2be2415b017'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


import requests
import datetime
import random

# ===== ここに OpenWeatherMap の API キーを貼る =====
OWM_API_KEY = "75752756f94430194a9f26ef4e0518db"

# 競艇場ごとの緯度・経度
BOAT_LATLON = {
    "桐生":   {"lat": 36.4028, "lon": 139.3344},
    "戸田":   {"lat": 35.8153, "lon": 139.6425},
    "江戸川": {"lat": 35.6925, "lon": 139.8681},
    "平和島": {"lat": 35.5878, "lon": 139.7422},
    "多摩川": {"lat": 35.6267, "lon": 139.4881},
    "浜名湖": {"lat": 34.7189, "lon": 137.6033},
    "蒲郡":   {"lat": 34.8264, "lon": 137.2478},
    "常滑":   {"lat": 34.8864, "lon": 136.8283},
    "津":     {"lat": 34.7192, "lon": 136.5142},
    "三国":   {"lat": 36.2211, "lon": 136.1692},
    "びわこ": {"lat": 35.0878, "lon": 135.9442},
    "住之江": {"lat": 34.6122, "lon": 135.4842},
    "尼崎":   {"lat": 34.7311, "lon": 135.4175},
    "鳴門":   {"lat": 34.1736, "lon": 134.6203},
    "丸亀":   {"lat": 34.2731, "lon": 133.7981},
    "児島":   {"lat": 34.4572, "lon": 133.7461},
    "宮島":   {"lat": 34.2953, "lon": 132.3292},
    "徳山":   {"lat": 34.0481, "lon": 131.8061},
    "下関":   {"lat": 33.9511, "lon": 130.9411},
    "若松":   {"lat": 33.9056, "lon": 130.8111},
    "芦屋":   {"lat": 33.8892, "lon": 130.6639},
    "福岡":   {"lat": 33.6344, "lon": 130.4442},
    "唐津":   {"lat": 33.4503, "lon": 129.9933},
    "大村":   {"lat": 32.9311, "lon": 129.9531},
}

# ホームストレッチの向き（度数：0=北,90=東,180=南,270=西）
COURSE_HEADING = {
    "桐生": 180,
    "戸田": 0,
    "江戸川": 180,
    "平和島": 0,
    "多摩川": 0,
    "浜名湖": 180,
    "蒲郡": 180,
    "常滑": 0,
    "津": 0,
    "三国": 180,
    "びわこ": 0,
    "住之江": 45,   # 北東向き（概ね）
    "尼崎": 0,
    "鳴門": 180,
    "丸亀": 180,
    "児島": 0,
    "宮島": 180,
    "徳山": 225,   # 南西向き
    "下関": 0,
    "若松": 180,
    "芦屋": 0,
    "福岡": 180,
    "唐津": 0,
    "大村": 180,
}

# 競艇場データ（例：丸亀のみ）
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

RACER_DATA = {}
MOTOR_DATA = {}

# ===== 気象キャッシュ（B案：7時以降の最初の予想時に全場まとめて取得） =====
DAILY_WEATHER = {}          # { "丸亀": {"deg": 180, "speed": 3.5, "desc": "晴れ"} }
LAST_WEATHER_DAY = None     # 「気象の日付」（7時またぎ対応）

def _weather_day(now: datetime.datetime):
    """7時を境に『気象の日付』を決める。
       7時前 → 前日扱い / 7時以降 → 当日扱い
    """
    if now.hour >= 7:
        return now.date()
    else:
        return (now.date() - datetime.timedelta(days=1))

def fetch_weather(place):
    """単一場の現在気象を OpenWeatherMap から取得"""
    info = BOAT_LATLON.get(place)
    if info is None or not OWM_API_KEY:
        return None, None, None

    lat = info["lat"]
    lon = info["lon"]

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ja"
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        wind = data.get("wind", {})
        wind_speed = wind.get("speed")  # m/s
        wind_deg = wind.get("deg")      # 0〜360°
        weather_desc = None
        if data.get("weather"):
            weather_desc = data["weather"][0].get("description")
        return wind_deg, wind_speed, weather_desc
    except:
        return None, None, None

def update_all_weather_if_needed():
    """7時以降の最初の予想時に、全場の気象をまとめて取得してキャッシュ"""
    global DAILY_WEATHER, LAST_WEATHER_DAY

    now = datetime.datetime.now()
    today_weather_day = _weather_day(now)

    # 初回 or 気象日が変わったら全場更新
    if LAST_WEATHER_DAY != today_weather_day and now.hour >= 7:
        DAILY_WEATHER = {}
        for place in BOAT_LATLON.keys():
            deg, speed, desc = fetch_weather(place)
            DAILY_WEATHER[place] = {
                "deg": deg,
                "speed": speed,
                "desc": desc
            }
        LAST_WEATHER_DAY = today_weather_day

def get_weather(place):
    """キャッシュされた気象を返す（必要なら全場更新）"""
    update_all_weather_if_needed()
    w = DAILY_WEATHER.get(place)
    if not w:
        return None, None, None
    return w["deg"], w["speed"], w["desc"]

# ===== ここから風向判定・スコア計算など =====

def normalize_angle_diff(a, b):
    diff = (a - b + 180) % 360 - 180
    return diff

def classify_relative_wind(place, wind_deg):
    if wind_deg is None:
        return "不明"

    heading = COURSE_HEADING.get(place)
    if heading is None:
        return "不明"

    diff_tail = normalize_angle_diff(wind_deg, heading)
    opposite = (heading + 180) % 360
    diff_head = normalize_angle_diff(wind_deg, opposite)

    if abs(diff_tail) <= 30:
        return "追い風"
    if abs(diff_head) <= 30:
        return "向かい風"

    rel = normalize_angle_diff(wind_deg, heading)
    if 0 < rel < 180:
        return "右横風"
    else:
        return "左横風"

def get_mock_race_data():
    data = []
    for i in range(1, 7):
        data.append({
            "艇番": i,
            "全国勝率": round(random.uniform(4.0, 7.5), 2),
            "当地勝率": round(random.uniform(4.0, 7.5), 2),
            "モーター": random.randint(20, 80),
            "ボート": random.randint(20, 80),
            "ST": round(random.uniform(0.10, 0.20), 2)
        })
    return data

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
    elif wind_type in ["右横風", "左横風"]:
        score -= (wind_speed or 0) * 0.5

    course = COURSE_DATA.get(place)
    if course:
        lane = racer["艇番"]
        if lane == 1:
            score += course.get("1コース1着率", 0) * 0.3
        if lane == 2:
            score += course.get("2コース差し率", 0) * 0.2
        if lane == 3:
            score += course.get("3コースまくり率", 0) * 0.2
        if lane == 4:
            score += course.get("4コースまくり差し率", 0) * 0.2

        wind_adj = course.get("風向き補正", {}).get(wind_type, {})
        score += wind_adj.get(str(lane), 0)

    return score

def get_prediction(race_name):
    place = race_name[:2]
    today = datetime.datetime.now().strftime("%Y/%m/%d")

    wind_deg, wind_speed, weather_desc = get_weather(place)
    wind_type = classify_relative_wind(place, wind_deg)

    racers = get_mock_race_data()
    internal_scores = []
    for r in racers:
        s = calculate_score(r, place, wind_type, wind_speed)
        internal_scores.append({"艇番": r["艇番"], "スコア": s})

    sorted_scores = sorted(internal_scores, key=lambda x: x["スコア"], reverse=True)
    top3 = sorted_scores[:3]

    wind_speed_display = wind_speed if wind_speed is not None else "不明"
    wind_deg_display = wind_deg if wind_deg is not None else "不明"
    weather_display = weather_desc if weather_desc is not None else "不明"

    text = f"""
📅 {today}
🏁【{race_name}】

【気象（OpenWeather 現在値・1日固定）】
天気：{weather_display}
風向：{wind_type}（方位：{wind_deg_display}°）
風速：{wind_speed_display}m/s

【スコア順位】
1位：{top3[0]["艇番"]}号艇
2位：{top3[1]["艇番"]}号艇
3位：{top3[2]["艇番"]}号艇
"""

    first, second, third = top3[0]["艇番"], top3[1]["艇番"], top3[2]["艇番"]
    confidence = round((top3[0]["スコア"] - top3[1]["スコア"]) / 10, 1)

    text += f"""

【本命 3連単 1点】
{first}-{second}-{third}（確信度：{confidence}）

【中穴 3連単 1点】
{second}-{first}-{third}
"""

    return text

BOAT_RACES = list(BOAT_LATLON.keys())


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    for place in BOAT_RACES:
        if place + "全レース" in user_text:
            predictions = []
            for r in range(1, 13):
                predictions.append(get_prediction(f"{place}{r}R"))
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("\n\n".join(predictions))
            )
            return

    for place in BOAT_RACES:
        if place in user_text and "R" in user_text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(get_prediction(user_text))
            )
            return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(user_text))
