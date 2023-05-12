from flask import Flask, request, abort, send_file
from flask_ngrok import run_with_ngrok
import numpy as np
import cv2
import json
import jsonpickle
from linebot import *
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, FlexSendMessage
)
import requests
import pigpio
import time
import RPi.GPIO as GPIO
from gpiozero import MotionSensor
from gpiozero import LightSensor , Buzzer
import os

pir = MotionSensor(12)


ldr = LightSensor(16)

LED_RED_PIN = 4
LED_GREEN_PIN = 23
LED_BLUE_PIN = 20

# R=198
# G=81
# B=0
# # brightness
# bright_red = 128
# bright_green = 81

# print(os.path.isfile("/home/pi/Desktop/FINAL/settings.json"))  
# with open('/home/pi/Desktop/Alpha/settings.json') as outfile:
#       contents = outfile.read()
#       parsed_json = json.loads(contents)
# settings = {
#     "R_LED_Value" : parsed_json["R_LED_Value"],
#     "G_LED_Value" : parsed_json["G_LED_Value"],
#     "B_LED_Value" : parsed_json["B_LED_Value"],
#     "Led_State" : parsed_json[ "Led_State"],
#     "Takeimage" : parsed_json["Takeimage"],
#     "Detect" : parsed_json[ "Detect"]
# }
# print(settings)
settings = {
    "R_LED_Value" : 198,
    "G_LED_Value" : 81,
    "B_LED_Value" : 0,
    "Led_State" : "Off",
    "Takeimage" : False,
    "Detect" : False,
    "AUTO" : False 
}

def load_data():
  # print(os.path.isfile("/home/pi/Desktop/FINAL/settings.json"))  
  with open('/home/pi/Desktop/Alpha/settings.json') as outfile:
        contents = outfile.read()
        parsed_json = json.loads(contents)
  # print(parsed_json["Takeimage"])
  settings['R_LED_Value'] = parsed_json["R_LED_Value"]
  settings["G_LED_Value"] = parsed_json["G_LED_Value"]
  settings["B_LED_Value"] = parsed_json["B_LED_Value"]
  settings["Led_State"] = parsed_json[ "Led_State"]
  settings["Takeimage"] = parsed_json["Takeimage"]
  settings["Detect" ] = parsed_json[ "Detect"]
  settings["AUTO"] = parsed_json[ "AUTO"]
  print( settings)
  return settings

          
def log_config():
  with open("/home/pi/Desktop/Alpha/settings.json", "w") as outfile:
    json.dump(settings, outfile)
def setting_line():
  with open('/home/pi/Desktop/Alpha/settings.json') as outfile:
      contents = outfile.read()
      parsed_json = json.loads(contents)
      text_message = TextMessage(text=f'R_Value: {parsed_json["R_LED_Value"]} G_Value: {parsed_json["G_LED_Value"]} B_Value: {parsed_json["B_LED_Value"]} Led_State: {parsed_json["Led_State"]} Take image : {parsed_json["Takeimage"]}')
      line_bot_api.push_message('U4bb84e00414f4e136bd1a18e54942a39',text_message)
