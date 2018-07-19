from django.shortcuts import render, Http404
from .models import Station
from .forms import *
from django.shortcuts import redirect
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

def addNewStation(request):
    if request.method=='POST':
        form=StationForm(request.POST)
        if form.is_valid():
            m=form.save(commit=False)
            m.save()
            return redirect('surveillanceapp:stationdetails',pk=m.pk)


    else:
        form=StationForm()

    return render(request,'surveillanceapp/addnewstation.html',{'form':form})


###for new station form
#class StationCreate(CreateView):
 #   model=Station
  #  fields=['station_name','lat_pos','lon_pos','station_pic']
   # template_name='surveillanceapp/addnewstation.html'


class StationListView(ListView):

    model = Station
    title="Station List"
    template_name = 'surveillanceapp/stationlist.html'
    paginate_by=6
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
    return render(request,'surveillanceapp/test.html')