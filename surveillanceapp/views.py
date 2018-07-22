from django.shortcuts import render, Http404, HttpResponse
from .models import Station
from django.views.generic import ListView,DetailView
from . import cvrender
import cv2
import multiprocessing
import threading

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

class StationListView(ListView):

    model = Station
    title="Station List"
    template_name = 'surveillanceapp/stationlist.html'
    context={
        'title':title
    }


class StationDetailView(DetailView):
    model = Station
    template_name = 'surveillanceapp/stationdetails.html'

    def station_detail_view(request,pk):
        try:
            station=Station.objects.get(pk=pk)
        except Station.DoesNotExist:
            raise Http404("Station does not exist")

        return render(request,'surveillanceapp/stationdetails.html',{'station':station})


def test(request):
    # print('New Process creating')
    # videoplayer = multiprocessing.Process(name='videoplayer',target=cvrender.playvideo)
    # videoplayer.start()
    # videoplayer.join()
    return render(request,'surveillanceapp/test.html')

def cv_playvideo(request):
    print('New Process creating')
    queue = multiprocessing.Queue()
    dataevent = multiprocessing.Event()
    endevent = multiprocessing.Event()
    videoplayer = multiprocessing.Process(name='videoplayer', target=cvrender.playvideo, args=(queue,dataevent,endevent))
    videoplayer.start()
    # while not endevent.is_set():
    #     print('----')
    #     dataevent.wait(1)
    #     result = queue.get()
    #     print(result)
    # print('Ended')
    videoplayer.join()
    return HttpResponse('The video finished playing')
