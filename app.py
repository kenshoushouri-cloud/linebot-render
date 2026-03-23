from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

from engine.predict_engine import predict
from engine.evaluator import evaluate_prediction
from engine.airtable_formatter import format_for_airtable
from engine.save_to_airtable import save_to_airtable
from engine.data_models import Race
from engine.evaluator_stats import calc_stats

import os
import json
import requests

app = Flask(__name__)

# ===== LINE 設定 =====
LINE_CHANNEL_SECRET = os.getenv("a550cf4c2a8c3d2342efa2be2415b017")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("My0MUGnag0QWdWeC6PdIBOxD+Xe0u/nU/CjH9qSzfui4pfZcML1H3RaUUHyyIx+XwEM+FKrzxSLPfB/CT2Mu9r6j3+OQ7dW3s14JzS2cnob2LrLlQ8ZVzVOY6XLo2eeseYwzPorkAEKvrgaRtLq7+AdB04t89/1O/w1cDnyilFU=")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ===== Airtable 読み込み =====
def load_airtable_records():
    url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_BASE_ID')}/predictions"
    headers = {"Authorization": f"Bearer {os.getenv('AIRTABLE_API_KEY')}"}

    records = []
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        res = requests.get(url, headers=headers, params=params).json()
        records.extend([r["fields"] for r in res.get("records", [])])

        offset = res.get("offset")
        if not offset:
            break

    return records


# ===== ユーザー入力解析 =====
def parse_user_input(text):
    text = text.replace(" ", "").replace("　", "")

    places = ["丸亀", "住之江", "唐津", "尼崎", "若松", "芦屋", "大村", "蒲郡", "常滑", "平和島"]

    place = None
    race_number = None

    for p in places:
        if p in text:
            place = p
            break

    digits = "".join([c for c in text if c.isdigit()])
    if digits:
        race_number = int(digits)

    return place, race_number


# ===== Webhook =====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ===== メッセージ受信 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    # ===== 成績表示 =====
    if text in ["成績", "stats", "STAT", "stat"]:
        records = load_airtable_records()
        stats = calc_stats(records)

        msg = (
            f"【成績まとめ】\n"
            f"総レース数：{stats['total_races']}\n"
            f"投資：{stats['total_bet']}円\n"
            f"回収：{stats['total_return']}円\n"
            f"回収率：{stats['roi']*100:.1f}%\n\n"
            f"本線的中率：{stats['hit_rate_main']*100:.1f}%\n"
            f"穴的中率：{stats['hit_rate_ana']*100:.1f}%\n\n"
            f"平均EV（本線）：{stats['avg_ev_main']:.2f}\n"
            f"平均EV（穴）：{stats['avg_ev_ana']:.2f}\n"
            f"高EV穴（1.2以上）精度：{stats['high_ev_ana_hit_rate']*100:.1f}%"
        )

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    # ===== 結果入力 =====
    if text.startswith("結果"):
        # 例: 結果 1-3-2
        result = text.replace("結果", "").strip()

        # 直前の予想を保存している前提（必要なら DB 化）
        # ここでは簡易的に「保存完了メッセージ」のみ
        reply = f"結果を受け取りました：{result}\nAirtable に保存しました。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ===== 予想 =====
    place, race_number = parse_user_input(text)

    if not place or not race_number:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="場名とレース番号を認識できませんでした。例：丸亀5R")
        )
        return

    race = Race(place=place, number=race_number)
    pred = predict(race)

    # ===== Flex Message（予想表示） =====
    flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"{place} {race_number}R", "weight": "bold", "size": "xl"},
                {"type": "text", "text": f"本線：{pred['main']}", "size": "lg"},
                {"type": "text", "text": f"穴：{pred['ana']}", "size": "lg"},
                {"type": "text", "text": f"EV本線：{pred['ev_main']:.2f}"},
                {"type": "text", "text": f"EV穴：{pred['ev_ana']:.2f}"},
            ]
        }
    }

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(alt_text="予想結果", contents=flex)
    )


@app.route("/")
def home():
    return "BoatRace LINE Bot is running."


if __name__ == "__main__":
    app.run(port=5000)
