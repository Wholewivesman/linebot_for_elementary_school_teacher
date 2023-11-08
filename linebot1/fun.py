from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import WebhookParser
from linebot.models import *
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError

import time
import emoji

#將資料庫資訊引進來
from linebot1.models import *

line_api = LineBotApi(channel_access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(channel_secret=settings.LINE_CHANNEL_SECRET)

first = emoji.emojize(":1st_place_medal:")
second = emoji.emojize(":2nd_place_medal:")
third = emoji.emojize(":3rd_place_medal:")

imageA = 'https://imgur.com/2QJLKzT.jpg'
imageB = 'https://imgur.com/HZDoIcK.jpg'
imageC = 'https://imgur.com/6I6MiO7.jpg'
imageD = 'https://imgur.com/UqHjhWX.jpg'
imageE = 'https://imgur.com/BEAeKu9.jpg'
imageOA = 'https://imgur.com/MtgzbzL.jpg'
imageOB = 'https://imgur.com/2K3TqyB.jpg'
imageOC = 'https://imgur.com/DTwaNkY.jpg'
imageOD = 'https://imgur.com/yv3qckR.jpg'
imageOE = 'https://imgur.com/buPXJhF.jpg'


#測驗開始
def test_start(event, qid, user_id):
    if Tests.objects.filter(qid = int(qid)).exists() == False:
        line_api.reply_message(event.reply_token, TextMessage(text=f'發生錯誤，題目不存在'))
    else:
        #玩家狀態更改
        User_Info.objects.filter(uid=user_id).update(now_state=f'test+{qid}')

        #確認題目類型
        test = Tests.objects.get(qid = int(qid))
        if test.show_type == 'B1':
            B1(event, qid)
        elif test.show_type == 'F1':
            F1(event, qid)
        elif test.show_type == 'F2':
            F2(event, qid, '')
        elif test.show_type == 'F3':
            F3(event, qid)

#測驗結束
def test_end(user_id):
    #玩家狀態更改
    User_Info.objects.filter(uid=user_id).update(now_state='default')

    #詢問是否查看積分
    message = []
    message.append(TextMessage(text=f'測驗結束，可以重新輸入"測驗開始"來開始測驗'))
    message.append(TemplateSendMessage(
                        alt_text='測驗結束，是否查看積分',
                        template=ConfirmTemplate(
                            title='查看積分',
                            text='測驗結束，是否查看積分',
                            actions=[                              
                                PostbackTemplateAction(label='查看積分',text='*查看積分*',data='cscore+1'),
                                PostbackTemplateAction(label='不查看積分',text='*不查看積分*',data='cscore+0')
                            ]
                        )
                    )
                )
    return message

#確認玩家狀態
def comfirm_state(event, user_id, display_name, user_state):
    if User_Info.objects.filter(uid = user_id).exists() == False:
        line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您尚未建立玩家資料\n請輸入"建立玩家"後，即可開始測驗'))
        return 0
    else:
        state = User_Info.objects.get(uid = user_id).now_state
        #print(f'user_state = {user_state}')
        if str(state) != str(user_state):
            #玩家非回答該題狀態
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您目前無回答此題的權限，可以輸入"測驗結束"，並重新開始喔'))
            return 0
    
    return 1

#建立排名
def establish_ranking():
    #取出大家的分數，並做出排序
    user_score_list = User_Info.objects.all().order_by('-points')
    count = 0
    highest = 101
    
    if ranking.objects.all().exists() == True:
        return 0

    #依照分數建立ranking
    for user in user_score_list:
        if user.points < highest:
            highest = user.points
            count += 1
        ranking.objects.create(rank=count, uid=user.uid, name=user.name, points=user.points)
    
    return 1


#列印排名
def print_ranking(event, user_id):
    #
    t = time.localtime()
    time_now = time.strftime("%Y/%m/%d %H:%M", t)

    rank_list = [
        BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(
                    text="名次",
                    size="sm"
                ),
                TextComponent(
                    text="玩家名字",
                    size="sm",
                    position="absolute",
                    offset_start="30%"
                ),
                TextComponent(
                    text="分數",
                    size="sm",
                    align="end",
                    position="absolute",
                    offset_end="0%"
                )
            ]
        ),
        SeparatorComponent(
            margin="xs"
        )
    ]

    #從資料庫取得排名
    for k in range(1,4):
        user_rank_list = ranking.objects.filter(rank = k)

        ranks = ''
        for user in user_rank_list:
            if user.rank == 1:
                ranks = f'{first}'
            else:
                ranks = str(user.rank)
            #每多一人就增加一行
            rank_list.append(
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(
                            text=f"{ranks}",
                            size="sm",
                        ),
                        TextComponent(
                            text=f"{user.name}",
                            size="sm",
                            position="absolute",
                            offset_start="30%"
                        ),
                        TextComponent(
                            text=f"{user.points}",
                            size="sm",
                            position="absolute",
                            align="end",
                            offset_end="0%"
                        )
                    ]
                )
            )

    message = []

    users = ranking.objects.get(uid=user_id)
    ranks = ''
    if users.rank == 1:
        ranks = f'第{users.rank}名{first}'
    else:
        ranks = f'第{users.rank}名'

    try:
        bubble = BubbleContainer(
            direction='ltr',
            body = BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(
                        text="你的名次",
                        weight="bold",
                        color="#1DB446",
                        size="sm",
                    ),
                    BoxComponent(
                        layout="baseline",
                        contents=[
                            TextComponent(
                                text=f"{ranks}",
                                weight="bold",
                                size="xxl",
                                margin="md",
                                offset_start="7%",
                                flex=4
                            ),
                            TextComponent(
                                text="總分為",
                                align="start",
                                flex=2
                            ),
                            TextComponent(
                                text=f"{users.points}",
                                size="lg",
                                align="center",
                                flex=2,
                                weight="bold",
                            ),
                            TextComponent(
                                text="分",
                                align="end",
                                flex=1
                            )
                        ]
                    ),
                    TextComponent(
                        text=f"{time_now}",
                        size="xs",
                        color="#aaaaaa",
                    ),
                    BoxComponent(
                        layout="vertical",
                        margin="xxl",
                        spacing="sm",
                        #rank_list放在這裡
                        contents=rank_list
                    )
                ]
            )
        )
        
        message.append(FlexSendMessage(alt_text="名次表",contents=bubble))
        line_api.reply_message(event.reply_token, message)
        
    except:
        message.append(TextSendMessage(text=f'名次輸出發生錯誤'))
        line_api.reply_message(event.reply_token, message)


