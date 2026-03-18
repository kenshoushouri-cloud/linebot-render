from flask import Flask, request, abort, redirect
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
import pickle
import google.auth.transport.requests
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)

# ===== LINE =====
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== OAuth =====
CLIENT_SECRETS_FILE = "client_secret.json"   # Render にアップロードする
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
REDIRECT_URI = "https://linebot-render-yfj4.onrender.com"  # 後で書き換える

TOKEN_FILE = "token.pickle"  # 認証後に自動生成される


def get_credentials():
    """OAuth 認証済みなら token.pickle を読み込む"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

        # トークンが期限切れなら更新
        if creds.expired and creds.refresh_token:
            request_session = google.auth.transport.requests.Request()
            creds.refresh(request_session)
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        return creds

    return None


@app.route("/authorize")
def authorize():
    """OAuth 認証開始"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """OAuth 認証完了 → token.pickle 保存"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    with open(TOKEN_FILE, "wb") as token:
        pickle.dump(creds, token)

    return "Google Sheets 認証が完了しました！"


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    creds = get_credentials()
    if not creds:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Google 認証が必要です。\n以下をタップしてください：\https://linebot-render-yfj4.onrender.com")
        )
        return

    # ===== Sheets に書き込み =====
    service = build("sheets", "v4", credentials=creds)
    sheet_id = "https://docs.google.com/spreadsheets/d/1-DXbAAyhKS2ZRrDVGN-FBp4_b4LkXmm22AqxHBdQFIQ/edit?usp=drivesdk"  # ←ここを書き換える

    values = [[user_text]]
    body = {"values": values}

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="書き込みました！")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
