from flask import Flask, request, abort
from engine.predict_engine import predict_all, format_summary

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os

app = Flask(__name__)

# ★ あなたのチャネルシークレットとアクセストークンをここに入れる
CHANNEL_SECRET = "あなたのチャネルシークレット"
CHANNEL_ACCESS_TOKEN = "あなたのアクセストークン"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ★ メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # 「予想」と送られたら予想エンジンを実行
    if user_text == "予想":
        result = predict_all()
        summary = format_summary(result)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=summary)
        )
    else:
        # その他のメッセージには説明を返す
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="「予想」と送ると本日の買うべきレースを表示します。")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
