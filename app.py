from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'My0MUGnag0QWdWeC6PdIBOxD+Xe0u/nU/CjH9qSzfui4pfZcML1H3RaUUHyyIx+XwEM+FKrzxSLPfB/CT2Mu9r6j3+OQ7dW3s14JzS2cnob2LrLlQ8ZVzVOY6XLo2eeseYwzPorkAEKvrgaRtLq7+AdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'a550cf4c2a8c3d2342efa2be2415b017'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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

def get_prediction(race_name):
    # ここに予想ロジックを入れる（今は固定）
    honmei = "1-2-3"
    ana = "1-3-5"
    return f"{race_name}の予想\n本命：{honmei}\n穴：{ana}"


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

