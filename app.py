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
CLIENT_SECRETS_FILE = "client_secret_159246054178-t7fqvkn6kac7agf3n8j2jtad79dfvgu7.apps.googleusercontent.com.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
REDIRECT_URI = "https://linebot-render-yfj4.onrender.com/callback"

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


# ===== 認証開始 =====
@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge_method="S256"
    )

    # code_verifier をファイルに保存（Render でも消えない）
    with open("code_verifier.txt", "w") as f:
        f.write(flow.code_verifier)

    return redirect(auth_url)


# ===== 認証完了 =====
@app.route("/callback")
def callback():
    # 保存しておいた code_verifier を読み込む
    if not os.path.exists("code_verifier.txt"):
        return "code_verifier が見つかりません。もう一度 /authorize から開始してください。"

    with open("code_verifier.txt", "r") as f:
        code_verifier = f.read().strip()

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        code_verifier=code_verifier
    )

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    with open(TOKEN_FILE, "wb") as token:
        pickle.dump(creds, token)

    return "Google Sheets 認証が完了しました！"


# ===== LINE Webhook =====
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ===== メッセージ処理 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    creds = get_credentials()
    if not creds:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "Google 認証が必要です。\n"
                    "以下をタップしてください：\n"
                    "https://linebot-render-yfj4.onrender.com/authorize"
                )
            )
        )
        return

    # ===== Sheets に書き込み =====
    service = build("sheets", "v4", credentials=creds)
    sheet_id = "1-DXbAAyhKS2ZRrDVGN-FBp4_b4LkXmm22AqxHBdQFIQ"  # 必要なら変更

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

