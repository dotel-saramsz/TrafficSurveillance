from django import forms
from .models import *

class StationForm(forms.ModelForm):

    class Meta:
        model=Station
        fields=('station_name','lat_pos','lon_pos','station_pic')