#玩家答案寫入資料庫
def write_score(user_id, qid, user_ans):
    if User_ans.objects.filter(uid = user_id, qid = qid).exists() == False:
        User_ans.objects.create(uid = user_id, qid = qid, user_ans=user_ans)
    else:
        #已有資料->可以選擇不要更新或更新
        #要更新
        User_ans.objects.filter(uid = user_id, qid = qid).update(user_ans=user_ans)

        #不更新
        #return

#印出玩家答案及積分
def print_score(event, user_id):
    #
    t = time.localtime()
    time_now = time.strftime("%Y/%m/%d %H:%M", t)

    score_list = [
        BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(
                    text="題號",
                    size="sm",
                ),
                TextComponent(
                    text="你的答案",
                    size="sm",
                    position="absolute",
                    offset_start="20%"
                ),
                TextComponent(
                    text="正確答案",
                    size="sm",
                    position="absolute",
                    offset_start="50%"
                ),
                TextComponent(
                    text="獲得分數",
                    size="sm",
                    align="end",
                    position="absolute",
                    offset_end="0%"
                )
            ]
        ),
        SeparatorComponent(
            margin="xs"
        )
    ]

    #從資料庫取得成績
    user_score_list = User_ans.objects.filter(uid = user_id).order_by('qid')
    all_points = 0
    for user in user_score_list:
        ans = Tests.objects.get(qid = user.qid).ans
        points = 0
        if user.user_ans == ans:
            points = 10
            all_points += 10
        #每多一題就增加一行
        score_list.append(
            BoxComponent(
                layout="horizontal",
                contents=[
                    TextComponent(
                        text=f"{user.qid}",
                        size="sm",
                    ),
                    TextComponent(
                        text=f"({user.user_ans})",
                        size="sm",
                        position="absolute",
                        offset_start="20%"
                    ),
                    TextComponent(
                        text=f"({ans})",
                        size="sm",
                        position="absolute",
                        offset_start="50%"
                    ),
                    TextComponent(
                        text=f"{points}/10",
                        size="sm",
                        position="absolute",
                        align="end",
                        offset_end="0%"
                    )
                ]
            )
        )


    message = []

    try:
        bubble = BubbleContainer(
            direction='ltr',
            body = BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(
                        text="你的分數",
                        weight="bold",
                        color="#1DB446",
                        size="sm",
                    ),
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            TextComponent(
                                text=f"{all_points}",
                                weight="bold",
                                size="3xl",
                                margin="md",
                                offset_start="7%"
                            ),
                            TextComponent(
                                text="/100",
                                size="md",
                                position="absolute",
                                offset_bottom="10%",
                                offset_start="28%"
                            )
                        ]
                    ),
                    TextComponent(
                        text=f"{time_now}",
                        size="xs",
                        color="#aaaaaa",
                    ),
                    BoxComponent(
                        layout="vertical",
                        margin="xxl",
                        spacing="sm",
                        #score_list放在這裡
                        contents=score_list
                    )
                ]
            )
        )
        
        message.append(FlexSendMessage(alt_text="分數",contents=bubble))
        line_api.reply_message(event.reply_token, message)
        
    except:
        message.append(TextSendMessage(text=f'成績輸出發生錯誤'))
        line_api.reply_message(event.reply_token, message)


