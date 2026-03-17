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

# 仮データ生成（ランダム）
def get_mock_race_data():
    data = []
    for lane in range(1, 7):
        player = {
            "lane": lane,
            "name": f"選手{lane}",
            "national_win": round(random.uniform(4.0, 7.5), 2),   # 全国勝率
            "local_win": round(random.uniform(4.0, 7.5), 2),      # 当地勝率
            "motor": random.randint(20, 60),                      # モーター2連率
            "boat": random.randint(20, 60),                       # ボート2連率
            "st": round(random.uniform(0.10, 0.25), 2),           # ST
            "penalty": random.choice([0, 0, 0, 1]),               # F/Lペナルティ
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
    score += (6 - p["lane"]) * 0.8        # コース別勝率の簡易版
    score -= p["st"] * 10                 # STは速いほど有利
    score -= p["penalty"] * 3             # F/Lペナルティ

    # コメント補正
    if p["comment"] == "伸び":
        score += 1.5
    elif p["comment"] == "出足":
        score += 1.0

    # 印補正
    if p["mark"] == "◎":
        score += 1.2
    elif p["mark"] == "○":
        score += 0.8
    elif p["mark"] == "▲":
        score += 0.4

    return round(score, 1)


# メイン予想関数
def get_prediction(race_name):
    # 仮データ生成
    players = get_mock_race_data()

    # スコア計算
    for p in players:
        p["score"] = calculate_score(p)

    # スコア順に並べる
    sorted_players = sorted(players, key=lambda x: x["score"], reverse=True)

    # 確信度
    D = round(sorted_players[0]["score"] - sorted_players[1]["score"], 1)

    # 確信度分類
    if D >= 5.5:
        rank = "鉄板"
    elif D >= 4.1:
        rank = "買い"
    else:
        rank = "スルー"

    # 本命・波乱（簡易版）
    honmei = f"{sorted_players[0]['lane']}-{sorted_players[1]['lane']}-{sorted_players[2]['lane']}"
    haran = f"{sorted_players[1]['lane']}-{sorted_players[0]['lane']}-{sorted_players[2]['lane']}"

    # 出力フォーマット
    text = f"""
🏁【{race_name}】

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

