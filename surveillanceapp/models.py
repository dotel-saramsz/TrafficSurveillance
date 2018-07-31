from django.db import models
from django.conf import settings
import os
import re

# Check below by replacing with BASE_DIR from settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# class for station
class Station(models.Model):
    station_id = models.AutoField(primary_key=True)  ##surveillance station id
    station_name = models.CharField(max_length=50)   #station name
    lat_pos = models.FloatField() #latitude position
    lon_pos = models.FloatField() #longitude position
    station_pic = models.ImageField(upload_to='station_img/', default='default/defaultstation.png')  #Media will be uploaded to MEDIA_ROOT/station_img

    def __str__(self):
        return self.station_name


## surveillance video class, this class has many to one relation with Station class
class SurveillanceVideo(models.Model):
    video_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()  # we will be manually adding videos of different days so don't add autonow
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='surveillance_videos')
    thumbnail_filename = models.CharField(max_length=200,null=True)
    video_name = models.CharField(max_length=100, null=True)
    video_filename = models.CharField(max_length=200, null=True)
    report = models.BooleanField(default=False)
    lane_dimens = models.CharField(max_length=200, null=True)
    duration = models.BigIntegerField(null=True)
    analysed_duration = models.BigIntegerField(default=0)
    analysed_percentage = models.IntegerField(default=0)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        print('Model save was called')
        super(SurveillanceVideo, self).save()

    def __str__(self):
        return str(self.video_name)

    # parse lane_dimensn and retrieve list of points
    def parsedimens(self):
        pattern = r'\[(\d+,\d+)\]'
        points = re.finditer(pattern, self.lane_dimens)
        point_list = []
        for point in points:
            point = point.group()
            point = [int(each) for each in point.lstrip('[').rstrip(']').split(',')]
            point_list.append(point)
        return point_list


##Surveillance Report Class has one to one relation with Surveillance Video class
class SurveillanceReport(models.Model):
    report_id = models.AutoField(primary_key=True)
    video = models.OneToOneField(SurveillanceVideo, on_delete=models.CASCADE, related_name='surveillance_report')
    congestion_jsonfile = models.CharField(null=True, max_length=100)
    count_jsonfile = models.CharField(null=True, max_length=100)
    contribution_jsonfile = models.CharField(null=True, max_length=100)
    report_file = models.CharField(null=True, max_length=100)
    avg_congestion_index = models.FloatField(default=0)
    avg_count_index = models.FloatField(default=0)
    outgoing_vehicle_count = models.IntegerField(default=0)
    outgoing_tempo_count = models.IntegerField(default=0)
    outgoing_bike_count = models.IntegerField(default=0)
    outgoing_car_count = models.IntegerField(default=0)
    outgoing_taxi_count = models.IntegerField(default=0)
    outgoing_micro_count = models.IntegerField(default=0)
    outgoing_pickup_count = models.IntegerField(default=0)
    outgoing_bus_count = models.IntegerField(default=0)
    outgoing_truck_count = models.IntegerField(default=0)

    def __str__(self):
        identifier = 'Report {} for {}'.format(self.report_id,self.video.video_name)
        return identifier

    def getCountList(self):
        pass

    def getAvgCapacity(self):
        pass

    def getAvgCount(self):
        pass

