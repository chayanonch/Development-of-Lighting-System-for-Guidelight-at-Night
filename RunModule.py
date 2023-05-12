import mediapipe as mp # Import mediapipe
import cv2 # Import opencv
import numpy as np
import json
import os
import time
mp_drawing = mp.solutions.drawing_utils # Drawing helpers
mp_holistic = mp.solutions.holistic # Mediapipe Solutions
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score # Accuracy metrics 
import pickle 
from flask import Flask, request, abort, send_file
from flask_ngrok import run_with_ngrok
import numpy as np
import cv2
import jsonpickle
from linebot import *
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)
import requests
import pandas as pd

app = Flask(__name__)
line_bot_api = LineBotApi('10lA8h+YDK0gOq8dh/5SJ5uvkh+bLnZZ3kZXhgUZGds/uXUbMgCuN6BfHpnX/vhG8iM6x23WsQlgzu5qLfmgYOUlxSNtw2rPcuecsYQHZYJ0hQ6kJgrP8ojDfNv3VKg0GyeFfWrIg+bqmLfstV9dlgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('166ec362b97bf2da651407d8643e8ba7')

def detect_state(settings):
    with open("/home/pi/Desktop/Alpha/settings.json", "w") as outfile:
        json.dump(settings, outfile)
def take_image(settings):
    # print(settings)
    image_message = ImageSendMessage(original_content_url='https://fd35-49-228-162-116.ngrok-free.app/api/falldetect',preview_image_url='https://fd35-49-228-162-116.ngrok-free.app/api/falldetect')
    line_bot_api.push_message('U4bb84e00414f4e136bd1a18e54942a39',image_message)
    with open("/home/pi/Desktop/Alpha/settings.json", "w") as outfile:
        json.dump(settings, outfile)
def fall_detection():
   image_message = ImageSendMessage(original_content_url='https://fd35-49-228-162-116.ngrok-free.app/api/falldetect',preview_image_url='https://fd35-49-228-162-116.ngrok-free.app/api/falldetect')
   line_bot_api.push_message('U4bb84e00414f4e136bd1a18e54942a39',image_message)
   line_bot_api.push_message('U4bb84e00414f4e136bd1a18e54942a39',TextSendMessage(text='fall detecion!'))
with open('body_language.pkl', 'rb') as f:
    model = pickle.load(f)
cap = cv2.VideoCapture(0)
# Initiate holistic model
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    elapsed = 0 
    detect = 0 #เช็คว่าจับภาพได้10วิ
    none_detect = 0
    while cap.isOpened():
        with open('/home/pi/Desktop/Alpha/settings.json','r',encoding='utf-8') as outfile:
            contents = outfile.read()
            parsed_json = json.loads(contents)
            print(parsed_json)
            # if parsed_json["Takeimage"] == True:
            #     print(parsed_json["Takeimage"])
            #     break
        print(parsed_json["Takeimage"])
        ret, frame = cap.read()
        
        
        # Recolor Feed
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False        
        
        # Make Detections
        results = holistic.process(image)
        
        # Recolor image back to BGR for rendering
        image.flags.writeable = True   
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        
        # 1. Right hand
        mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                                mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4),
                                mp_drawing.DrawingSpec(color=(80,44,121), thickness=2, circle_radius=2)
                                )

        # 2. Left Hand
        mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                                mp_drawing.DrawingSpec(color=(121,22,76), thickness=2, circle_radius=4),
                                mp_drawing.DrawingSpec(color=(121,44,250), thickness=2, circle_radius=2)
                                )

        # 3. Pose Detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, 
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4),
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                )  
        
        # คำสั่งถ่ายภาพ save_img
        if parsed_json["Takeimage"] == True:
                cv2.imwrite(filename='saved_img.jpg', img=frame)
                cv2.waitKey(1650)
                parsed_json["Takeimage"] = False
                print(parsed_json["Takeimage"])
                take_image(parsed_json)
                print("Take Image!")
        # Export coordinates
        try:
            start = time.time()
            time.process_time() 
            # Extract Pose landmarks
            pose = results.pose_landmarks.landmark
            pose_row = list(np.array([[landmark.x, landmark.y, landmark.z, landmark.visibility] for landmark in pose]).flatten())      

            
            # Concate rows
            row = pose_row           

            # Make Detections
            X = pd.DataFrame([row])
            # print(type(X))
            
            
            body_language_class = model.predict(X)[0]
            body_language_prob = model.predict_proba(X)[0]
            # print(body_language_class, body_language_prob)

            # Grab ear coords
            coords = tuple(np.multiply(
                            np.array(
                                (results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_EAR].x, 
                                results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_EAR].y))
                        , [640,480]).astype(int))
            
            cv2.rectangle(image, 
                        (coords[0], coords[1]+5), 
                        (coords[0]+len(body_language_class)*20, coords[1]-30), 
                        (245, 117, 16), -1)
            cv2.putText(image, body_language_class, coords, 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Get status box
            cv2.rectangle(image, (0,0), (250, 60), (245, 117, 16), -1)
            
            # Display Class
            cv2.putText(image, 'CLASS'
                        , (95,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, body_language_class.split(' ')[0]
                        , (90,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Display Probability
            cv2.putText(image, 'PROB'
                        , (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(round(body_language_prob[np.argmax(body_language_prob)],2))
                        , (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            if(body_language_class == 'SIT'):
                elapsed+=1
                print("count: %02d",int(elapsed)) 
                time.sleep(1)
            if elapsed == 10:
                cv2.imwrite(filename='saved_img.jpg', img=frame)
                cv2.waitKey(1650)
                print("Image saved!")
                fall_detection()
                elapsed=0
            detect +=1
            time.sleep(0.1)
            print(detect)
            if detect >10 :  
                print(detect)              
                parsed_json["Detect"] = True
                detect_state(parsed_json)
                detect = 0
                
        except:
            print("Not detect")
            none_detect +=1
            time.sleep(0.1)
            if none_detect >10:
                parsed_json['Detect'] = False 
                detect_state(parsed_json)
                none_detect = 0                 
                    
            pass
        cv2.imshow('Raw Webcam Feed', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()