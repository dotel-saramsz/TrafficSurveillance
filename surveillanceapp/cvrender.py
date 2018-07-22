import cv2
from darkflow.net.build import TFNet
import multiprocessing
import time
from django.shortcuts import render, HttpResponse
import json

def playvideo(queue,dataevent,endevent):
    print('Process name:',multiprocessing.current_process().name)
    print('Process id:',multiprocessing.current_process().pid)
    cap = cv2.VideoCapture('testvideos/ratnapark.MOV')
    framecount = 0
    while cap.isOpened():
        ret,frame = cap.read()
        if ret:
            cv2.imshow('Video Window',frame)
            queue.put('Current Frame Count: {}'.format(framecount))
            dataevent.set()
            framecount += 1
            ch = cv2.waitKey(30) & 0xFF
            if ch == 27:
                cv2.destroyAllWindows()
                cap.release()
                break
        else:
            print('Error in retrieving frame')
    else:
        print('Video couldnt be loaded')
    endevent.set()
    return


def runvideo(queue,videoid):
    print('Process name:',multiprocessing.current_process().name)
    print('Process id:',multiprocessing.current_process().pid)
    if not queue.empty():
        message = queue.get()
    print(type(message))
    print('Message:',message.reply_channel)
    print('Video ID:',videoid)

    # cap = cv2.VideoCapture('testvideos/ratnapark.MOV')
    # framecount = 0
    # lasttime = time.time()
    # starttime = time.time()
    # print('Connection established. Now playing the video!')
    # while cap.isOpened():
    #     ret, frame = cap.read()
    #     if ret:
    #         cv2.imshow('Video Window', frame)
    #         if time.time() - lasttime >= 1.0:
    #             lasttime = time.time()
    #             message.reply_channel.send({
    #                 'text': json.dumps({
    #                     'eof': False,
    #                     'message': 'Video Playing:{}. Current Frame Count: {}'.format(videoid, time.time() - starttime)
    #                 })
    #             }, True)
    #         # if time.time() - starttime >= 4.0:
    #         #     cap.release()
    #         #     break
    #         framecount += 1
    #         ch = cv2.waitKey(30) & 0xFF
    #         if ch == 27:
    #             cv2.destroyAllWindows()
    #             cap.release()
    #             break
    #     else:
    #         print('Error in retrieving frame')
    # end of video
    message.reply_channel.send({
        'text': json.dumps({
            'eof': True,
            'message': 'The video stream has ended'
        })
    },True)


def rundetection(videoid):
    pass