app = Flask(__name__)
line_bot_api = LineBotApi('10lA8h+YDK0gOq8dh/5SJ5uvkh+bLnZZ3kZXhgUZGds/uXUbMgCuN6BfHpnX/vhG8iM6x23WsQlgzu5qLfmgYOUlxSNtw2rPcuecsYQHZYJ0hQ6kJgrP8ojDfNv3VKg0GyeFfWrIg+bqmLfstV9dlgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('166ec362b97bf2da651407d8643e8ba7')

@app.route('/api/falldetect', methods=['GET'])
def get_image():
  filename = '/home/pi/Desktop/Alpha/saved_img.jpg'
  return send_file(filename, mimetype='image/jpeg')

@app.route("/", methods=['POST'])

def callback():
    # log_config() #reset settings.json
    body = request.get_data(as_text=True)
    req = request.get_json(silent=True, force=True)
    intent = req["queryResult"]["intent"]["displayName"]
    reply_token = req['originalDetectIntentRequest']['payload']['data']['replyToken']
    id = req['originalDetectIntentRequest']['payload']['data']['source']['userId']
    text = ''
    print(intent)
    load_data()
    if intent == 'TakeImage':
      settings['Takeimage'] = True
      # intent = [""]
      # log_config()
      # print(settings)
      print("WTF")
    if intent == 'LED Control':
      text = req['queryResult']['parameters']['state']
      if text != 'อัตโนมัติ':
         settings["AUTO"] = False
         log_config()
    if intent == 'LED Brightness - custom - custom':
      R = req['queryResult']['parameters']['r-value']
      G = req['queryResult']['parameters']['g-color']
      B = req['queryResult']['parameters']['b-value']
      print(R,G,B)
      settings['R_LED_Value'] = R
      settings['G_LED_Value'] = G
      settings['B_LED_Value'] = B
      # print(settings)
      log_config()
    # print(settings)
    disname = line_bot_api.get_profile(id).display_name
    led_mode_control(intent,text,reply_token,id,disname)
    log_config()
    # print(body)
    return 'OK'

def autoled():
    body = request.get_data(as_text=True)
    req = request.get_json(silent=True, force=True)
    intent = req["queryResult"]["intent"]["displayName"]
    reply_token = req['originalDetectIntentRequest']['payload']['data']['replyToken']
    id = req['originalDetectIntentRequest']['payload']['data']['source']['userId']
    text = ''
    with open('/home/pi/Desktop/Alpha/settings.json') as outfile:
            contents = outfile.read()
            parsed_json = json.loads(contents)
            r = parsed_json['R_LED_Value']
            g = parsed_json['G_LED_Value']
            b = parsed_json['B_LED_Value']
    if intent == 'LED Brightness - custom - custom':
      r = req['queryResult']['parameters']['r-value']
      g = req['queryResult']['parameters']['g-color']
      b = req['queryResult']['parameters']['b-value']
      print(r,g,b)
      settings['R_LED_Value'] = r
      settings['G_LED_Value'] = g 
      settings['B_LED_Value'] = b
      # print(settings)
      log_config()
    return r,g,b

def led_mode_control(intent,text,reply_token,id,disname):
  with open('/home/pi/Desktop/Alpha/settings.json') as outfile:
            contents = outfile.read()
            parsed_json = json.loads(contents)
            R = parsed_json['R_LED_Value']
            G = parsed_json['G_LED_Value']
            B = parsed_json['B_LED_Value']
  print(R,G,B)
  if intent == 'LED Control':
    if text == 'เปิด':
      text_message = TextSendMessage(text='เปิด LED')
      line_bot_api.push_message(id,text_message)
      pi = pigpio.pi()
      pi.set_PWM_frequency(LED_RED_PIN, 100)
      pi.set_PWM_frequency(LED_GREEN_PIN, 100)
      pi.set_PWM_frequency(LED_BLUE_PIN, 100)
      pi.set_PWM_dutycycle(LED_RED_PIN, R)
      pi.set_PWM_dutycycle(LED_GREEN_PIN, G)
      pi.set_PWM_dutycycle(LED_BLUE_PIN, B)
      settings['Led_State'] = "On"
      log_config()
      pi.stop()
    if text == 'ปิด':
      text_message = TextSendMessage(text='ปิด LED')
      line_bot_api.push_message(id,text_message)
      pi = pigpio.pi()
      pi.set_PWM_dutycycle(LED_RED_PIN, 0)
      pi.set_PWM_dutycycle(LED_GREEN_PIN, 0)
      pi.set_PWM_dutycycle(LED_BLUE_PIN, 0)
      settings['Led_State'] = "Off"
      log_config()
      pi.stop()
    if text == 'อัตโนมัติ':
      settings["AUTO"] = True
      log_config()
      text_message = TextSendMessage(text='เปิด LED อัตโนมัติ')
      line_bot_api.push_message(id,text_message)
      # pi.set_mode(4, pigpio.INPUT)
      while True:
            # callback()
            pi = pigpio.pi()
            time.sleep(0.5)
            load_data()
            if settings["AUTO"] == False:
               break
            # print(bool(ldr.value <= 0.1))
            # print(ldr.value)
            if ldr.value <= 0.1:
              # print('error')
              i=GPIO.input(12)
              # print(i)
              if i==1:                 
              # pir.wait_for_motion()
                print("You Moved")
                pi.set_PWM_frequency(LED_RED_PIN, 100)
                pi.set_PWM_frequency(LED_GREEN_PIN, 100)
                pi.set_PWM_frequency(LED_BLUE_PIN, 100)
                pi.set_PWM_dutycycle(LED_RED_PIN, R)
                pi.set_PWM_dutycycle(LED_GREEN_PIN, G)
                pi.set_PWM_dutycycle(LED_BLUE_PIN, B)
                # print("setting")
                settings['Led_State'] = "On"
                # print('before')
                log_config()
                # print('after')
                time.sleep(10)
              else:               
                if settings['Detect'] == False:
                  print("detect false")
                  # pir.wait_for_no_motion()
                  pi.set_PWM_dutycycle(LED_RED_PIN, 0)
                  pi.set_PWM_dutycycle(LED_GREEN_PIN, 0)
                  pi.set_PWM_dutycycle(LED_BLUE_PIN, 0)
                  settings['Led_State'] = "Off"
                  log_config()
            else:
                print('light')
                pi.set_PWM_dutycycle(LED_RED_PIN, 0)
                pi.set_PWM_dutycycle(LED_GREEN_PIN, 0)
                pi.set_PWM_dutycycle(LED_BLUE_PIN, 0)
                settings['Led_State'] = "Off"
                log_config()
            pi.stop()
            print('before')
            R,G,B = autoled()
               
  if intent == 'LED Brightness - Auto':
    print('LED Auto')
    pi = pigpio.pi()
    pi.set_PWM_dutycycle(LED_RED_PIN, 128)
    pi.set_PWM_dutycycle(LED_GREEN_PIN, 81)
    settings['R_LED_Value'] = 128
    settings['G_LED_Value'] = 81
    settings['B_LED_Value'] = 0
    log_config()
    pi.stop() 
  if intent == 'LED Brightness - custom - custom':
    print('LED Custom')
    pi = pigpio.pi()
    pi.set_PWM_dutycycle(LED_RED_PIN, R)
    pi.set_PWM_dutycycle(LED_GREEN_PIN, G)    
    pi.set_PWM_dutycycle(LED_BLUE_PIN, B)
    # settings['R_LED_Value'] = R
    # settings['G_LED_Value'] = G
    # settings['B_LED_Value'] = B
    # print(settings)
    log_config()
    pi.stop()
  if intent == "Settings":
    setting_line()
if __name__ == "__main__":
  app.run(debug=True)
  