def B1(event, qid):
    #問題：文字(在按鈕上)
    #選項：文字(在按鈕上)
    #回答方式：按鈕

    test = Tests.objects.get(qid = int(qid))

    #答案
    ANS = test.ans

    line_api.reply_message(event.reply_token, 
                           TemplateSendMessage(
                                alt_text=f'第{qid}題',
                                template=ButtonsTemplate(
                                    title=f'第{qid}題',
                                    text=f'{test.question}',
                                    thumbnail_image_url='https://i.imgur.com/D4a3Ale.jpg',
                                    actions=[
                                            #data為內部回傳資訊，使用者看不到
                                            PostbackTemplateAction(label=f'(A){test.opA}', text='*已選擇(A)*', data=f"a{qid}+A+{ANS}"),
                                            PostbackTemplateAction(label=f'(B){test.opB}', text='*已選擇(B)*', data=f"a{qid}+B+{ANS}"),
                                            PostbackTemplateAction(label=f'(C){test.opC}', text='*已選擇(C)*', data=f"a{qid}+C+{ANS}"),
                                            PostbackTemplateAction(label=f'(D){test.opD}', text='*已選擇(D)*', data=f"a{qid}+D+{ANS}")
                                    ]
                                )
                            )
                        )
    

def F1(event, qid):
    #單選
    #問題：文字
    #選項：文字
    #回答方式：圖片製成的按鈕
    
    test = Tests.objects.get(qid = int(qid))

    #答案
    ANS = test.ans

    try:
        bubble = BubbleContainer(
            direction='ltr',
            header= BoxComponent(
                layout = 'vertical',
                background_color='#00B900',
                contents = [
                    TextComponent(text=f'第{qid}題', color='#FFFFFF')]
            ),
            body = BoxComponent(
                layout = 'vertical',
                contents = [
                    BoxComponent(
                        layout = 'vertical', 
                        margin='lg',
                        contents=[
                            TextComponent(text=f'{test.question}',size="xl", weight="bold"),
                            BoxComponent(
                                layout="vertical",
                                margin="lg",
                                spacing="sm",
                                contents=[
                                    BoxComponent(
                                        layout="baseline",
                                        spacing="sm",
                                        contents=[
                                            TextComponent(text="(A)",color="#aaaaaa", size="md", flex=1),
                                            TextComponent(text=f"{test.opA}",color="#666666", size="md", wrap=True, flex=7)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="baseline",
                                        spacing="sm",
                                        contents=[
                                            TextComponent(text="(B)",color="#aaaaaa", size="md", flex=1),
                                            TextComponent(text=f"{test.opB}",color="#666666", size="md", wrap=True, flex=7)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="baseline",
                                        spacing="sm",
                                        contents=[
                                            TextComponent(text="(C)",color="#aaaaaa", size="md", flex=1),
                                            TextComponent(text=f"{test.opC}",color="#666666", size="md", wrap=True, flex=7)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="baseline",
                                        spacing="sm",
                                        contents=[
                                            TextComponent(text="(D)",color="#aaaaaa", size="md", flex=1),
                                            TextComponent(text=f"{test.opD}",color="#666666", size="md", wrap=True, flex=7)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="baseline",
                                        spacing="sm",
                                        contents=[
                                            TextComponent(text="(E)",color="#aaaaaa", size="md", flex=1),
                                            TextComponent(text=f"{test.opE}",color="#666666", size="md", wrap=True, flex=7)
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ),
            footer = BoxComponent(
                layout='horizontal',
                contents=[
                    ImageComponent(
                        url=imageA,
                        size="lg",
                        aspect_mode="cover",
                        action=PostbackTemplateAction(
                            label='A',
                            text='*已選擇(A)*',
                            data=f'a{qid}+A+{ANS}'
                        )
                    ),
                    ImageComponent(
                        url=imageB,
                        size="lg",
                        aspect_mode="cover",
                        action=PostbackTemplateAction(
                            label='B',
                            text='*已選擇(B)*',
                            data=f'a{qid}+B+{ANS}'
                        )
                    ),
                    ImageComponent(
                        url=imageC,
                        size="lg",
                        aspect_mode="cover",
                        action=PostbackTemplateAction(
                            label='C',
                            text='*已選擇(C)*',
                            data=f'a{qid}+C+{ANS}'
                        )
                    ),
                    ImageComponent(
                        url=imageD,
                        size="lg",
                        aspect_mode="cover",
                        action=PostbackTemplateAction(
                            label='D',
                            text='*已選擇(D)*',
                            data=f'a{qid}+D+{ANS}'
                        )
                    ),
                    ImageComponent(
                        url=imageE,
                        size="lg",
                        aspect_mode="cover",
                        action=PostbackTemplateAction(
                            label='E',
                            text='*已選擇(E)*',
                            data=f'a{qid}+E+{ANS}'
                        )
                    ),
                ]
            )
        )
        
        message = []
        message.append(FlexSendMessage(alt_text=f"第{qid}題",contents=bubble))
        line_api.reply_message(event.reply_token, message)
        
    except:
        line_api.reply_message(event.reply_token,TextSendMessage(text=f'第{qid}題發生錯誤'))


def multi_chose(chosen:str, next_choose:str):
    if (next_choose in chosen):
        chosen = chosen.replace(next_choose,'')
    else:
        chosen += next_choose
        chosen_list = list(chosen)
        chosen_list.sort()
        #list轉string
        chosen = ''.join(chosen_list)
    return chosen



def F2(event, qid, chosen):
    #多選
    #問題：文字
    #選項：文字
    #回答方式：圖片製成的按鈕、按鈕

    #
    urla = imageA
    urlb = imageB
    urlc = imageC
    urld = imageD
    urle = imageE

    if('A' in chosen):
        urla = imageOA
    if('B' in chosen):
        urlb = imageOB
    if('C' in chosen):
        urlc = imageOC
    if('D' in chosen):
        urld = imageOD
    if('E' in chosen):
        urle = imageOE
    
    #選項更新
    new_chosen_a = multi_chose(chosen, "A")
    new_chosen_b = multi_chose(chosen, "B")
    new_chosen_c = multi_chose(chosen, "C")
    new_chosen_d = multi_chose(chosen, "D")
    new_chosen_e = multi_chose(chosen, "E")
    
    


    test = Tests.objects.get(qid = int(qid))

    #答案
    ANS = test.ans
    if chosen == '':
        try:
            bubble = BubbleContainer(
                direction='ltr',
                header= BoxComponent(
                    layout = 'vertical',
                    background_color='#00B900',
                    contents = [
                        TextComponent(text=f'第{qid}題', color='#FFFFFF')]
                ),
                body = BoxComponent(
                    layout = 'vertical',
                    contents = [
                        BoxComponent(
                            layout = 'vertical', 
                            margin='lg',
                            contents=[
                                TextComponent(text=f'{test.question}',size="xl", weight="bold"),
                                BoxComponent(
                                    layout="vertical",
                                    margin="lg",
                                    spacing="sm",
                                    contents=[
                                        BoxComponent(
                                            layout="baseline",
                                            spacing="sm",
                                            contents=[
                                                TextComponent(text="(A)",color="#aaaaaa", size="md", flex=1),
                                                TextComponent(text=f"{test.opA}",color="#666666", size="md", wrap=True, flex=7)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="baseline",
                                            spacing="sm",
                                            contents=[
                                                TextComponent(text="(B)",color="#aaaaaa", size="md", flex=1),
                                                TextComponent(text=f"{test.opB}",color="#666666", size="md", wrap=True, flex=7)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="baseline",
                                            spacing="sm",
                                            contents=[
                                                TextComponent(text="(C)",color="#aaaaaa", size="md", flex=1),
                                                TextComponent(text=f"{test.opC}",color="#666666", size="md", wrap=True, flex=7)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="baseline",
                                            spacing="sm",
                                            contents=[
                                                TextComponent(text="(D)",color="#aaaaaa", size="md", flex=1),
                                                TextComponent(text=f"{test.opD}",color="#666666", size="md", wrap=True, flex=7)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="baseline",
                                            spacing="sm",
                                            contents=[
                                                TextComponent(text="(E)",color="#aaaaaa", size="md", flex=1),
                                                TextComponent(text=f"{test.opE}",color="#666666", size="md", wrap=True, flex=7)
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                footer = BoxComponent(
                    layout='vertical',
                    contents=[
                        BoxComponent(
                            layout="horizontal",
                            contents=[
                                ImageComponent(
                                    url=f"{urla}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='A',
                                        text=f'*目前選擇({new_chosen_a})*',
                                        data=f'F2{qid}+{new_chosen_a}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urlb}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='B',
                                        text=f'*目前選擇({new_chosen_b})*',
                                        data=f'F2{qid}+{new_chosen_b}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urlc}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='C',
                                        text=f'*目前選擇({new_chosen_c})*',
                                        data=f'F2{qid}+{new_chosen_c}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urld}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='D',
                                        text=f'*目前選擇({new_chosen_d})*',
                                        data=f'F2{qid}+{new_chosen_d}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urle}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='E',
                                        text=f'*目前選擇({new_chosen_e})*',
                                        data=f'F2{qid}+{new_chosen_e}'
                                    )
                                )
                            ]
                        ),
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                TextComponent(
                                    text="此題為多選題",
                                    margin="xl",
                                    size="xxs",
                                    align="center",
                                ),
                                TextComponent(
                                    text="選擇一個選項後，將會新按鈕可選擇其他選項",
                                    size="xxs",
                                    align="center",
                                )
                            ]
                        )
                    ]
                )
            )
            
            message = []
            message.append(FlexSendMessage(alt_text=f"第{qid}題",contents=bubble))
            # message.append(TemplateSendMessage(
            #     alt_text=f'你目前選的答案為{chosen}，請點選送出答案以完成此多選題',
            #     template=ButtonsTemplate(
            #         title='送出答案',
            #         text=f'你目前選的答案為({chosen})，請點選送出答案以完成此多選題',
            #         thumbnail_image_url="https://i.imgur.com/D4a3Ale.jpg",
            #         actions=[                              
            #             PostbackTemplateAction(
            #                 label='送出答案',
            #                 text=f'*已選擇({chosen})*',
            #                 data=f'a{qid}+{chosen}+{ANS}'
            #             )
            #         ]
            #     )
            # ))
            line_api.reply_message(event.reply_token, message)
        except:
            line_api.reply_message(event.reply_token,TextSendMessage(text=f'第{qid}題發生錯誤'))
    else:
        try:
            bubble = BubbleContainer(
                direction='ltr',
                header= BoxComponent(
                    layout = 'vertical',
                    background_color='#00B900',
                    contents = [
                        TextComponent(text=f'第{qid}題', color='#FFFFFF')]
                ),
                footer = BoxComponent(
                    layout='vertical',
                    contents=[
                        BoxComponent(
                            layout="horizontal",
                            contents=[
                                ImageComponent(
                                    url=f"{urla}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='A',
                                        text=f'*目前選擇({new_chosen_a})*',
                                        data=f'F2{qid}+{new_chosen_a}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urlb}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='B',
                                        text=f'*目前選擇({new_chosen_b})*',
                                        data=f'F2{qid}+{new_chosen_b}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urlc}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='C',
                                        text=f'*目前選擇({new_chosen_c})*',
                                        data=f'F2{qid}+{new_chosen_c}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urld}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='D',
                                        text=f'*目前選擇({new_chosen_d})*',
                                        data=f'F2{qid}+{new_chosen_d}'
                                    )
                                ),
                                ImageComponent(
                                    url=f"{urle}",
                                    size="lg",
                                    aspect_mode="cover",
                                    action=PostbackTemplateAction(
                                        label='E',
                                        text=f'*目前選擇({new_chosen_e})*',
                                        data=f'F2{qid}+{new_chosen_e}'
                                    )
                                )
                            ]
                        ),
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                TextComponent(
                                    text="此題為多選題",
                                    margin="xl",
                                    size="xxs",
                                    align="center",
                                ),
                                TextComponent(
                                    text="按下選過的選項即可取消回答",
                                    size="xxs",
                                    align="center",
                                ),
                                TextComponent(
                                    text="確認答案無誤後，請按下完成作答",
                                    size="xxs",
                                    align="center",
                                ),
                                ButtonComponent(
                                    margin="xl",
                                    style="primary",
                                    action=PostbackAction(
                                            label='完成作答',
                                            text=f'*已選擇({chosen})*',
                                            data=f'a{qid}+{chosen}+{ANS}'
                                        )
                                    
                                )
                            ]
                        )
                    ]
                )
            )
            
            message = []
            message.append(FlexSendMessage(alt_text=f"第{qid}題",contents=bubble))
            # message.append(TemplateSendMessage(
            #     alt_text=f'你目前選的答案為{chosen}，請點選送出答案以完成此多選題',
            #     template=ButtonsTemplate(
            #         title='送出答案',
            #         text=f'你目前選的答案為({chosen})，請點選送出答案以完成此多選題',
            #         thumbnail_image_url="https://i.imgur.com/D4a3Ale.jpg",
            #         actions=[                              
            #             PostbackTemplateAction(
            #                 label='送出答案',
            #                 text=f'*已選擇({chosen})*',
            #                 data=f'a{qid}+{chosen}+{ANS}'
            #             )
            #         ]
            #     )
            # ))
            
            line_api.reply_message(event.reply_token, message)
        except:
            line_api.reply_message(event.reply_token,TextSendMessage(text=f'第{qid}題發生錯誤'))


def F3(event, qid):
    #圖片單選
    #問題：文字
    #選項：圖片
    #回答方式：圖片按鈕
    
    test = Tests.objects.get(qid = int(qid))

    #答案
    ANS = test.ans

    try:
        bubble = BubbleContainer(
            direction='ltr',
            header= BoxComponent(
                layout = 'vertical',
                background_color='#00B900',
                contents = [
                    TextComponent(text=f'第{qid}題', color='#FFFFFF')]
            ),
            hero = BoxComponent(
                layout = 'vertical',
                contents = [
                    TextComponent(
                        text=f"{test.question}",
                        margin="md",
                        size="xl",
                        weight="bold",
                        offset_start="5%"
                    ),
                    BoxComponent(
                        layout = 'horizontal', 
                        contents=[
                            ImageComponent(
                                url=f"{test.opA}",
                                action=PostbackAction(
                                    label='A',
                                    text='*已選擇(A)*',
                                    data=f'a{qid}+A+{ANS}'
                                )
                            ),
                            ImageComponent(
                                url=f"{test.opB}",
                                action=PostbackAction(
                                    label='B',
                                    text='*已選擇(B)*',
                                    data=f'a{qid}+B+{ANS}'
                                )
                            )
                        ]
                    ),
                    BoxComponent(
                        layout = 'horizontal', 
                        contents=[
                            ImageComponent(
                                url=f"{test.opC}",
                                action=PostbackAction(
                                    label='C',
                                    text='*已選擇(C)*',
                                    data=f'a{qid}+C+{ANS}'
                                )
                            ),
                            ImageComponent(
                                url=f"{test.opD}",
                                action=PostbackAction(
                                    label='D',
                                    text='*已選擇(D)*',
                                    data=f'a{qid}+D+{ANS}'
                                )
                            )
                        ]
                    )
                ]
            )
        )
        
        message = []
        message.append(FlexSendMessage(alt_text=f"第{qid}題",contents=bubble))
        line_api.reply_message(event.reply_token, message)
        
    except:
        line_api.reply_message(event.reply_token,TextSendMessage(text=f'第{qid}題發生錯誤'))