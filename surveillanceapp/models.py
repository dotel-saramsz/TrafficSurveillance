from django.db import models

# class for station
class Station(models.Model):
    station_id=models.AutoField(primary_key=True)  ##surveillance station id
    station_name=models.CharField(max_length=15)   #station name
    lat_pos=models.FloatField()   #latitude position
    lon_pos=models.FloatField () #longitude position
    station_pic=models.ImageField(upload_to='station_img/',default='default/defaultstation.png')  #Media will be uploaded to MEDIA_ROOT/station_img

    def __str__(self):
        return self.station_name



## surveillance video class
## this class has many to one relation with Station class
class SurveillanceVideo(models.Model):
    surveillance_id=models.AutoField(primary_key=True)
    surveillancevideo_name=models.CharField(max_length=25)  #surveillance video name
    timestamp=models.DateTimeField()
    report=models.BooleanField(default=False)
    lane_dimen1=models.FloatField()
    lane_dimen2=models.FloatField()
    lane_dimen3=models.FloatField()
    lane_dimen4=models.FloatField()
    station=models.ForeignKey(Station,on_delete=models.CASCADE)

    def __str__(self):
        return self.surveillancevideo_name

    def getSurveillanceImage(self):
        pass

##Surveillance Report Class
####has one to one relation with Surveillance Video class
class SurveillanceReport(models.Model):
    report_id=models.AutoField(primary_key=True)
    video=models.OneToOneField(SurveillanceVideo, on_delete=models.CASCADE)
    avg_capacity_index=models.FloatField()
    avg_count_index=models.FloatField()
    json_data=models.FileField()
    bike_count_list=models.CharField(max_length=5)
    car_count_list=models.CharField(max_length=5)
    taxi_count_list=models.CharField(max_length=5)
    pickup_count_list=models.CharField(max_length=5)
    micro_count_list=models.CharField(max_length=5)
    bus_count_list=models.CharField(max_length=5)
    truck_count_list=models.CharField(max_length=5)
    tempo_count_list=models.CharField(max_length=5)

    def __str__(self):
        return self.report_id

    def getCountList(self):
        pass

    def getAvgCapacity(self):
        pass

    def getAvgCount(self):
        pass

