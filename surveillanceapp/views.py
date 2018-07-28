from django.shortcuts import render, redirect, Http404, HttpResponse
from .models import Station,SurveillanceVideo,SurveillanceReport
from django.views.generic import ListView,DetailView
from .forms import *
from . import cvrender
import cv2
import json
import numpy as np
import datetime
import os
import re
from django.conf import settings


def index(request):
    title = "Dashboard"
    stations_data = Station.objects.all()
    querySetLength = Station.objects.count()
    context={
        'title':title,
        'stations':stations_data,
        'stationCount':querySetLength
    }
    return render(request,'surveillanceapp/index.html',context)


def addNewStation(request):
    if request.method == 'POST':
        received = request.POST.copy()
        print(received)
        form = StationForm(request.POST, request.FILES)
        if form.is_valid():
            station = form.save(commit=False)
            os.mkdir(os.path.join(settings.VIDEO_DIR, station.station_name))     #Create a new folder to store the videos of that station
            station.save()
            return redirect('surveillanceapp:stationdetails', pk=station.station_id)
    else:
        form = StationForm()

    return render(request, 'surveillanceapp/addnewstation.html', {'form': form})


def list_stations(request):
    try:
        station_list = Station.objects.all()
    except Station.DoesNotExist:
        raise Http404
    return render(request, 'surveillanceapp/stationlist.html', {'title': 'Station List', 'station_list': station_list})


def station_detail(request,pk):
    try:
        station = Station.objects.get(pk=pk)
        folder_name = station.station_name
        search_dir = os.path.join(settings.VIDEO_DIR, folder_name)

        for file in os.scandir(search_dir):
            stats = os.stat(file.path)
            timestamp = datetime.datetime.fromtimestamp(stats.st_ctime)
            access_time = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
            pattern = r'[a-zA-Z]+_\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.\w{3,}'

            if not re.match(pattern, file.name):
                # This means a new video is added to that folder
                print(file.name, 'in ',folder_name,' does not match the pattern')
                unique_name = '{}_{}'.format(folder_name, access_time)
                fileext = os.path.splitext(file.name)[1]

                video_name = unique_name    # The unique name to be used for JSON files as well

                video_filename = os.path.join(search_dir, unique_name + fileext)    # The full path to the video file

                os.rename(file.path, video_filename)    # To rename the video file according to our standards

                # extracting a thumbnail and saving as an image
                cap = cv2.VideoCapture(video_filename)
                cap.set(cv2.CAP_PROP_POS_MSEC, 10000)  # capture a frame at position 10 seconds from the start
                duration = math.ceil((cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(
                    cv2.CAP_PROP_FPS)) / 60)  # Finds the duration in minutes
                ret, frame = cap.read()
                if ret:
                    thumbnail_filename = os.path.join('video_thumbnails', '{}.jpg'.format(unique_name))
                    thumbnail_path = os.path.join(settings.BASE_DIR, 'static', thumbnail_filename)
                    frame = cvrender.overlap_play(frame)
                    cv2.imwrite(thumbnail_path, frame)
                    print('Thumbnail created and saved')
                cap.release()

                # Now create a new Surveillance Video model to save the new video
                newvideo = SurveillanceVideo.objects.create(station=station,
                                                            video_name=video_name,
                                                            video_filename=video_filename,
                                                            timestamp=timestamp,
                                                            duration=duration,
                                                            thumbnail_filename=thumbnail_filename)

                print('New Video found and added: {}, {}, {}, {}'.format(newvideo.video_filename,newvideo.timestamp,newvideo.thumbnail_filename,newvideo.duration))
        videolist = SurveillanceVideo.objects.filter(station_id=pk)
        return render(request, 'surveillanceapp/stationdetails.html',{'station': station, 'videolist': videolist})

    except Station.DoesNotExist:
        raise Http404


def surveillance_video(request,station_id,video_id):
    video = SurveillanceVideo.objects.get(video_id=video_id)
    return render(request, 'surveillanceapp/video.html', {'video': video})


