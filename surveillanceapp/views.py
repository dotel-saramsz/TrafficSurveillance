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
        'title': title,
        'stations': stations_data,
        'stationCount': querySetLength,
        'videoCount': SurveillanceVideo.objects.count(),
        'reportCount': SurveillanceReport.objects.count()
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
        stations = Station.objects.all()
        station_list = []
        for station in stations:
            total_videos = 0
            analysed_videos = 0
            for video in station.surveillance_videos.all():
                if video.report:
                    analysed_videos += 1
                total_videos += 1
            if total_videos == 0:
                percent = 0
            else:
                percent = int(analysed_videos/total_videos*100)
            station_list.append({
                'station': station,
                'progress': {
                    'total': total_videos,
                    'analysed': analysed_videos,
                    'percent': percent
                }
            })
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
            access_time = timestamp.strftime('%Y-%m-%d_%H-%M-%S')
            pattern = r'[a-zA-Z]+_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.\w{3,}'

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
                duration = math.ceil((cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)))  # Finds the duration in seconds
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
        videolist = SurveillanceVideo.objects.filter(station_id=pk).order_by('-timestamp')
        return render(request, 'surveillanceapp/stationdetails.html',{'station': station, 'videolist': videolist})

    except Station.DoesNotExist:
        raise Http404


def surveillance_video(request,station_id,video_id):
    video = SurveillanceVideo.objects.get(video_id=video_id)
    print(video.video_name)
    print(video.report)
    return render(request, 'surveillanceapp/video.html', {'video': video})


