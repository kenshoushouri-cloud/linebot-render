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

# 朝7時の気象データ取得
def get_weather_morning(place):
    try:
        code = AMEDAS_CODE.get(place)
        if code is None:
            return None, None

        today = datetime.datetime.now().strftime("%Y%m%d")
        times = ["0700", "0650", "0640"]

        for t in times:
            url = f"https://www.jma.go.jp/bosai/amedas/data/{today}{t}/{code}.json"
            try:
                data = requests.get(url, timeout=5).json()
                info = data[0]
                wind_dir = info["wind_direction"]["value"]
                wind_speed = info["wind"]["value"]
                return wind_dir, wind_speed
            except:
                continue

        return None, None

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


# モックデータ生成
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
def calculate_score(racer, wind_dir, wind_speed):
    score = (
        racer["全国勝率"] * 8 +
        racer["当地勝率"] * 6 +
        racer["モーター"] * 0.4 +
        racer["ボート"] * 0.3 +
        (0.20 - racer["ST"]) * 100
    )

    if wind_dir == "追い風":
        score += (wind_speed or 0) * 1.5
    elif wind_dir == "向かい風":
        score -= (wind_speed or 0) * 1.2
    elif wind_dir in ["右横風", "左横風"]:
        score -= (wind_speed or 0) * 0.5

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
        s = calculate_score(r, direction, wind_speed)
        internal_scores.append({"艇番": r["艇番"], "スコア": s})

    sorted_scores = sorted(internal_scores, key=lambda x: x["スコア"], reverse=True)
    top3 = sorted_scores[:3]

    # 内部ログ
    print("【内部ログ】", today, race_name)
    print(sorted_scores)

    # 風速の表示を安全に処理
    wind_speed_display = wind_speed if wind_speed is not None else "不明"

    text = f"""
📅 {today}
🏁【{race_name}】

【気象（朝7時）】
風向：{direction}
風速：{wind_speed_display}m

【スコア順位】
1位：{top3[0]["艇番"]}号艇
2位：{top3[1]["艇番"]}号艇
3位：{top3[2]["艇番"]}号艇
"""

    # --- 買い目生成（A-1方式） ---
    first = top3[0]["艇番"]
    second = top3[1]["艇番"]
    third = top3[2]["艇番"]

    confidence = round((top3[0]["スコア"] - top3[1]["スコア"]) / 10, 1)

    honmei = f"{first}-{second}-{third}"
    nakana = f"{second}-{first}-{third}"

    text += f"""

【本命 3連単 1点】
{honmei}（確信度：{confidence}）

【中穴 3連単 1点】
{nakana}
"""

    return text
