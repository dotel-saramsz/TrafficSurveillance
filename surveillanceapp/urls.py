from django.urls import path, include
from . import views

app_name = 'surveillanceapp'

urlpatterns=[
    path('',views.index,name='index'),
    path('stations/',views.list_stations,name='stationlist'),
    path('stations/<int:pk>',views.StationDetailView.as_view(),name='stationdetails'),
    path('test/',views.test,name='test'),
    path('stations/addnewstation/',views.addNewStation,name='stationcreate'),
    path('report/', views.report, name='report'),
]
