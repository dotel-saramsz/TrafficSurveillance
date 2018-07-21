from django.urls import path, include
from . import views

app_name = 'surveillanceapp'

urlpatterns=[
    path('',views.index,name='index'),
    path('stations/',views.StationListView.as_view(),name='stationlist'),
    path('stations/<int:pk>',views.StationDetailView.as_view(),name='stationdetails'),
    path('stations/addnewstation/',views.addNewStation,name='stationcreate'),
    path('test',views.test,name='test'),
    path('report', views.report, name='report'),
]
