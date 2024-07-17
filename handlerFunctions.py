from linebot.v3.messaging import (
    PostbackAction,
    TemplateMessage,
    ButtonsTemplate,
    FlexBox,
    FlexSeparator,
    FlexBubble,
    FlexMessage,
    FlexText,
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from db import (
    getQuestion,
    getUserInfo,
    getQuestionDict,
    getUserAns,
    getUserRankingAsc,
)
import time
import requests
import json
from bs4 import BeautifulSoup


def buildQuestionMessage(qid):
    question = getQuestion(qid)
    if not question:
        return None
    message = TemplateMessage(
        alt_text=f"第{qid}題",
        template=ButtonsTemplate(
            title=f"第{qid}題",
            text=question["question"],
            actions=[
                PostbackAction(
                    label=f"(A) {question['opA']}",
                    data=f"q{qid}-A",
                ),
                PostbackAction(
                    label=f"(B) {question['opB']}",
                    data=f"q{qid}-B",
                ),
                PostbackAction(
                    label=f"(C) {question['opC']}",
                    data=f"q{qid}-C",
                ),
                PostbackAction(
                    label=f"(D) {question['opD']}",
                    data=f"q{qid}-D",
                ),
            ],
        ),
    )
    return message


def buildScoreMessage(uid):
    t = time.localtime()
    time_now = time.strftime("%Y/%m/%d %H:%M", t)
    userInfo = getUserInfo(user_id=uid)
    points = userInfo.points
    score_list = [
        FlexBox(
            layout="horizontal",
            contents=[
                FlexText(
                    text="題號",
                    size="sm",
                ),
                FlexText(
                    text="你的答案", size="sm", position="absolute", offset_start="20%"
                ),
                FlexText(
                    text="正確答案", size="sm", position="absolute", offset_start="50%"
                ),
                FlexText(
                    text="答對",
                    size="sm",
                    align="end",
                    position="absolute",
                    offset_end="0%",
                ),
            ],
        ),
        FlexSeparator(margin="xs"),
    ]
    questionDict = getQuestionDict()
    for i, q in enumerate(questionDict["questions"]):
        qid = i + 1
        thisUserAnsObj = getUserAns(uid, qid)
        thisUserAns = thisUserAnsObj.ans
        qAns = q["ans"]
        score_list.append(
            FlexBox(
                layout="horizontal",
                contents=[
                    FlexText(
                        text=f"{qid}",
                        size="sm",
                    ),
                    FlexText(
                        text=f"{thisUserAns}",
                        size="sm",
                        position="absolute",
                        offset_start="20%",
                    ),
                    FlexText(
                        text=f"{qAns}",
                        size="sm",
                        position="absolute",
                        offset_start="50%",
                    ),
                    FlexText(
                        text=f"{'O' if thisUserAns == qAns else 'X'}",
                        size="sm",
                        align="end",
                        position="absolute",
                        offset_end="0%",
                    ),
                ],
            ),
        )
    bubble = FlexBubble(
        direction="ltr",
        body=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text="你的分數",
                    weight="bold",
                    color="#1DB446",
                    size="sm",
                ),
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(
                            text=f"{points}",
                            weight="bold",
                            size="3xl",
                            margin="md",
                            offset_start="7%",
                        ),
                        FlexText(
                            text="  /100",
                            size="md",
                            position="absolute",
                            offset_bottom="10%",
                            offset_start="28%",
                        ),
                    ],
                ),
                FlexText(
                    text=f"{time_now}",
                    size="xs",
                    color="#aaaaaa",
                ),
                FlexBox(
                    layout="vertical",
                    margin="xxl",
                    spacing="sm",
                    contents=score_list,
                ),
            ],
        ),
    )

    message = FlexMessage(alt_text="分數", contents=bubble)
    return message


