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

# AMeDAS地点コード
AMEDAS_CODE = {
    "桐生": "42111", "戸田": "43372", "江戸川": "44132", "平和島": "44132", "多摩川": "44132",
    "浜名湖": "50331", "蒲郡": "51106", "常滑": "53133", "津": "53141", "三国": "54012",
    "びわこ": "60216", "住之江": "62078", "尼崎": "62078", "鳴門": "71106", "丸亀": "72086",
    "児島": "71351", "宮島": "74151", "徳山": "74182", "下関": "81236", "若松": "82182",
    "芦屋": "82182", "福岡": "82131", "唐津": "82442", "大村": "84431"
}

# 競艇場データ（Cプラン用）
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

# 朝7時の気象データ取得（正しいURL形式）
def get_weather_morning(place):
    code = AMEDAS_CODE.get(place)
    if code is None:
        return None, None

    today = datetime.datetime.now().strftime("%Y%m%d")

    # 07:00 → 06:50 → 06:40 → … → 05:00
    times = ["0700","0650","0640","0630","0620","0610","0600","0550","0540","0530","0520","0510","0500"]

    for t in times:
        url = f"https://www.jma.go.jp/bosai/amedas/data/{today}/{code}/{t}.json"
        try:
            data = requests.get(url, timeout=5).json()
            info = data[0]
            return info["wind_direction"]["value"], info["wind"]["value"]
        except:
            continue

    # 最後の手段：最新データ
    try:
        latest = requests.get("https://www.jma.go.jp/bosai/amedas/data/latest_time.txt").text.strip()
        url = f"https://www.jma.go.jp/bosai/amedas/data/{latest}/{code}.json"
        data = requests.get(url, timeout=5).json()
        info = data[0]
        return info["wind_direction"]["value"], info["wind"]["value"]
    except:
        return None, None


# 風向分類
def classify_wind_direction(wind_dir):
    if wind_dir is None:
        return "不明"
    if wind_dir in [0, 1]:
        return "向かい風"
    if wind_dir in [4, 5]:
        return "追い風"
    if wind_dir in [2, 3]:
        return "右横風"
    if wind_dir in [6, 7]:
        return "左横風"
    return "不明"


# モックデータ（後で実データに置換）
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


# スコア計算
def calculate_score(racer, place, wind_dir, wind_speed):
    score = (
        racer["全国勝率"] * 8 +
        racer["当地勝率"] * 6 +
        racer["モーター"] * 0.4 +
        racer["ボート"] * 0.3 +
        (0.20 - racer["ST"]) * 100
    )

    # 風の影響
    if wind_dir == "追い風":
        score += (wind_speed or 0) * 1.5
    elif wind_dir == "向かい風":
        score -= (wind_speed or 0) * 1.2
    elif wind_dir in ["右横風", "左横風"]:
        score -= (wind_speed or 0) * 0.5

    # 競艇場補正
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

        # 風向き補正
        wind_adj = course["風向き補正"].get(wind_dir, {})
        score += wind_adj.get(str(lane), 0)

    return score


# メイン予想
def get_prediction(race_name):
    place = race_name[:2]
    today = datetime.datetime.now().strftime("%Y/%m/%d")

    wind_dir_raw, wind_speed = get_weather_morning(place)
    direction = classify_wind_direction(wind_dir_raw)

    racers = get_mock_race_data()

    internal_scores = []
    for r in racers:
        s = calculate_score(r, place, direction, wind_speed)
        internal_scores.append({"艇番": r["艇番"], "スコア": s})

    sorted_scores = sorted(internal_scores, key=lambda x: x["スコア"], reverse=True)
    top3 = sorted_scores[:3]

    wind_speed_display = wind_speed if wind_speed is not None else "不明"

    text = f"""
📅 {today}
🏁【{race_name}】

【気象（朝7時固定）】
風向：{direction}
風速：{wind_speed_display}m

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


# 対応する競艇場一覧
BOAT_RACES = [
    "桐生","戸田","江戸川","平和島","多摩川",
    "浜名湖","蒲郡","常滑",
    "津","三国","びわこ","住之江","尼崎",
    "鳴門","丸亀","児島","宮島","徳山",
    "下関","若松","芦屋","福岡","唐津","大村"
]


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    for place in BOAT_RACES:
        if place + "全レース" in user_text:
            predictions = []
            for r in range(1, 13):
                predictions.append(get_prediction(f"{place}{r}R"))
            line_bot_api.reply_message(event.reply_token, TextSendMessage("\n\n".join(predictions)))
            return

    for place in BOAT_RACES:
        if place in user_text and "R" in user_text:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(get_prediction(user_text)))
            return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(user_text))


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
