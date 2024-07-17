import json
import re
from flask import Flask, request, abort, render_template

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    PostbackEvent,
)
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    PostbackAction,
    TemplateMessage,
    ButtonsTemplate,
    ConfirmTemplate,
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from settings import key_config
from db import (
    createUserInfo,
    initDB,
    getUserInfo,
    incCurrentQid,
    addUserAns,
    calcPoints,
    getQuestionDict,
)
from handlerFunctions import (
    buildQuestionMessage,
    buildScoreMessage,
    buildRankingMessage,
    buildScraperMessage,
)

app = Flask(__name__)

access_token = key_config.LINE_CHANNEL_ACCESS_TOKEN
secret = key_config.LINE_CHANNEL_SECRET
Q_PATTERN = "q(\d)-([A-D])"

configuration = Configuration(access_token=access_token)
handler = WebhookHandler(secret)


@app.route("/", methods=["GET"])
def hello():
    return "hello"


@app.route("/set_questions_page", methods=["GET"])
def set_questions_page():
    return render_template("set_questions.html")


@app.route("/get_questions", methods=["GET"])
def get_questions():
    with open("./questions.json", "r") as f:
        return f.read()


@app.route("/set_questions", methods=["POST"])
def set_questions_post():
    qDict = request.get_data(as_text=True)
    json.dump(json.loads(qDict), open("./questions.json", "w"))
    return {}, 200


@app.route("/linebot", methods=["POST"])
def linebot():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if event.message.text == "建立資料":
            profile = line_bot_api.get_profile(event.source.user_id)
            info = getUserInfo(event.source.user_id)
            if info:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(
                                text=f"{profile.display_name} 的資料已建立! 不可重複建立!"
                            ),
                        ],
                    )
                )
            else:
                createUserInfo(profile)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(
                                text=f"{profile.display_name} 您好!資料已建立成功!"
                            ),
                        ],
                    )
                )
        elif event.message.text == "測驗開始":
            thisUserInfo = getUserInfo(event.source.user_id)
            if not thisUserInfo:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(text="請先建立資料!"),
                        ],
                    )
                )
            elif thisUserInfo.currentQid == 0:
                incCurrentQid(event.source.user_id)
                messages = []
                messages.append(buildQuestionMessage(thisUserInfo.currentQid + 1))
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(replyToken=event.reply_token, messages=messages)
                )
            else:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(text="測驗已經開始!"),
                        ],
                    )
                )
        elif event.message.text == "排名查詢":
            thisUserInfo = getUserInfo(event.source.user_id)
            if not thisUserInfo:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(text="請先建立資料!"),
                        ],
                    )
                )
            else:
                messages = [buildRankingMessage(event.source.user_id)]
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=messages,
                    )
                )
        elif event.message.text == "教育學程公告訊息":
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[buildScraperMessage()],
                )
            )


@handler.add(PostbackEvent)
def handle_postback(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        body = event.postback.data
        if len(body) == 0:
            return
        if body[0] == "q":
            thisUserInfo = getUserInfo(event.source.user_id)
            qMatch = re.match(Q_PATTERN, event.postback.data)
            thisQid = int(qMatch.group(1))
            if thisQid < thisUserInfo.currentQid:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(text="此題已作答完成!"),
                        ],
                    )
                )
                return
            thisOp = qMatch.group(2)
            addUserAns(uid=event.source.user_id, qid=thisQid, ans=thisOp)
            messages = [TextMessage(text=f"您選擇了 ({thisOp})!")]
            incCurrentQid(user_id=event.source.user_id)
            numOfQuestion = getQuestionDict()["number"]
            if thisQid >= numOfQuestion:
                calcPoints(event.source.user_id)
                messages.append(
                    TemplateMessage(
                        altText="作答結束",
                        template=ButtonsTemplate(
                            title="作答結束",
                            text="作答結束",
                            actions=[
                                PostbackAction(label="查看分數", data="check_score")
                            ],
                        ),
                    )
                )
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(replyToken=event.reply_token, messages=messages)
                )
                return
            messages.append(buildQuestionMessage(thisUserInfo.currentQid + 1))
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(replyToken=event.reply_token, messages=messages)
            )
        elif body == "check_score":
            messages = [buildScoreMessage(event.source.user_id)]
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=messages,
                )
            )


if __name__ == "__main__":
    initDB()
    app.run(port=8000)