def buildRankingMessage(uid):
    t = time.localtime()
    time_now = time.strftime("%Y/%m/%d %H:%M", t)
    userInfo = getUserInfo(user_id=uid)
    points = userInfo.points
    rank_list = [
        FlexBox(
            layout="horizontal",
            contents=[
                FlexText(
                    text="名次",
                    size="sm",
                ),
                FlexText(
                    text="玩家名字", size="sm", position="absolute", offset_start="30%"
                ),
                FlexText(
                    text="分數",
                    size="sm",
                    align="end",
                    position="absolute",
                    offset_end="0%",
                ),
            ],
        ),
        FlexSeparator(margin="xs"),
    ]
    userInfos = getUserRankingAsc()
    if len(userInfos) == 0:
        return TextMessage(text="尚未釋出排名!")
    thisRank = 0
    user_ranking_list = []
    lastRank = 0
    lastPoints = 101
    for u in userInfos:
        if u.points < lastPoints:
            lastRank += 1
        lastPoints = u.points
        if u.uid == userInfo.uid:
            thisRank = lastRank
        user_ranking_list.append((u.uid, lastRank))
    for i in range(0, min(len(userInfos), 4)):
        thisUid = user_ranking_list[i][0]
        print(thisUid)
        thisUser = getUserInfo(user_id=thisUid)
        rank_list.append(
            FlexBox(
                layout="horizontal",
                contents=[
                    FlexText(
                        text=f"{user_ranking_list[i][1]}",
                        size="sm",
                    ),
                    FlexText(
                        text=f"{thisUser.name}",
                        size="sm",
                        position="absolute",
                        offset_start="30%",
                    ),
                    FlexText(
                        text=f"{thisUser.points}",
                        size="sm",
                        align="end",
                        position="absolute",
                        offset_end="0%",
                    ),
                ],
            ),
        )
    bubble = FlexBubble(
        direction="ltr",
        body=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text="你的名次",
                    weight="bold",
                    color="#1DB446",
                    size="sm",
                ),
                FlexBox(
                    layout="baseline",
                    contents=[
                        FlexText(
                            text=f"{thisRank}",
                            weight="bold",
                            size="xxl",
                            margin="md",
                            offset_start="7%",
                            flex=4,
                        ),
                        FlexText(text="總分為", align="start", flex=2),
                        FlexText(
                            text=f"{points}",
                            size="lg",
                            align="center",
                            flex=2,
                            weight="bold",
                        ),
                        FlexText(
                            text="分",
                            align="end",
                            flex=1,
                        ),
                    ],
                ),
                FlexText(
                    text=f"{time_now}",
                    size="xs",
                    color="#aaaaaa",
                ),
                FlexBox(
                    layout="vertical",
                    margin="xxl",
                    spacing="sm",
                    contents=rank_list,
                ),
            ],
        ),
    )

    message = FlexMessage(alt_text="名次表", contents=bubble)
    return message


def _getTitles(pageNo: int):
    r = requests.post(
        "https://cte.utaipei.edu.tw/app/index.php?Action=mobilercglist",
        {"Rcg": 357, "Op": "getpartlist", "Page": pageNo},
    )

    jsonData: dict = json.loads(r.text)
    # with open('download.html', 'w', encoding='utf-8') as f:
    #     f.write(jsonData['content'])
    content = "<html>" + jsonData["content"] + "</html>"
    soup = BeautifulSoup(content, "html.parser")
    titleList = []
    blocks = soup.find_all("a")
    for block in blocks:
        titleList.append(
            {
                "title": block["title"],
                "url": block["href"],
            }
        )
    return titleList


def buildScraperMessage():
    titles = _getTitles(1)
    text = ""
    for i, title in enumerate(titles[:10]):
        text += f"{i+1}. {title['title']}\n({title['url']})\n\n"
    # message = TemplateMessage(
    #     alt_text="公告",
    #     template=ButtonsTemplate(
    #         title="公告",
    #         text="公告",
    #         actions=actions,
    #     ),
    # )
    message = TextMessage(text=text)
    return message
