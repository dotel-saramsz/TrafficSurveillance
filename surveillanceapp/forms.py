from django import forms
from .models import *
import os
from django.conf import settings
import cv2
import math
from . import cvrender

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['station_name', 'lat_pos', 'lon_pos', 'station_pic']


class VideoAdminForm(forms.ModelForm):
    def clean(self):
        formdata = self.cleaned_data
        entered_filename = formdata.get('video_filename')
        actual_filename = os.path.join(settings.VIDEO_DIR,entered_filename)
        try:
            with open(actual_filename, 'r') as videofile:
                pass
            return formdata
        except FileNotFoundError:
            raise forms.ValidationError('Entered File has not been saved in the video directory yet!')

    # def save(self, commit=True):
    #     video = super(VideoAdminForm, self).save(commit=False)
    #     actual_filename = os.path.join(settings.VIDEO_DIR, video.video_filename)
    #     unique_name = '{}_{}_{}'.format(str(video.station), str(video.timestamp.date()),str(video.timestamp.time()))
    #     fileext = os.path.splitext(video.video_filename)[1]
    #     print('The entered name was {} but the new name is {}'.format(video.video_filename,unique_name+fileext))
    #     self.instance.video_filename = unique_name+fileext
    #     self.instance.video_name = unique_name
    #     new_filename = os.path.join(settings.VIDEO_DIR, video.video_filename)
    #     os.rename(actual_filename,new_filename)
    #     # extracting a thumbnail and saving as an image
    #     cap = cv2.VideoCapture(new_filename)
    #     cap.set(cv2.CAP_PROP_POS_MSEC, 10000)   # capture a frame at position 10 seconds from the start
    #     self.instance.duration = math.ceil((cap.get(cv2.CAP_PROP_FRAME_COUNT)/cap.get(cv2.CAP_PROP_FPS))/60)  # Finds the duration in minutes
    #     ret, frame = cap.read()
    #     if ret:
    #         thumbnail_filename = os.path.join('video_thumbnails','{}.jpg'.format(unique_name))
    #         thumbnail_path = os.path.join(settings.BASE_DIR,'static',thumbnail_filename)
    #         frame = cvrender.overlap_play(frame)
    #         cv2.imwrite(thumbnail_path, frame)
    #         self.instance.thumbnail_filename = thumbnail_filename
    #         print('Done')
    #     cap.release()
    #
    #     print('Now saving at {}'.format(thumbnail_path))
    #     return self.instance

    class Meta:
        model = SurveillanceVideo
        fields = ['timestamp', 'station', 'video_filename', 'lane_dimens', 'duration']