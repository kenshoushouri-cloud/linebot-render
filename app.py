from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from engine.predict_engine import predict_all, format_full_output
from data_loader import load_today_races  # ルート直下の data_loader.py を読み込む

app = Flask(__name__)

# ★ あなたの LINE チャネル情報をここに入れる
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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text == "予想":
        # ★ 今日のレース一覧を取得
        races = load_today_races()

        # ★ 全レース結果と買うべきレース一覧を取得
        results, summary = predict_all(races)

        # ★ 詳細 → 一覧 の順で整形
        output_text = format_full_output(results, summary)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=output_text)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="「予想」と送ると本日の買うべきレースを表示します。")
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
