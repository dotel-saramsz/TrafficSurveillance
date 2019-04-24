from django.contrib import admin
from .models import *
from .forms import VideoAdminForm
# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    form = VideoAdminForm


admin.site.register(Station)
admin.site.register(SurveillanceReport)
admin.site.register(SurveillanceVideo, VideoAdmin)