def surveillance_report(request,station_id,video_id):

    report = SurveillanceReport.objects.get(video__video_id=video_id)

    with open(report.count_jsonfile, 'r') as countfile:
        countdata = json.load(countfile)

    with open(report.congestion_jsonfile, 'r') as congestionfile:
        congestiondata = json.load(congestionfile)

    with open(report.contribution_jsonfile, 'r') as contribfile:
        contribdata = json.load(contribfile)

    totalcount = []
    vclass_name = ['Tempo','Bike','Car','Taxi','Micro','Pickup','Bus','Truck']
    vclass_count = [[] for each in vclass_name]
    for data in countdata:
        for i in range(len(data)):
            vclass_count[i].append(data[i])
        totalcount.append(sum(data))

    # Congestion contribution from area approach
    avg_congestion = sum(congestiondata) / len(congestiondata)
    vclass_contrib = [[] for each in vclass_name]
    for i, data in enumerate(contribdata):
        actual_contrib = np.array(data) * congestiondata[i]
        for i in range(len(data)):
            vclass_contrib[i].append(actual_contrib[i])
    avg_contrib = [(sum(contrib) / len(contrib)) / avg_congestion for contrib in vclass_contrib]
    avg_contrib = np.round(avg_contrib, 3)

    #Congestion contribution from count in bike units method
    outgoing_counts = [report.outgoing_tempo_count,
                       report.outgoing_bike_count,
                       report.outgoing_car_count,
                       report.outgoing_taxi_count,
                       report.outgoing_micro_count,
                       report.outgoing_pickup_count,
                       report.outgoing_bus_count,
                       report.outgoing_truck_count]
    vehicle_weights = [2,1,2,2,3,3,5,5] #This is to convert each vclass count into the bike units
    outgoing_counts = np.array(outgoing_counts) * np.array(vehicle_weights)
    count_avgcontrib = np.round(outgoing_counts/np.sum(outgoing_counts), 3)

    net_contrib = np.round((2/3)*count_avgcontrib + (1/3)*avg_contrib, 3).tolist()  #[2/3 * countbased + 1/3 * areabased]

    # Rolling average of congestion sampled over a window of 5 seconds
    interval = int(math.ceil(0.1*len(countdata)))
    rolling_avg_congestion = np.convolve(np.array(congestiondata), np.ones((interval,)) / interval, mode='same').tolist()
    rolling_avg_congestion = [float(each) for each in rolling_avg_congestion]

    # Rolling average of total no. of vehicles sampled over a window of 5 seconds
    rolling_avg_count = np.convolve(np.array(totalcount), np.ones((interval,)) / interval, mode='same').tolist()
    rolling_avg_count = [float(each) for each in rolling_avg_count]

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
            'plotOptions': {
                'series': {
                    'pointStart': 1
                }
            },
            'title': {'text': 'No.of {} in the road vs time'.format(vclass_name[i])},
            'xAxis': {'title': {'text': 'Time'}},
            'yAxis': {'title': {'text': vclass_name[i]+' Count'}},
            'series': [vcount_series[i]],
            'credits': {'enabled': False}
        })
        count_dump.append(json.dumps(count_chart[i]))

    totalcount_chart = json.dumps({
        'chart': {'type': 'line'},
        'title': {'text': 'Plot of total no. of vehicles in road vs time'},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'No.of Vehicles'}},
        'series': [{'name': 'No.of vehicles', 'data': totalcount}],
        'credits': {'enabled': False}
    })

    totalcount_roll_chart = json.dumps({
        'chart': {'type': 'line'},
        'title': {'text': 'Rolling average plot of total vehicle count sampled over a window of {} seconds'.format(interval)},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'No.of Vehicles'}},
        'series': [{'name': 'No.of vehicles', 'data': rolling_avg_count,'color': '#7c212c'}],
        'credits': {'enabled': False}
    })

    congestion_chart = json.dumps({
        'chart': {'type': 'line'},
        'title': {'text': 'Plot of the approx. congestion in the road vs time'},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'Congestion'}},
        'series': [{'name':'Congestion Index','data': congestiondata}],
        'credits': {'enabled': False}
    })

    congestion_roll_chart = json.dumps({
        'chart': {'type': 'line'},
        'title': {'text': 'Rolling average plot of congestion sampled over a window of {} seconds'.format(interval)},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'Congestion'}},
        'series': [{'name': 'Congestion Index', 'data': rolling_avg_congestion,'color': '#7c212c'}],
        'credits': {'enabled': False}
    })

    vcontrib_series = [{} for each in vclass_name]
    for i in range(0, len(vclass_name)):
        vcontrib_series[i] = {
            'name': vclass_name[i],
            'y': net_contrib[i],
        }

    contribution_chart = json.dumps({
        'chart': {'type': 'pie'},
        'title': {'text': 'Contribution of different vehicle classes to the overall congestion'},
        'xAxis': {'title': {'text': 'Time'}},
        'yAxis': {'title': {'text': 'Congestion'}},
        'series': [{'name':'Average Contribution','data': vcontrib_series}],
        'credits': {'enabled': False}
    })

    count_chart = []
    for i, each in enumerate(vclass_name):
        count_chart.append({
            'chart': count_dump[i],
            'class_name': each
        })

    cvrender.save_pdf(report,vclass_name,vclass_count,totalcount,rolling_avg_count,congestiondata,rolling_avg_congestion,net_contrib,interval)


    return render(request, 'surveillanceapp/report.html', {'report': report,
                                                           'vclass_names':vclass_name,
                                                           'count_chart': count_chart,
                                                           'totalcount_chart': totalcount_chart,
                                                           'totalcount_roll_chart':totalcount_roll_chart,
                                                           'congest_chart': congestion_chart,
                                                           'congest_roll_chart': congestion_roll_chart,
                                                           'contrib_chart': contribution_chart})


def analytics(request):
    stationlist = Station.objects.all()
    videolist = []
    for video in SurveillanceVideo.objects.all().order_by('-last_analysed'):
        if video.last_analysed is not None:
            videolist.append(video)
    return render(request,'surveillanceapp/analytics.html', {'stationlist':stationlist, 'videolist': videolist})


def filter_analytics(request):
    received = request.GET.get('id')
    videolist = []
    if received == 'all':
        for video in SurveillanceVideo.objects.all().order_by('-last_analysed'):
            if video.last_analysed is not None:
                videolist.append(video)
    else:
        station_id = int(received)
        for video in SurveillanceVideo.objects.filter(station_id=station_id).order_by('-last_analysed'):
            if video.last_analysed is not None:
                videolist.append((video))
    return render(request,'surveillanceapp/analyticstable.html',{'videolist': videolist})