def report(request):
    countdata = [[1, 2, 0, 0, 0, 0, 0, 0], [1, 2, 0, 0, 0, 0, 0, 0], [1, 2, 0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0, 0, 0], [0, 3, 0, 0, 0, 0, 0, 0], [0, 3, 1, 0, 0, 0, 0, 0], [0, 2, 1, 0, 0, 0, 0, 0], [0, 2, 1, 1, 0, 0, 0, 0], [0, 2, 2, 1, 0, 0, 0, 0], [0, 2, 2, 1, 0, 0, 1, 0], [0, 2, 2, 1, 0, 0, 1, 0], [0, 1, 2, 1, 0, 0, 2, 0], [0, 1, 1, 1, 0, 0, 2, 0], [0, 1, 1, 0, 0, 0, 2, 0], [0, 3, 1, 0, 0, 0, 2, 0], [0, 4, 1, 0, 0, 0, 1, 0], [0, 5, 1, 0, 0, 0, 1, 0], [0, 8, 1, 0, 0, 0, 0, 0], [0, 10, 0, 0, 0, 0, 0, 0], [0, 9, 0, 0, 0, 0, 0, 0], [0, 7, 0, 0, 0, 0, 0, 0], [0, 6, 1, 0, 0, 0, 0, 0], [0, 4, 1, 0, 0, 0, 0, 0], [0, 5, 2, 0, 0, 0, 0, 0], [0, 5, 2, 0, 0, 0, 0, 0], [0, 5, 2, 0, 0, 0, 0, 0], [0, 7, 2, 1, 0, 0, 0, 0], [0, 8, 2, 1, 0, 0, 0, 0], [0, 7, 2, 1, 0, 0, 0, 0], [0, 9, 1, 1, 0, 0, 0, 0], [0, 6, 1, 1, 1, 0, 0, 0], [0, 6, 1, 1, 1, 0, 0, 0], [0, 7, 1, 0, 1, 0, 0, 0], [0, 11, 1, 0, 1, 0, 0, 0], [0, 10, 1, 0, 1, 0, 0, 0], [0, 10, 1, 0, 1, 0, 0, 0], [0, 10, 0, 0, 0, 0, 0, 0], [0, 7, 1, 0, 0, 0, 0, 0], [0, 4, 2, 1, 0, 0, 1, 0], [0, 2, 2, 2, 0, 0, 1, 0], [0, 1, 2, 2, 0, 0, 1, 0], [0, 1, 5, 2, 0, 0, 1, 0], [0, 1, 6, 2, 0, 0, 1, 0], [0, 1, 5, 2, 0, 0, 1, 0], [0, 0, 5, 3, 0, 0, 0, 0], [0, 1, 5, 2, 0, 0, 0, 0], [0, 2, 4, 3, 0, 0, 0, 0], [0, 3, 4, 3, 0, 0, 0, 0], [0, 2, 4, 3, 0, 0, 0, 0], [0, 2, 3, 3, 0, 0, 0, 0], [0, 3, 3, 2, 0, 0, 1, 0], [0, 3, 2, 2, 1, 0, 1, 0], [0, 2, 3, 2, 1, 0, 1, 0], [0, 3, 2, 1, 1, 0, 1, 0], [0, 3, 3, 0, 1, 0, 2, 0], [0, 2, 2, 0, 1, 0, 2, 0], [0, 3, 2, 0, 1, 0, 2, 0], [0, 1, 4, 1, 1, 0, 2, 0], [0, 2, 4, 1, 1, 0, 1, 1], [0, 2, 4, 1, 1, 0, 1, 0], [0, 2, 4, 1, 1, 0, 1, 0], [0, 3, 3, 1, 1, 0, 0, 0], [0, 2, 4, 1, 1, 0, 0, 0]]
    contribdata = [[0.097, 0.903, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.394, 0.606, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.565, 0.435, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.875, 0.125, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.249, 0.616, 0.0, 0.006, 0.0, 0.03, 0.0, 0.099], [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.986, 0.014, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.899, 0.101, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.7, 0.264, 0.036, 0.0, 0.0, 0.0, 0.0], [0.0, 0.593, 0.264, 0.144, 0.0, 0.0, 0.0, 0.0], [0.0, 0.224, 0.464, 0.246, 0.0, 0.002, 0.064, 0.0], [0.0, 0.235, 0.443, 0.189, 0.0, 0.0, 0.133, 0.0], [0.0, 0.106, 0.51, 0.206, 0.0, 0.0, 0.178, 0.0], [0.0, 0.028, 0.287, 0.354, 0.0, 0.0, 0.326, 0.005], [0.0, 0.04, 0.267, 0.154, 0.0, 0.0, 0.532, 0.006], [0.0, 0.057, 0.222, 0.009, 0.0, 0.0, 0.712, 0.0], [0.0, 0.091, 0.029, 0.001, 0.0, 0.0, 0.878, 0.0], [0.0, 0.089, 0.06, 0.0, 0.0, 0.0, 0.851, 0.0], [0.0, 0.238, 0.205, 0.0, 0.0, 0.0, 0.557, 0.0], [0.0, 0.509, 0.491, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.996, 0.004, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.926, 0.074, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.844, 0.156, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.524, 0.476, 0.001, 0.0, 0.0, 0.0, 0.0], [0.0, 0.503, 0.497, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.5, 0.49, 0.01, 0.0, 0.0, 0.0, 0.0], [0.0, 0.457, 0.486, 0.057, 0.0, 0.0, 0.0, 0.0], [0.0, 0.437, 0.502, 0.06, 0.0, 0.0, 0.0, 0.0], [0.0, 0.48, 0.429, 0.092, 0.0, 0.0, 0.0, 0.0], [0.0, 0.644, 0.206, 0.144, 0.007, 0.0, 0.0, 0.0], [0.0, 0.52, 0.083, 0.332, 0.065, 0.0, 0.0, 0.0], [0.0, 0.336, 0.095, 0.423, 0.146, 0.0, 0.0, 0.0], [0.0, 0.469, 0.148, 0.111, 0.272, 0.0, 0.0, 0.0], [0.0, 0.516, 0.16, 0.017, 0.307, 0.0, 0.0, 0.0], [0.0, 0.285, 0.242, 0.033, 0.439, 0.0, 0.0, 0.0], [0.0, 0.637, 0.16, 0.0, 0.202, 0.0, 0.0, 0.0], [0.0, 0.984, 0.016, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.871, 0.08, 0.0, 0.0, 0.0, 0.048, 0.001], [0.0, 0.502, 0.188, 0.052, 0.0, 0.0, 0.257, 0.0], [0.0, 0.124, 0.271, 0.118, 0.0, 0.0, 0.486, 0.0], [0.0, 0.038, 0.24, 0.131, 0.0, 0.0, 0.59, 0.0], [0.0, 0.038, 0.234, 0.097, 0.0, 0.0, 0.631, 0.0], [0.0, 0.059, 0.327, 0.157, 0.0, 0.0, 0.457, 0.0], [0.0, 0.028, 0.369, 0.383, 0.0, 0.0, 0.22, 0.0], [0.0, 0.004, 0.656, 0.341, 0.0, 0.0, 0.0, 0.0], [0.0, 0.016, 0.822, 0.161, 0.0, 0.0, 0.0, 0.0], [0.0, 0.016, 0.699, 0.286, 0.0, 0.0, 0.0, 0.0], [0.0, 0.076, 0.702, 0.222, 0.0, 0.0, 0.0, 0.0], [0.0, 0.057, 0.6, 0.342, 0.0, 0.0, 0.0, 0.0], [0.0, 0.076, 0.444, 0.478, 0.0, 0.0, 0.002, 0.0], [0.0, 0.125, 0.474, 0.33, 0.005, 0.0, 0.067, 0.0], [0.0, 0.177, 0.26, 0.389, 0.024, 0.0, 0.15, 0.0], [0.0, 0.082, 0.415, 0.279, 0.038, 0.0, 0.187, 0.0], [0.0, 0.157, 0.291, 0.235, 0.063, 0.0, 0.253, 0.0], [0.0, 0.109, 0.393, 0.028, 0.086, 0.0, 0.383, 0.0], [0.0, 0.094, 0.16, 0.0, 0.108, 0.0, 0.638, 0.0], [0.0, 0.097, 0.07, 0.002, 0.116, 0.0, 0.715, 0.0], [0.0, 0.049, 0.145, 0.018, 0.207, 0.0, 0.568, 0.013], [0.0, -0.009, 0.208, -0.009, 0.272, 0.0, 0.355, 0.184], [0.0, 0.029, 0.305, 0.023, 0.052, 0.0, 0.59, 0.0], [0.0, 0.088, 0.351, 0.051, 0.041, 0.03, 0.44, 0.0], [0.0, 0.256, 0.483, 0.114, 0.094, 0.054, 0.0, 0.0], [0.0, 0.181, 0.576, 0.138, 0.105, 0.0, 0.0, 0.0]]
    congestiondata = [0.055, 0.074, 0.083, 0.091, 0.038, 0.022, 0.042, 0.076, 0.059, 0.087, 0.081, 0.149, 0.211, 0.216, 0.22, 0.292, 0.371, 0.285, 0.208, 0.122, 0.112, 0.12, 0.114, 0.081, 0.06, 0.051, 0.07, 0.108, 0.166, 0.227, 0.214, 0.218, 0.132, 0.164, 0.172, 0.218, 0.264, 0.196, 0.169, 0.143, 0.138, 0.127, 0.202, 0.343, 0.427, 0.325, 0.186, 0.133, 0.217, 0.226, 0.202, 0.207, 0.203, 0.212, 0.231, 0.215, 0.219, 0.248, 0.356, 0.349, 0.272, 0.334, 0.292, 0.17, 0.198]
    vclass_name = ['Tempo','Bike','Car','Taxi','Micro','Pickup','Bus','Truck']
    vclass_count = [[] for each in vclass_name]
    for data in countdata:
        for i in range(len(data)):
            vclass_count[i].append(data[i])

    avg_congestion = sum(congestiondata) / len(congestiondata)
    vclass_contrib = [[] for each in vclass_name]
    for i, data in enumerate(contribdata):
        actual_contrib = np.array(data) * congestiondata[i]
        for i in range(len(data)):
            vclass_contrib[i].append(actual_contrib[i])
    avg_contrib = [(sum(contrib) / len(contrib)) / avg_congestion for contrib in vclass_contrib]
    avg_contrib = np.round(avg_contrib, 3).tolist()

    count_chart = []
    count_dump = []
    vcount_series = [{} for each in vclass_name]
    for i in range(0, len(vclass_name)):
        vcount_series[i] = {
            'name': vclass_name[i],
            'data': vclass_count[i],
        }
        count_chart.append({
            'chart': {'type': 'line'},
            'title': {'text': vclass_name[i]},
            'xAxis': {'title': {'text': 'Time'},'categories': vclass_name[i]},
            'yAxis': {'title': {'text': vclass_name[i]+' Count'}},
            'series': [vcount_series[i]],
            'credits': 'false'
        })
        count_dump.append(json.dumps(count_chart[i]))

    congestion_chart = {
        'chart': {'type': 'column'},
        'title': {'text': 'Congestion Chart'},
        'xAxis': {'title': {'text': 'Time'},'categories':'Vehicles'},
        'yAxis': {'title': {'text': 'Congestion'}},
        'series': [{'name':'Congestion Index','data':congestiondata}],
        'credits': 'false'
    }

    vcontrib_series = [{} for each in vclass_name]
    for i in range(0, len(vclass_name)):
        vcontrib_series[i] = {
            'name': vclass_name[i],
            'y': avg_contrib[i],
        }

    contribution_chart = {
        'chart': {'type': 'pie'},
        'title': {'text': 'Contribution Plot'},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'Congestion'}},
        'series': [{'name':'Average Contribution','data': vcontrib_series}],
        'credits': 'false'
    }

    return render(request, 'surveillanceapp/report.html', {'vclass_names':vclass_name,'vcounts': count_dump,'vcon': congestion_chart,'vcontrib': contribution_chart})
