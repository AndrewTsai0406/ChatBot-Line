"""
A line chatbot implementation which is capable of handling Chinese and English conversation.
Besides, it is able to to the following tasks:
    
    1.text2img generation
    2.deepdream img generation
    3.image captioning
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import conversational_chat_bot #https://github.com/yangjianxin1/GPT2-chitchat
import meena.predict as predict #https://github.com/frankplus/meena-chatbot
from langdetect import detect #https://pypi.org/project/langdetect/

from PIL import Image
import requests,io,pickle,os

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('@@@@@@@@@@')
# Channel Secret
handler = WebhookHandler('@@@@@@@@@@')
#Store users' current status
User_status={}
#flex message
with open('flex.pickle', 'rb') as handle:
    flex_message = pickle.load(handle)
    
# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

#處理訊息
@handler.add(MessageEvent)
def handle_message(event):
    userid=event.source.user_id
    try:
        _ = User_status[userid]
    except KeyError:
        User_status[userid]='text'
    
    if event.message.type=='text':
        if event.message.text.lower() in ['-h','help','h','"h"']:
            message = FlexSendMessage(alt_text='展示功能',contents=flex_message)
            line_bot_api.reply_message(event.reply_token, message)
            
        elif User_status[userid]=='txt2img':
            User_status[userid]='text'
            r = requests.post(
                "https://api.deepai.org/api/text2img",
                data={
                    'text': event.message.text,
                }, 
                headers={'api-key': '28601fe0-4849-4678-8319-91a829f7e36c'})
            message = ImageSendMessage(
            original_content_url=r.json()['output_url'],
            preview_image_url=r.json()['output_url'])
            line_bot_api.reply_message(event.reply_token, message)
            
        elif detect(event.message.text) in ['ko','zh-cn','zh-tw']:
            #https://github.com/yangjianxin1/GPT2-chitchat
            text=conversational_chat_bot.being_called(userid,event.message.text)
            message = TextSendMessage(text=''.join(text)+'\nType "h" for help')
            line_bot_api.reply_message(event.reply_token, message)
            
        else:
            #https://github.com/frankplus/meena-chatbot
            text=predict.predict(event.message.text)[0]
            message = TextSendMessage(text=''.join(text)+'\nType "h" for help')
            line_bot_api.reply_message(event.reply_token, message)
        
    elif event.message.type=='image':
        img = line_bot_api.get_message_content(message_id=event.message.id)
        image = Image.open(io.BytesIO(img.content))
        image.save('1.jpg')
        
        if User_status[userid]=='text':
            message = TextSendMessage(text='To used image related features,please press the corresponding buttons. (-h for help)')
            line_bot_api.reply_message(event.reply_token, message)

        if User_status[userid]=='Deep_dream':
            User_status[userid]='text'
            r = requests.post(
                "https://api.deepai.org/api/deepdream",
                files={
                    'image': open('1.jpg', 'rb'),
                },
                headers={'api-key': '28601fe0-4849-4678-8319-91a829f7e36c'}
            )
            message = ImageSendMessage(
            original_content_url=r.json()['output_url'],
            preview_image_url=r.json()['output_url'])
            line_bot_api.reply_message(event.reply_token, message)
            
        elif User_status[userid]=='imgcap':
            User_status[userid]='text'
            r = requests.post(
                "https://api.deepai.org/api/neuraltalk",
                files={'image': open('1.jpg', 'rb'),
                },
                headers={'api-key': '28601fe0-4849-4678-8319-91a829f7e36c'}
            )
            message = TextSendMessage(text='Your photo has: '+r.json()['output'])
            line_bot_api.reply_message(event.reply_token, message)
            
    elif event.message.type=='sticker':
        message = TextSendMessage(text='Where can I get one of this sticker?')
        line_bot_api.reply_message(event.reply_token, message)        
    elif event.message.type=='audio':
        pass
    else:
        pass


@handler.add(PostbackEvent)
def handle_message(event):
    #Record which type of ervice is being requested
    userid=event.source.user_id
    try:
        _ = User_status[userid]
    except KeyError:
        User_status[userid]='text'
        
    if event.postback.data=='txt2img':
        userid=event.source.user_id
        User_status[userid]='txt2img'
        print('text2img===> ',User_status)
        message = TextSendMessage(text='Please start to describe an object:')
        line_bot_api.reply_message(event.reply_token, message)
        
    elif event.postback.data=='Deep_dream':
        userid=event.source.user_id
        User_status[userid]='Deep_dream'
        print('Deep_dream===> ',User_status)
        message = TextSendMessage(text='Please send me a picture to inference:')
        line_bot_api.reply_message(event.reply_token, message)
        
    elif event.postback.data=='imgcap':
        userid=event.source.user_id
        User_status[userid]='imgcap'
        print('imgcap===> ',User_status)
        message = TextSendMessage(text='Please send me a picture to inference:')
        line_bot_api.reply_message(event.reply_token, message)


@handler.add(FollowEvent)
def handle_message(event):
    #Record the new comers' info
    userid=event.source.user_id
    User_status[userid]='text'
    print('Follow===> ',User_status)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
