from django.shortcuts import render, Http404
from .models import Station
from django.views.generic import ListView,DetailView

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




