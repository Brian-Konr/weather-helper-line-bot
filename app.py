import os
import requests
from dotenv import load_dotenv

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

load_dotenv()
app = Flask(__name__)

channel_access_token = os.getenv("LINE_CHANNEL_TOKEN")
channel_secrets = os.getenv("LINE_CHANNEL_SECRETS")

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secrets)

@app.route("/")
def hello_world():
    return "Hello World!"

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
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    weather, rain, temp = get_weather_temp_n_rain()
    message = generate_response(weather, rain, temp)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))

def get_weather_temp_n_rain():
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-D0047-061?Authorization=CWB-6C11428A-C0C8-4DF7-9C96-CDADAE01D506'
    data = requests.get(url)   
    data_json = data.json()   
    rain1 = data_json['records']['locations'][0]['location'][6]['weatherElement'][0]['time'][0]['elementValue'][0]['value']
    rain2 = data_json['records']['locations'][0]['location'][6]['weatherElement'][0]['time'][1]['elementValue'][0]['value']
    rain = (int(rain1)+int(rain2))/2
    Rain = int(rain) #整日平均降雨機率
    temp = data_json['records']['locations'][0]['location'][6]['weatherElement'][3]['time'][3]['elementValue'][0]['value'] 
    Temp = temp #早上九點溫度
    weather = data_json['records']['locations'][0]['location'][6]['weatherElement'][1]['time'][3]['elementValue'][0]['value'] #早上九點天氣現象

    return weather, Rain, Temp

def generate_response(weather, rain, temp):
    temp = int(temp)
    message = f"你好，今天是{weather}天，"
    
    if temp <= 12 :
        message += "超級寒流！建議搭配手套圍巾厚外套，盡量待在室內並全力保暖！"
    if temp > 12 and temp <= 18 :
        message += "氣溫寒冷建議搭配較厚外套禦寒"
    if temp > 18 and temp <= 23 :
        message += "溫涼爽，建議攜帶薄外套備著即可！"
    if temp > 23 and temp <= 26  :
        message += "溫暖舒適的溫度~”"
    if temp > 26 and temp <= 31  :
        message += "略感炎熱，記得適時補充水分！"
    if temp > 31 and temp <= 36 :
        message += "炎熱！記得適時補充水分！"
    if temp > 36 :
        message += "極度炎熱！記得防曬、注意散熱、多喝水並避免戶外活動！"
    if rain >= 70 :
        message += "提醒您，看起來今天很有可能會下雨，如果要出門記得帶雨傘，騎車要記得帶雨衣唷！\n"
    if rain > 30 and rain <70 :
        message += "體醒您，今天如果帶著傘可能會很幸運！"
    if rain < 10:
        message += "恭喜您，今天看來不會下雨！"
     
    return message


if __name__ == "__main__":
    app.run()