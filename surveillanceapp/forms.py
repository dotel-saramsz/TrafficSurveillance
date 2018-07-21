from django import forms
from .models import *

class StationForm(forms.ModelForm):
    station_name=forms.CharField(max_length=15)
    lat_pos=forms.FloatField()
    lon_pos=forms.FloatField()


    class Meta:
        model=Station
        fields=('station_name','lat_pos','lon_pos','station_pic')


