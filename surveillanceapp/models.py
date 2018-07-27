from django.db import models
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


    video_id=models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()  # we will be manually adding videos of different days so don't add autonow
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    ##set custom filename
    def file_path(self,filename):

        extension=(os.path.splitext(filename))[1]
        filename=str(self.video_id)+'_'+str(self.timestamp.date())+'_'+str(self.station) ##get the file extension
        return os.path.join(BASE_DIR,'media/surveillance_videos/',filename)+extension


    video_file=models.FileField(upload_to=file_path,max_length=250)#$"surveillance_videos/")
    report=models.BooleanField(default=False)
    lane_dimens=models.CharField(max_length=50)


    def __str__(self):
        return str(self.video_id)

    ##clean data
    def clean(self,*args,**kwargs):
        data=super(SurveillanceVideo,self).clean(*args,**kwargs)
        return data

    def storeDimens(self):
        pass

    ## store as a list
    def parseDimens(self):
        pass

    ## parse list and retrive dimensions
    def setThumbnail(self):
        pass

        ## try to retrive first frame from surveillancevideo

    def getSurveillanceImage(self):
        pass

##Surveillance Report Class
####has one to one relation with Surveillance Video class
class SurveillanceReport(models.Model):
    report_id=models.AutoField(primary_key=True)
    video=models.OneToOneField(SurveillanceVideo, on_delete=models.CASCADE)
    avg_capacity_index=models.FloatField()
    avg_count_index=models.FloatField()
    congestion_data=models.FileField()
    count_data=models.FileField()
    contribution_data=models.FileField()

    def __str__(self):
        return self.report_id

    def getCountList(self):
        pass

    def getAvgCapacity(self):
        pass

    def getAvgCount(self):
        pass

