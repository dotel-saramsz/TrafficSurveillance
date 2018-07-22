from channels import Group, channel
import json
import time
import cv2
import random
import multiprocessing
from multiprocessing.managers import BaseManager
from . import cvrender, videoplayer
import numpy as np
import os
from django.conf import settings


class MyChannel(channel.Channel):

    def __init__(self,name):
        super(MyChannel, self).__init__(name)
        print('My Channel created with name {}'.format(name))
        print(self.name)
        print(self.channel_layer)

    def send(self, content, immediately=True):
        print('Sending from my channel')
        super(MyChannel, self).send(content, immediately)

    def set(self,value):
        self.value = value

    def get(self):
        print(self.value)


def testfunc(returnchannel):
    # print('Channel layer: ', returnchannel.channel_layer)
    # print('Channel name: ', returnchannel.name)
    # customchannel = MyChannel(returnchannel.name)   # Use channel layer also in next try!
    returnchannel.send({
        'text': json.dumps({
            'eof': True,
            'message': 'The video stream has ended'
        })
    }, True)

    returnchannel.set('Hello world')


def ws_connect(message,videoid):
    print(message)
    Group('users').add(message.reply_channel)
    message.reply_channel.send({
        'accept': True
    })


def ws_receive(message,videoid):
    print('A message has arrived')
    print(message.reply_channel)
    received = json.loads(message.content.get('text'))
    if received['start']:
        videopath = os.path.join(settings.BASE_DIR,'testvideos/ratnapark.MOV')   # This is the place where we find the address of the video
        videoplayer.runvideo(videopath, message.reply_channel)
        print('This must be printed after the video has been closed and returned to consumer')


        # BaseManager.register('MyChannel', MyChannel, exposed=['send'])
        # manager = BaseManager()
        # manager.start()
        # # customchannel = manager.MyChannel(message.reply_channel.name)
        # customchannel = channel.Channel(message.reply_channel.name)
        # # videoplayer = multiprocessing.Process(name='videoplayer',target=testfunc,args=[customchannel])
        # # videoplayer.start()
        # # videoplayer.join()
        # customchannel.send({
        #     'text': json.dumps({
        #         'eof': True,
        #         'message': 'The video stream has ended'
        #     })
        # }, True)
        # cvrender.rundetection(videoid)
        # cap = cv2.VideoCapture('testvideos/ratnapark.MOV')
        # random_str = 'video{}'.format(int(random.random()*1000000))
        # framecount = 0
        # lasttime = time.time()
        # starttime = time.time()
        # print('Connection established. Now playing the video!')
        # if cap.isOpened():
        #     ret, frame = cap.read()
        # display = plt.imshow(frame)
        # while cap.isOpened():
        #     ret, frame = cap.read()
        #     if ret:
        #         display.set_data(frame)
        #         plt.pause(0.005)
        #         # cv2.imshow('Video', frame)
        #         print('Just below the cv2.imshow()')
        #         if time.time() - lasttime >= 1.0:
        #             lasttime = time.time()
        #             message.reply_channel.send({
        #                 'text': json.dumps({
        #                     'eof': False,
        #                     'message': 'Video Playing:{}. Current Frame Count: {} and image size {}'.format(videoid,
        #                                                                                   time.time() - starttime,frame.size)
        #                 })
        #             }, True)
        #         if time.time() - starttime >= 5.0:
        #             plt.close()
        #             cap.release()
        #             break
        #         framecount += 1
        #         # ch = cv2.waitKey(30) & 0xFF
        #         # if ch == 27:
        #         #     cv2.destroyAllWindows()
        #         #     cap.release()
        #         #     break
        #     else:
        #         print('Error in retrieving frame')
        # # end of video
        # plt.show()
        # message.reply_channel.send({
        #     'text': json.dumps({
        #         'eof': True,
        #         'message': 'The video stream has ended'
        #     })
        # })


def ws_disconnect(message,videoid):
    print('Socket has now been disconnected: ',message.reply_channel.name)
    Group('users').discard(message.reply_channel)

# def ws_connect(message,videoid):
#     lasttime = time.time()
#     Group('users').add(message.reply_channel)
#     seconds = 0
#     while seconds < 3:
#         if time.time()-lasttime >= 1.0:
#             seconds += 1
#             sendingdata = 'Data for {} on second {}'.format(videoid,seconds)
#             lasttime = time.time()
#             message.reply_channel.send({
#                 'text':json.dumps({
#                     'eof': False,
#                     'message': sendingdata
#                 })
#             }, True)
#     message.reply_channel.send({
#         'text': json.dumps({
#             'eof': True,
#             'message': None
#         })
#     }, True)
#
#
# def ws_disconnect(message,videoid):
#     print('Socket is disconnected')
#     Group('users').discard(message.reply_channel)
