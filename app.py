from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'My0MUGnag0QWdWeC6PdIBOxD+Xe0u/nU/CjH9qSzfui4pfZcML1H3RaUUHyyIx+XwEM+FKrzxSLPfB/CT2Mu9r6j3+OQ7dW3s14JzS2cnob2LrLlQ8ZVzVOY6XLo2eeseYwzPorkAEKvrgaRtLq7+AdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'a550cf4c2a8c3d2342efa2be2415b017'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)



import random
import requests

# AMeDAS地点コード（風向相関優先）
AMEDAS_CODE = {
    "桐生": "42111", "戸田": "43372", "江戸川": "44132", "平和島": "44132", "多摩川": "44132",
    "浜名湖": "50331", "蒲郡": "51106", "常滑": "53133", "津": "53141", "三国": "54012",
    "びわこ": "60216", "住之江": "62078", "尼崎": "62078", "鳴門": "71106", "丸亀": "72086",
    "児島": "71351", "宮島": "74151", "徳山": "74182", "下関": "81236", "若松": "82182",
    "芦屋": "82182", "福岡": "82131", "唐津": "82442", "大村": "84431"
}

# 気象データ取得（AMeDAS地点コード版）
def get_weather(place):
    try:
        code = AMEDAS_CODE.get(place)
        if code is None:
            return None, None

        # 最新時刻取得
        latest = requests.get("https://www.jma.go.jp/bosai/amedas/data/latest_time.json", timeout=5).json()
        latest_time = list(latest.values())[0]

        # 地点コードで直接アクセス
        url = f"https://www.jma.go.jp/bosai/amedas/data/{latest_time}/{code}.json"
        data = requests.get(url, timeout=5).json()

        info = data[0]  # 最新データ

        wind_dir = info["wind_direction"]["value"]
        wind_speed = info["wind"]["value"]

        return wind_dir, wind_speed

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

# 風補正
def wind_score_adjust(direction, speed):
    if speed is None:
        return 0

    score = 0

    if direction == "追い風":
        score += speed * 0.3
    elif direction == "向かい風":
        score += speed * 0.4
    elif direction == "右横風":
        score += speed * 0.5
    elif direction == "左横風":
        score += speed * 0.5

    if speed >= 7:
        score -= 1.5
    elif speed >= 5:
        score += 1.0

    return score

# 仮データ生成
def get_mock_race_data():
    data = []
    for lane in range(1, 7):
        player = {
            "lane": lane,
            "name": f"選手{lane}",
            "national_win": round(random.uniform(4.0, 7.5), 2),
            "local_win": round(random.uniform(4.0, 7.5), 2),
            "motor": random.randint(20, 60),
            "boat": random.randint(20, 60),
            "st": round(random.uniform(0.10, 0.25), 2),
            "penalty": random.choice([0, 0, 0, 1]),
            "comment": random.choice(["伸び", "出足", "普通", ""]),
            "mark": random.choice(["◎", "○", "▲", "△", ""])
        }
        data.append(player)
    return data

# スコア計算
def calculate_score(p):
    score = 0
    score += p["national_win"] * 2
    score += p["local_win"] * 1.2
    score += (p["motor"] / 3)
    score += (p["boat"] / 4)
    score += (6 - p["lane"]) * 0.8
    score -= p["st"] * 10
    score -= p["penalty"] * 3

    if p["comment"] == "伸び":
        score += 1.5
    elif p["comment"] == "出足":
        score += 1.0

    if p["mark"] == "◎":
        score += 1.2
    elif p["mark"] == "○":
        score += 0.8
    elif p["mark"] == "▲":
        score += 0.4

    return round(score, 1)

# メイン予想
def get_prediction(race_name):
    place = race_name[:2]

    # 気象データ取得
    wind_dir_raw, wind_speed = get_weather(place)
    direction = classify_wind_direction(wind_dir_raw)

    players = get_mock_race_data()

    # スコア計算＋風補正
    for p in players:
        p["score"] = calculate_score(p)
        p["score"] += wind_score_adjust(direction, wind_speed)

    sorted_players = sorted(players, key=lambda x: x["score"], reverse=True)

    D = round(sorted_players[0]["score"] - sorted_players[1]["score"], 1)

    if D >= 5.5:
        rank = "鉄板"
    elif D >= 4.1:
        rank = "買い"
    else:
        rank = "スルー"

    honmei = f"{sorted_players[0]['lane']}-{sorted_players[1]['lane']}-{sorted_players[2]['lane']}"
    haran = f"{sorted_players[1]['lane']}-{sorted_players[0]['lane']}-{sorted_players[2]['lane']}"

    text = f"""
🏁【{race_name}】

【気象】
風向：{direction}
風速：{wind_speed}m

【スコア順位】
1位：{sorted_players[0]['lane']}号艇（{sorted_players[0]['name']}）［{sorted_players[0]['score']}］
2位：{sorted_players[1]['lane']}号艇（{sorted_players[1]['name']}）［{sorted_players[1]['score']}］
3位：{sorted_players[2]['lane']}号艇（{sorted_players[2]['name']}）［{sorted_players[2]['score']}］

【展開予想】
■本命：{honmei}
■波乱：{haran}

【本命 3連単 1点】
{honmei}（確信度：{D}［{rank}］）

【中穴 3連単 1点】
なし
"""
    return text



@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


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

    # ①「◯◯全レース」の場合
    for place in BOAT_RACES:
        if place + "全レース" in user_text:
            predictions = []
            for r in range(1, 13):
                race_name = f"{place}{r}R"
                predictions.append(get_prediction(race_name))
            reply_text = "\n\n".join(predictions)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            return

    # ②「◯◯◯R」の場合（例：丸亀12R）
    for place in BOAT_RACES:
        if place in user_text and "R" in user_text:
            reply_text = get_prediction(user_text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            return

    # ③その他はオウム返し
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=user_text)
    )

