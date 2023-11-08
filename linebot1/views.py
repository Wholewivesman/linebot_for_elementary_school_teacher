from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt


# Create your views here.

from linebot import WebhookParser
from linebot.models import *
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError

import time

#將資料庫資訊引進來
from linebot1.models import *
from linebot1.fun import *

#現在狀態
mode = 0

line_api = LineBotApi(channel_access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(channel_secret=settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if event.type == 'message' and mode == 0:
                handle_message_state_0(event)
            if event.type == 'postback':
                handle_postback(event)
    
        return HttpResponse()
    else:
        return HttpResponseBadRequest()



def handle_postback(event):
    #得到user資訊
    display_name = line_api.get_profile(event.source.user_id).display_name
    user_id = line_api.get_profile(event.source.user_id).user_id
    picture_url = line_api.get_profile(event.source.user_id).picture_url
    
    #使用者的回傳訊息
    data = str(event.postback.data)

    #a開頭代表要回答問題
    if data[:1] == 'a':
        #取a以後的字
        data1 = data[1:]
        qid = data1.split('+')[0]
        user_ans = data1.split('+')[1]
        ans = data1.split('+')[2]

        #確認玩家狀態
        if comfirm_state(event, user_id, display_name, 'test+'+qid) == 0:
            return
        
        #玩家答案寫入資料庫
        write_score(user_id, qid, user_ans)

        
        #解析玩家答案
        if user_ans == ans:
            user_info = User_Info.objects.filter(uid = user_id)
            for user in user_info:
                points = int(user.points)
                User_Info.objects.filter(uid=user_id).update(points=points+10)
        
        #先檢查是否為最後一題
        if Tests.objects.filter(qid = int(qid)+1).exists() == False:
            #是最後一題
            messages = test_end(user_id)
            line_api.reply_message(event.reply_token, messages)
        else:
            #不是最後一題，進下一題
            test_start(event, int(qid)+1, user_id)
    elif data[:2] == 'F2':
        data1 = data[2:]
        qid = data1.split("+")[0]
        chosen = data1.split("+")[1]
        F2(event, qid, chosen)
        
    #c開頭表示查看成績
    elif data[:1] == 'c':
        data1 = data[1:]
        order = data1.split('+')[0]
        if order == 'score':
            #確認玩家是否在默認狀態
            if User_Info.objects.filter(uid = user_id).exists() == False:
                line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您尚未建立玩家資料\n請輸入"建立玩家"後，即可開始測驗'))
                return
            else:
                state = User_Info.objects.get(uid = user_id).now_state
                if str(state) != 'default':
                    #玩家非默認狀態
                    line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您目前非默認狀態，可以輸入"測驗結束"，重新回到默認狀態'))
                    return
            check = data1.split('+')[1]
            if check == '1':
                print_score(event, user_id)
                # user_info = User_Info.objects.filter(uid = user_id)
                # for user in user_info:
                #     points = int(user.points)
                # line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}~\n目前獲得{points}分！'))
    else:
        pass




def handle_message_state_0(event):
    #得到user資訊
    display_name = line_api.get_profile(event.source.user_id).display_name
    user_id = line_api.get_profile(event.source.user_id).user_id
    
    #使用者的訊息
    text = event.message.text

    #管理者指令區
    if '/' in text:
        #先確定是否為管理者
        if superuser.objects.filter(uid = user_id).exists() == False:
            try:
                order = text[1:]
            except:
                line_api.reply_message(event.reply_token, TextMessage(text='您非管理者，無權限輸入指令'))
            #非管理者
            if order == '加入管理者':
                superuser.objects.create(uid = user_id, name=display_name)
                line_api.reply_message(event.reply_token, TextMessage(text='成功建立管理者'))
            else:
                line_api.reply_message(event.reply_token, TextMessage(text='您非管理者，無權限輸入指令'))

        else:
            #管理者
            #管理者指令區，order即為指令
            order = text[1:]
            if order == '刪除管理者':
                superuser.objects.filter(uid = user_id).delete()
                line_api.reply_message(event.reply_token, TextMessage(text='已刪除管理者'))
            elif order == '加入管理者':
                line_api.reply_message(event.reply_token, TextMessage(text='已於先前加入管理者'))
            elif order == '清除玩家積分':
                User_Info.objects.all().update(points = 0)
                line_api.reply_message(event.reply_token, TextMessage(text='已清除所有玩家積分'))
            elif order == '清除回答紀錄':
                User_ans.objects.all().delete()
                line_api.reply_message(event.reply_token, TextMessage(text='已清除所有玩家回答紀錄'))
            elif order == '建立排名':
                if(establish_ranking()):
                    line_api.reply_message(event.reply_token, TextMessage(text='成功建立排名'))
                else:
                    line_api.reply_message(event.reply_token, TextMessage(text='請先刪除排名，再重新建立排名'))
            elif order == '刪除排名':
                ranking.objects.filter().delete()
                line_api.reply_message(event.reply_token, TextMessage(text='成功刪除排名'))
            else:
                line_api.reply_message(event.reply_token, TextMessage(text='無此指令'))
    #玩家指令區
    elif text == '建立玩家':
        if User_Info.objects.filter(uid = user_id).exists() == False:
            User_Info.objects.create(uid = user_id, name=display_name)
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，玩家資料已建立成功'))
        else:
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，玩家資料先前已建立'))
    elif text == '測驗開始':
        #一般測驗，隨時可以開始
        if User_Info.objects.filter(uid = user_id).exists() == False:
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您尚未建立玩家資料\n請輸入"建立玩家"後，即可開始測驗'))
        else:
            state = User_Info.objects.get(uid = user_id).now_state
            if state != 'default':
                line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您目前無回答此題的權限，可以輸入"測驗結束"，並重新開始喔'))
                return
            #測驗開始
            test_start(event, 1, user_id)
    elif text == '測驗結束':
        if User_Info.objects.filter(uid = user_id).exists() == False:
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，您尚未建立玩家資料\n請輸入"建立玩家"後，即可開始測驗'))
        else:
            messages = []
            messages = test_end(user_id)
            line_api.reply_message(event.reply_token, messages)
    elif text == '排名查詢':
        if ranking.objects.filter(rank = 1).exists() == False:
            line_api.reply_message(event.reply_token, TextMessage(text=f'{display_name}你好，老師尚未釋出排名'))
            return
        else:
            print_ranking(event, user_id)
    elif '*' in text:
        pass
        #line_api.reply_message(event.reply_token,TextMessage(text = '正在處裡'))
    elif text == '練習':
        line_api.reply_message(event.reply_token, FlexSendMessage(alt_text="000", contents={}))
    else:
        #回傳訊息
        line_api.reply_message(event.reply_token,TextMessage(text = text))


    