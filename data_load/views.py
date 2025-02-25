# from ffwc_django_project.settings import BASE_DIR

from rest_framework import permissions,viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from django.db import models
from django.contrib.auth.models import User



from django.db.models import OuterRef, Subquery

from django.db.models import F

# Annotate with row number for each unique_id
from django.db.models import Window
from django.db.models.functions import RowNumber


from django_filters.rest_framework import DjangoFilterBackend

from data_load.models import FfwcLastUpdateDate,FfwcStations2023,WaterLevelForecasts,WaterLevelObservations,WaterLevelForecastsExperimentals
from data_load.models import FfwcRainfallStations,RainfallObservations,MonthlyRainfall
from data_load.models import Feedback,AuthUser
from data_load.models import IndianStations

from data_load.models import ForecastWithStationDetails

from data_load import models as data_load_models
import data_load.serializers as serializers

from data_load.serializers import lastUpdateDateSerializer,stationSerializer,observedWaterlevelSerializer,forecastWaterlevelSerializer
from data_load.serializers import rainfallStationSerializer,rainfallObservationSerializer,monthlyRainfallSerializer
from data_load.serializers import threeDaysObservedRainfallSerializer,experimentalForecastWaterlevelSerializer

from data_load.serializers import feedbackSerializer,userSerializer
from data_load.serializers import indianStationSerializer


from collections import defaultdict

from datetime import date, datetime, timedelta
import calendar
import json
from itertools import chain


import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, AllValuesFilter, DateTimeFilter, NumberFilter 

from django.http import JsonResponse
from django.http import HttpResponse
from itertools import groupby
from django.core.serializers.json import DjangoJSONEncoder
# from rest_framework import filters

from django.db.models import Sum,Avg,Max,Min


import urllib.parse
from urllib.parse import quote
from urllib.request import urlopen 

from django.http.response import StreamingHttpResponse
import time
from queue import Queue, Empty
from threading import Thread, current_thread

import sys
import math

import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray
import shapely
import netCDF4
import numpy as np

import os
import json
import ast 

from io import StringIO
import requests

import pickle


import warnings
warnings.filterwarnings("ignore")

# fixedDate='2023-10-27 09:00:00'
fixedDate='2023-11-02T09:00:00Z'
# Function to Return Query Forecast Date

from data_load.tasks import go_to_sleep



def home(request):
    return StreamingHttpResponse(example())


def returnDate():

    entry_date_time = FfwcLastUpdateDate.objects.all().values_list('entry_date',flat=True)[0]
    entry_date = str(entry_date_time.date())
    entry_hour = str(entry_date_time.hour)

    hourIndexDict={
        '00':['06','07','08'],
        '06':['06','07','08'],  
        '09':['09','10','11'], 
        '12':['12','13','14'], 
        '15':['15','16','17'],
        '18':['18','19','20','21','22','23']
    }

    for key in list(hourIndexDict.keys()):
        if entry_hour in hourIndexDict[key]:
           entry_hour='T'+key

    entryDateTimeString=entry_date+entry_hour+':00:00Z'


    # Experimental Entry Datetime

    experimental_last_update_date = data_load_models.FfwcLastUpdateDateExperimental.objects.all().values_list('last_update_date',flat=True)[0]
    experimentalLastUpdateDatestring = str(experimental_last_update_date)

    experimental_entry_date_time = data_load_models.FfwcLastUpdateDateExperimental.objects.all().values_list('entry_date',flat=True)[0]
    experimental_entry_date_time=experimental_entry_date_time.replace(hour=6)
    # print('Experimental Entry Date: ', experimental_entry_date_time)

    experimental_entry_date = experimental_entry_date_time.date().strftime('%Y-%m-%d')
    experimental_entry_hour = experimental_entry_date_time.strftime("%H")



    for key in list(hourIndexDict.keys()):
        if experimental_entry_hour in hourIndexDict[key]:
            experimental_entry_hour='T'+str(key)

    experimentalEntryDateTimeString=experimental_entry_date+experimental_entry_hour+':00:00Z'


    # print('Experimental Entry Date time String: ', experimentalEntryDateTimeString)


    # presentDate=datetime.today()
    presentDate=datetime.today()-timedelta(days=0)
    dateInput=datetime.strftime(presentDate,'%Y-%m-%d')
    hourInput='T06'
    observedDate=dateInput+hourInput+':00:00Z'

    # print('Last Observed Date: '+observedDate)


    getLastUpdateTime=WaterLevelForecasts.objects.filter(st_id=31).order_by('-fc_date').values_list('fc_date',flat=True)[0]
    lastForecastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

    # print('Last Update Time in Forecast Table: ', lastForecastUpdateDateTime)


    # previousDate=datetime.today()-timedelta(days=1)
    previousDate=datetime.today()
    dateInput=datetime.strftime(previousDate,'%Y-%m-%d')
    hourInput='T09'
    forecastDate=dateInput+hourInput+':00:00Z'

    entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # print('Entry Datetime in Last update Database Table: ',entryDateTimeString )

    experimentalEntryDateTime = datetime.strptime(experimentalEntryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # print('Experimental Entry Datetime in Last update Database Table: ',experimentalEntryDateTime )

    return dateInput,hourInput,observedDate,forecastDate,lastForecastUpdateDateTime,entryDateTimeString,experimentalEntryDateTimeString,experimentalLastUpdateDatestring

#Calling Function to return Date Today
dateInput,hourInput,observedDate,forecastDate,lastForecastUpdateDateTime,entryDateTimeString,experimentalEntryDateTimeString,experimentalLastUpdateDatestring=returnDate()



class updateDateViewSet(viewsets.ModelViewSet):

    queryset = FfwcLastUpdateDate.objects.all()
    serializer_class = lastUpdateDateSerializer

    def list(self, request, *args, **kwargs):
        mydata = FfwcLastUpdateDate.objects.values_list('last_update_date')
        return Response(mydata[0])
        

class experimentalUpdateDateViewSet(viewsets.ModelViewSet):

    queryset = data_load_models.FfwcLastUpdateDateExperimental.objects.all()
    serializer_class = lastUpdateDateSerializer

    def list(self, request, *args, **kwargs):
        mydata = data_load_models.FfwcLastUpdateDateExperimental.objects.values_list('last_update_date')
        return Response(mydata[0])

# Rainfall Stations Viewset
class rainfallStationsViewSet(viewsets.ModelViewSet):

    queryset = data_load_models.FfwcRainfallStations.objects.all()
    serializer_class = serializers.rainfallStationSerializer


class station2023ViewSet(viewsets.ModelViewSet):

    queryset = FfwcStations2023.objects.all()
    serializer_class = stationSerializer

class stationViewSet(viewsets.ModelViewSet):

    # print('Base Directory:  ', BASE_DIR)

    queryset = FfwcStations2023.objects.filter(status=1)
    # queryset = FfwcStations2023.objects.all()
    serializer_class = stationSerializer

    def shortRangestation(self,request,**kwargs):
        # basin_order=self.kwargs['basin_order']
        queryset=FfwcStations2023.objects.filter(forecast_observation__gt=0,status=1)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)

    def mediumRangestation(self,request,**kwargs):
        # basin_order=self.kwargs['basin_order']
        queryset=FfwcStations2023.objects.filter(medium_range_station=1,status=1)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)

    def stationById(self,request,**kwargs):
        station_id=self.kwargs['station_id']
        queryset=FfwcStations2023.objects.filter(id=station_id)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def stationByName(self,request,**kwargs):
        station_name=self.kwargs['station_name']
        queryset=FfwcStations2023.objects.filter(name=station_name)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)

    def stationByBasin(self,request,**kwargs):
        basin_order=self.kwargs['basin_order']
        queryset=FfwcStations2023.objects.filter(basin_order=basin_order)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)


    def stationByDivision(self,request,**kwargs):
        division=self.kwargs['division']
        queryset=FfwcStations2023.objects.filter(division=division,status=1)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)

    def shortRangestationByBasin(self,request,**kwargs):
        basin_order=self.kwargs['basin_order']
        queryset=FfwcStations2023.objects.filter(forecast_observation__gt=0,status=1,basin_order=basin_order)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def mediumRangestationByBasin(self,request,**kwargs):
        basin_order=self.kwargs['basin_order']
        queryset=FfwcStations2023.objects.filter(medium_range_station=1,status=1,basin_order=basin_order)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)


    def shortRangestationByDivision(self,request,**kwargs):
        division=self.kwargs['division']
        queryset=FfwcStations2023.objects.filter(forecast_observation__gt=0,status=1,division=division)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)
    

    def mediumRangestationByDivision(self,request,**kwargs):
        division=self.kwargs['division']
        queryset=FfwcStations2023.objects.filter(medium_range_station=1,status=1,division=division)
        serializer = stationSerializer(queryset, many=True)
        return Response(serializer.data)



short_range_station=stationViewSet.as_view({'get':'shortRangestation'})
medium_range_station=stationViewSet.as_view({'get':'mediumRangestation'})

station_by_id=stationViewSet.as_view({'get':'stationById'})
station_by_name=stationViewSet.as_view({'get':'stationByName'})

station_by_basin=stationViewSet.as_view({'get':'stationByBasin'})
station_by_division=stationViewSet.as_view({'get':'stationByDivision'})

short_range_station_by_basin=stationViewSet.as_view({'get':'shortRangestationByBasin'})
medium_range_station_by_basin=stationViewSet.as_view({'get':'mediumRangestationByBasin'})

short_range_station_by_division=stationViewSet.as_view({'get':'shortRangestationByDivision'})
medium_range_station_by_division=stationViewSet.as_view({'get':'mediumRangestationByDivision'})


# Data for Morning Bulletin
class morningWaterlevelViewSet(viewsets.ModelViewSet):

    
    def list(self, request, *args, **kwargs):

        latest_record = WaterLevelObservations.objects.latest('wl_date')
        print('Latest record Date: ', latest_record.wl_date)

        print('Entry Date Time String in Morning Observed: ',entryDateTimeString )
        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateTime = entryDateTime.replace(hour=9)
        print('Entry Datetime (in Morning Observed) : ', entryDateTime)


        d1 = latest_record.wl_date-timedelta(days=1,hours=0,minutes=0,seconds=0)
        d2 = latest_record.wl_date+timedelta(days=0,hours=0,minutes=0,seconds=0)

        print(d1,d2)

        q1 = WaterLevelObservations.objects.filter(
            wl_date=d1
            ).order_by('st_id','wl_date')

        q2 = WaterLevelObservations.objects.filter(
            wl_date=d2,
            ).order_by('st_id','wl_date')


        q3=q1.union(q2)

        waterlevel=[]
        stationIDs=[]
        dates=[]

        for results in q3:
            stationIDs.append(results.st_id)
            dates.append(results.wl_date.strftime("%m-%d-%Y %H"))
            # dates.append(results.fc_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(dict)

        print('Morning Observed Data Length: ', len(stationIDs))
        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i][j]=k

        return JsonResponse(waterlevelDict,safe=False)


# Data for Afternoon Bulletin
class afternoonWaterlevelViewSet(viewsets.ModelViewSet):

    
    def list(self, request, *args, **kwargs):

        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateTime = entryDateTime.replace(hour=9)
        print('Entry Datetime (in Afternoon Observed) : ', entryDateTime)

   
        latest_record = WaterLevelObservations.objects.latest('wl_date')
        entryDateTime = latest_record.wl_date
        print('Last Record in Afternoon Observed: ',entryDateTime )

        d1 = entryDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        d2 = entryDateTime+timedelta(days=0,hours=6,minutes=0,seconds=0)

        

        q1 = WaterLevelObservations.objects.filter(
            wl_date=d1
            ).order_by('st_id','wl_date')

        q2 = WaterLevelObservations.objects.filter(
            wl_date=d2,
            ).order_by('st_id','wl_date')

        if(len(q2)==0 or len(q1)==0):
            
            d1 = entryDateTime-timedelta(days=1,hours=0,minutes=0,seconds=0)
            d2 = d1+timedelta(days=0,hours=6,minutes=0,seconds=0)

            q1 = WaterLevelObservations.objects.filter(
            wl_date=d1
            ).order_by('st_id','wl_date')

            q2 = WaterLevelObservations.objects.filter(
                wl_date=d2,
                ).order_by('st_id','wl_date')
            # print('No Data ')
        

        # print('Length of Q2: ', len(q1))

        q3=q1.union(q2)

        waterlevel=[]
        stationIDs=[]
        dates=[]

        for results in q3:
            stationIDs.append(results.st_id)
            dates.append(results.wl_date.strftime("%m-%d-%Y %H"))
            # dates.append(results.fc_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(dict)

        print('After Observed Data Length: ', len(stationIDs))
        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i][j]=k

        return JsonResponse(waterlevelDict,safe=False)


# from rest_framework.generics import ListAPIView
# Recent Observed
class recentObservedWaterlevelViewSet(viewsets.ModelViewSet):

    from django.db.models import OuterRef, Subquery
    # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # entryDateString = entryDateTime.strftime("%Y-%m-%d")
    # print('In recent Observed Entry Date String: ',entryDateString )
    # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    
    def list(self, request, *args, **kwargs):

        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateString = entryDateTime.strftime("%Y-%m-%d")
        print('Entry Date String (in recent Observed):  ',entryDateString )
        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        print('Entry Datetime (in Recent Observed) : ', entryDateTime)

        latest_record = WaterLevelObservations.objects.latest('wl_date')
        # latest_record = WaterLevelObservations.objects.exclude(waterlevel=-9999.00).order_by('wl_date').first()
        ten_days_ago = latest_record.wl_date - timedelta(days=10)

        print('Date of Ten days earlier: ', ten_days_ago)


        # Get the Latest Timestamp for Each Station
        q1 = WaterLevelObservations.objects.values('st_id').annotate(max_timestamp=Max('wl_date')).order_by('st_id')
        # q1 = WaterLevelObservations.objects.values('st_id').annotate(max_timestamp=Max('wl_date')).order_by('st_id')
        # q2 = WaterLevelObservations.objects.filter(wl_date__in=[record['max_timestamp'] for record in q1]).order_by('st_id')

        # Get the last ten days of data for each station
        q2 = WaterLevelObservations.objects.filter(
            wl_date__gte=ten_days_ago,
            st_id__in=[record['st_id'] for record in q1]
        ).order_by('st_id', 'wl_date')

        # q2 = WaterLevelObservations.objects.values('waterlevel').annotate(max_timestamp=Max('wl_date')).order_by('-wl_date')
        # q2 = WaterLevelObservations.objects.order_by('st_id', '-wl_date').distinct('st_id')
        
        # # Create a subquery to get the last ten days of data for each station
        # subquery = WaterLevelObservations.objects.filter(
        #     st_id=OuterRef('st_id'),
        #     wl_date__gte=ten_days_ago
        # ).exclude(waterlevel=-9999.00).order_by('-wl_date')


        # # Annotate each station with the latest data from the subquery
        # q3 = WaterLevelObservations.objects.values('st_id').annotate(
        #     latest_data=Subquery(subquery.values('waterlevel')[:1])
        # ).order_by('st_id')


        st_ids=[]
        wl_dates=[]
        waterlevels=[]

        observedValuesDict=defaultdict(list)

        for results in q2:
                
                # if results.waterlevel>0:

                st_ids.append(results.st_id)
                wl_dates.append(results.wl_date.strftime('%Y-%m-%d %H'))
                waterlevels.append(results.waterlevel)

                # print(results.st_id,results.wl_date)

            # print('Printing Quet Result ..')
            # print(results.st_id,results.wl_date,results.waterlevel)
            # if results.wl_date.strftime('%Y-%m-%d') >=entryDateString:
            #     st_ids.append(results.st_id)
            #     wl_dates.append(results.wl_date.strftime('%Y-%m-%d %H'))
            #     waterlevels.append(results.waterlevel)
                # print(results.st_id,results.wl_date.strftime('%Y-%m-%d %H'),results.waterlevel)

        
        for st_id,wl_date,waterlevel in zip(st_ids,wl_dates,waterlevels):
            # print(st_id,wl_date,waterlevel)
            observedValuesDict[st_id].append({wl_date:waterlevel})

        return JsonResponse(observedValuesDict,safe=False)

    
    # queryset = WaterLevelObservations.objects.filter(wl_date=entryDateTime).order_by('st_id','wl_date')
    # serializer_class = observedWaterlevelSerializer

class modifiedObservedViewSet(viewsets.ModelViewSet):

        
    # serializer_class = observedWaterlevelSerializer

    # def get_queryset(self):
    #     # Filter and return the most recent record
    #     queryset = WaterLevelObservations.objects.order_by('wl_date')[:1]
    #     return queryset

    def list(self, request, *args, **kwargs):
        
        from django.db.models import Q

        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        queryset = WaterLevelObservations.objects.values('st_id').annotate(max_wl_date=Max('wl_date')).order_by('st_id')
        most_recent_records = WaterLevelObservations.objects.filter(

            Q(wl_date=queryset.values('max_wl_date')[3:4])|Q(wl_date=queryset.values('max_wl_date')[1:2]),
            st_id__in=queryset.values('st_id'), 
        ).order_by('st_id','wl_date')


        waterlevelDict = defaultdict(dict)
        # for i, j,k  in zip(stationIDs, dates,waterlevel):
        #     waterlevelDict[i][j]=k

        for results in most_recent_records:
            st_id=results.st_id
            wl_date=results.wl_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            # wl_date=results.wl_date
            waterlevel=results.waterlevel
            waterlevelDict[st_id][wl_date]=waterlevel
            print(st_id,wl_date,waterlevel)
        # context=''
        return JsonResponse(waterlevelDict,safe=False)

    # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # # print('Entry Datetime in Last update Database Table: ',entryDateTime )

    # # queryset = WaterLevelObservations.objects.filter(wl_date =  entryDateTime).order_by('st_id','wl_date')
    # queryset = WaterLevelObservations.objects.values('st_id').annotate(max_created_at=Max('wl_date')).order_by()
    # for results in queryset:
    #     print(results)

    # serializer_class = observedWaterlevelSerializer

class observedWaterlevelViewSet(viewsets.ModelViewSet):
    

    entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # print('Entry Datetime in Last update Database Table: ',entryDateTime )
    previousThreehourEntryDatetime = entryDateTime - timedelta(hours=3)
    # print('Previous Three Hour Entry Datetime: ', previousThreehourEntryDatetime)



    # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    # print('Entry Datetime (in Observed) : ', entryDateTime)



    # getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=1).order_by('-wl_date').values_list('wl_date',flat=True)[0]
    # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
    # hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
    # lastUpdateDateTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")

    # lastUpdateDate = FfwcLastUpdateDate.objects.values_list('last_update_date')[0]
    # print('Last Update Date: ', lastUpdateDate[0])

    # entryDate = FfwcLastUpdateDate.objects.values_list('entry_date')[0][0]
    # entryHour=datetime.strptime(str(entryDate.hour)+':00:00','%H:%M:%S').time()
    
    # lastUpdateDateTime= datetime.combine(entryDate, entryHour) - timedelta(hours=1)
    # hourPart=lastUpdateDateTime.time()

    # entryHour= entryHour - timedelta(hours=1) 
    # print('Last Entry Date: ', databaseDate)

    # getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=1).order_by('-wl_date').values_list('wl_date',flat=True)[0]
    # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
    
    # print('Last Update Time based on Database: ', lastUpdateDateTime)

    # hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
    # databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")


    # queryDate= datetime.combine(date.today(), hourPart)- timedelta(hours=3)
    # queryDate= datetime.combine(date.today(), hourPart)- timedelta(hours=0)

    # print('Observed By Station Database Time: ' , lastUpdateDateTime)
    # # print('Observed By Station Hour Part: ', hourPart)
    # print('Observed By Station Query Datetime: ', queryDate)
    

    # if (lastUpdateDateTime==queryDate):
    #     print('Database Time ==  Query Time')
    #     pass
    #     # queryDate = datetime.combine(date.today(), hourPart)
    #     # queryDate=datetime.combine(date.today()-timedelta(days=1), hourPart)
    #     # print('Obsered Query Date: ', queryDate)
    # elif (lastUpdateDateTime <= queryDate):
    #     print('Database Time Not Equal  Query Time')
    #     queryDate=datetime.combine(date.today()-timedelta(days=1), hourPart)
    #     print('Obsered Query Date: ', queryDate)


    # queryset = WaterLevelObservations.objects.filter(wl_date=fixedDate).order_by('st_id','wl_date')
    # queryset = WaterLevelObservations.objects.filter(wl_date=lastUpdateDateTime).order_by('st_id','wl_date')

    # date = datetime.strptime('2024-07-16 12:00:00',"%Y-%m-%d %H:%M:%S")
    # print('Entry Date in Observed View: ', date)

    # queryset = WaterLevelObservations.objects.filter(wl_date=queryDate).order_by('st_id','wl_date')
    # queryset = WaterLevelObservations.objects.filter(wl_date__year=2024).order_by('st_id','wl_date')

    # if WaterLevelObservations.objects.filter(wl_date=entryDateTime).order_by('st_id','wl_date').exists():
        # q1 = WaterLevelObservations.objects.values('st_id').annotate(max_timestamp=Max('wl_date')).order_by('st_id')

    
    latest_record = WaterLevelObservations.objects.latest('wl_date')
    entryDateTime = latest_record.wl_date

    queryset = WaterLevelObservations.objects.filter(wl_date =  entryDateTime).order_by('st_id','wl_date')
    if (len(queryset))==0:
        queryset = WaterLevelObservations.objects.filter(wl_date =  previousThreehourEntryDatetime).order_by('st_id','wl_date')

    # print(len(queryset))
    # queryset = WaterLevelObservations.objects.values('st_id').annotate(wl_date=Max('wl_date'))
    serializer_class = observedWaterlevelSerializer



    def observedWaterlevelByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        if (WaterLevelObservations.objects.filter(st_id=stationId)).exists():
            print('Station Exists : ', stationId)
        else:
            print('Station Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=stationId).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        
        print('Station Id: ', stationId, 'Last Update Time: ',getLastUpdateTime)

        lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

        hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")
        queryDate= datetime.combine(date.today(), hourPart)

        serializer_class = observedWaterlevelSerializer

        queryset = WaterLevelObservations.objects.filter(
            st_id=stationId,
            wl_date=databaseTime
            # wl_date__gte=databaseTime-timedelta(days=7)
            )

        serializer = observedWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)


    def sevenDaysobservedWaterlevelByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        if (WaterLevelObservations.objects.filter(st_id=stationId)).exists():
            print('Station Observed Exists : ', stationId)
        else:
            print('Station Observed Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=stationId).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        # getLastUpdateTime.replace(hour=6)
        
        print('Station Id: ', stationId, 'Last Update Time: ',getLastUpdateTime)

        lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

        hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")
        newDatabaseTime=databaseTime.replace(hour=6)
        
        queryDate= datetime.combine(date.today(), hourPart)

        serializer_class = observedWaterlevelSerializer

     
        queryset = WaterLevelObservations.objects.filter(
            st_id=stationId,
            # wl_date=databaseTime
            wl_date__gte=newDatabaseTime-timedelta(days=7)
            ).order_by('wl_date')

        serializer = observedWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)

    def waterlevelByStationToday(self,request,**kwargs):

        print(' . . In Waterlevel by Station for Present Day . . ')
        stationId=self.kwargs['st_id']
        startDate=self.kwargs['startDate']
        startDate=startDate+'T00:00:00Z'
        
        lastUpdateDateTime= datetime.strptime(startDate,"%Y-%m-%dT%H:%M:%SZ") 
        latest_record = WaterLevelObservations.objects.filter(st_id=stationId).latest('wl_date')
        print('In Waterlevel Observation By Station and For Today: ', latest_record.wl_date)
        lastUpdateDateTime = latest_record.wl_date

    # wl_date__gte=lastUpdateDateTime-timedelta(days=0),
    # wl_date__=lastUpdateDateTime+timedelta(days=1)

        queryset = WaterLevelObservations.objects.filter(
            st_id=stationId,
            waterlevel__gte=0
            )
        # queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=databaseTime)
        
        serializer= observedWaterlevelSerializer(queryset,many=True)

        # latest_queryset = queryset.latest('wl_date') 
        # serializer= observedWaterlevelSerializer(latest_queryset)
        
        return Response(serializer.data)

    def waterlevelByStationAndDate(self,request,**kwargs):

        print(' . . In Waterlevel by Station And Date . . ')
        stationId=self.kwargs['st_id']
        startDate=self.kwargs['startDate']
        startDate=startDate+'T06:00:00Z'
        
        lastUpdateDateTime= datetime.strptime(startDate,"%Y-%m-%dT%H:%M:%SZ") 
        queryset = WaterLevelObservations.objects.filter(
            st_id=stationId,
            wl_date__gte=lastUpdateDateTime-timedelta(days=40),
            wl_date__lte=lastUpdateDateTime-timedelta(days=0)
            ).order_by('-wl_date')
        # queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=databaseTime)
        
        serializer= observedWaterlevelSerializer(queryset,many=True)
        
        return Response(serializer.data)

    def waterlevelSumByStationAndYear(self,request,**kwargs):

        stationId=self.kwargs['st_id']
        year=int(self.kwargs['year'])
        months=[4,5,6,7,8,9,10]
        
        waterlevelDict={}

        for month in months:

            queryset= WaterLevelObservations.objects\
            .filter(st_id=stationId)\
            .filter(wl_date__year__gte=year,wl_date__month__gte=month)\
            .filter(wl_date__year__lte=year,wl_date__month__lte=month)\
            .aggregate(Avg("waterlevel"))

            waterlevelDict[month]=queryset

        return JsonResponse(waterlevelDict,safe=False)

    def waterlevelMaxByStationAndYear(self,request,**kwargs):

        stationId=self.kwargs['st_id']
        year=int(self.kwargs['year'])
        months=[4,5,6,7,8,9,10]
        
        waterlevelDict={}

        for month in months:

            queryset= WaterLevelObservations.objects\
            .filter(st_id=stationId)\
            .filter(wl_date__year__gte=year,wl_date__month__gte=month)\
            .filter(wl_date__year__lte=year,wl_date__month__lte=month)\
            .aggregate(Max("waterlevel"))

            waterlevelDict[month]=queryset

        return JsonResponse(waterlevelDict,safe=False)


    def observedWaterlevelTrendByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        stationQueryset=FfwcStations2023.objects.filter(id=stationId)[0]
        dangerLevel= float(stationQueryset.dangerlevel)
        print('Station Danger Level: ', dangerLevel)

        if (WaterLevelObservations.objects.filter(st_id=stationId)).exists():
            
            print('Station Observed Exists : ', stationId)
        else:
            pass 
            # return JsonResponse(None,safe=False)

        getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=stationId).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        print('Station Id: ', stationId, 'Last Update Time: ',getLastUpdateTime)

        lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
        hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")
        newDatabaseTime=databaseTime.replace(hour=6)


        d1 = databaseTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        lastObservedWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d1)[0]
        lastObservedWaterlevel= float(lastObservedWaterlevelQ.waterlevel)
        print('Last Observed Waterlevel: ', lastObservedWaterlevel)

        d2 = d1-timedelta(days=0,hours=3,minutes=0,seconds=0)
        lastLastObservedWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d2)[0]
        lastLastObservedWaterlevel= float(lastLastObservedWaterlevelQ.waterlevel)
        print('Second to Last Observed Waterlevel: ', lastLastObservedWaterlevel)

        d3 = d1-timedelta(days=1,hours=0,minutes=0,seconds=0)
        previousDaydWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d3)[0]
        previoudDayObservedWaterlevel= float(previousDaydWaterlevelQ.waterlevel)
        print('Last 24th Hours Observed Waterlevel: ', previoudDayObservedWaterlevel)

        change24= round(float(lastObservedWaterlevel-previoudDayObservedWaterlevel),3)
        print('Change of Value from Previous Day: ',change24 )

        observedWaterlevelFromPreviousWaterlevel = round(float(lastObservedWaterlevel-lastLastObservedWaterlevel),2)
        print('Recent Trend of Observed Waterlevel: ', observedWaterlevelFromPreviousWaterlevel)

        observedWaterlevelFromDangerLevel = round(float(lastObservedWaterlevel-dangerLevel),2)
        print('Observed Waterlevel from Dangerlevel: ',observedWaterlevelFromDangerLevel )

        status=''
        trends=''



        if (observedWaterlevelFromDangerLevel > 0): status = str(observedWaterlevelFromDangerLevel)+'cm Above Danger Level'
        else: status = str(observedWaterlevelFromDangerLevel)+'cm Below Danger Level'

        if(observedWaterlevelFromPreviousWaterlevel>0):trend='Rising'
        elif(observedWaterlevelFromPreviousWaterlevel<0):trend='Falling'
        elif(observedWaterlevelFromPreviousWaterlevel==0):trend='Steady'

        stationsTrend = {
            'Status':status,
            'Trend':trend,
            'Value':observedWaterlevelFromPreviousWaterlevel,
            '24h':change24
        }

        # # d1 = newDatabaseTime-timedelta(days=2)
        # d2 = d1-timedelta(days=0,hours=3,minutes=0,seconds=0)
        # # d1 = datetime.strptime(lastForecastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")+timedelta(days=0,hours=0,minutes=0,seconds=0)

        # q1 = WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d2).order_by('wl_date')
        # q2 = WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d1).order_by('wl_date')

        # q3=q1.union(q2)

        # waterlevel=[]
        # stationIDs=[]
        # dates=[]

        # for results in q3:
        #     print(results)
        #     print(results.wl_date)
        #     stationIDs.append(results.st_id)
        #     dates.append(results.wl_date.strftime("%Y-%m-%dT%H"))
        #     # dates.append(results.wl_date)
        #     waterlevel.append(results.waterlevel)

        # waterlevelDict = defaultdict(list)
        # for i, j,k  in zip(stationIDs, dates,waterlevel):
        #     waterlevelDict[i].append({j:k})

        return JsonResponse(stationsTrend,safe=False)

        # serializer_class = observedWaterlevelSerializer
        # queryset = WaterLevelObservations.objects.filter(


        #     st_id=stationId,
        #     wl_date__gte=d1
        #     ).order_by('wl_date')

        # serializer = observedWaterlevelSerializer(queryset,many=True)
        # return Response(serializer.data)

observed_waterlevel_by_station=observedWaterlevelViewSet.as_view({'get':'observedWaterlevelByStation'})
seven_days_observed_waterlevel_by_station=observedWaterlevelViewSet.as_view({'get':'sevenDaysobservedWaterlevelByStation'})
observed_waterlevel_by_station_and_today=observedWaterlevelViewSet.as_view({'get':'waterlevelByStationToday'})
observed_waterlevel_by_station_and_date=observedWaterlevelViewSet.as_view({'get':'waterlevelByStationAndDate'})
observed_waterlevel_sum_by_station_and_year=observedWaterlevelViewSet.as_view({'get':'waterlevelSumByStationAndYear'})
observed_waterlevel_max_by_station_and_year=observedWaterlevelViewSet.as_view({'get':'waterlevelMaxByStationAndYear'})
observed_waterlevel_trend_by_station=observedWaterlevelViewSet.as_view({'get':'observedWaterlevelTrendByStation'})


# Trend ViewSet
class AnnotatedObservedTrendViewSet(viewsets.ModelViewSet):

    # print('Entry Date Time String in Observed Tend Viewset: ', entryDateTimeString)
    # print(stationIDs)
    # serializer_class = observedWaterlevelSerializer

    def list(self, request, *args, **kwargs):

        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        latest_record = WaterLevelObservations.objects.latest('wl_date')
        entryDateTime =  latest_record.wl_date

        # d1 = datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")-timedelta(days=1,hours=0,minutes=0,seconds=0)
        d1 = entryDateTime-timedelta(days=0,hours=0,minutes=0,seconds=0)
        # print('Day 1 Date: ', d1)
        d2=entryDateTime-timedelta(days=2,hours=0,minutes=0,seconds=0)
        # print('Day 2 Date: ', d2)
 

        waterleveDatelDict=defaultdict(list)
        waterleveValueslDict=defaultdict(list)

        waterlevelDict={}

        # q1 = WaterLevelObservations.objects.values('st_id').annotate(max_timestamp=Max('wl_date')).order_by('st_id')
        q1 = WaterLevelObservations.objects.values('st_id','wl_date','waterlevel').filter(wl_date__gte=d2
        ).order_by('st_id','-wl_date')
        
        for results in q1:
            # print(results)
            st_id = results['st_id']

            wl_date = results['wl_date']
            waterleveDatelDict[st_id].append(wl_date)

            waterlevel = results['waterlevel']
            waterleveValueslDict[st_id].append(waterlevel)

            # waterlevelDict[st_id]={wl_date:waterlevel}
        
        for key in waterleveDatelDict.keys():
            #  print(key, waterleveDatelDict[key])
            #  print(datetime.strftime(waterleveDatelDict[key],"%Y-%m-%dT%H:%M:%SZ"))
             waterlevelDict[key] = {'wl_date': waterleveDatelDict[key], 'waterlevel': waterleveValueslDict[key]}
            #  print(waterlevelDict[key]['wl_date'])
  
        # for date,value in zip(waterleveDatelDict.values(), waterleveValueslDict.values()):
        #     print(date,":",value)
            # waterlevelDict[keys]={waterleveDatelDict[keys]:waterleveValueslDict[keys]}


        # date_list = waterlevelDict[1]['wl_date']    
        # hour_diff_list = [date_list[0] - date_list[i] for i in range(len(date_list))]
        # hour_diff_list = [item.seconds//3600 for  item in hour_diff_list]

        # value_list= waterlevelDict[1]['waterlevel']   
        # value_diff_list = [value_list[0] - value_list[i] for i in range(len(value_list))]
        # value_diff_list = [item.seconds//3600 for  item in subtracted_list]

        # days = duration.days
        # hours = duration.seconds // 3600
        # minutes = (duration.seconds % 3600) // 60

        # print(hour_diff_list,value_diff_list)

        # print(waterlevelDict)

        # hour3='na'
        # value24='na'
        # hour24='na'
        station_value_diff_by_hour={}


        for key in waterlevelDict.keys():
       
            lengthOfDateList = len(waterlevelDict[key]['wl_date'])
            # print(key,lengthOfDateList)

            if(lengthOfDateList>1):
                # print('Length of Date List: ', lengthOfDateList)
                for index in range(lengthOfDateList):
                    

                    date = waterlevelDict[key]['wl_date'][index]
                    waterlevel = waterlevelDict[key]['waterlevel'][index]

                    date_list = waterlevelDict[key]['wl_date']   
                    # print(date_list,waterlevel)


                    hour_diff_list = [date_list[0] - date_list[i] for i in range(len(date_list))]
                    hour_diff_list = [item.seconds//3600 for  item in hour_diff_list]
                    
                    value_list= waterlevelDict[key]['waterlevel']   
                    value_diff_list = [value_list[0] - value_list[i] for i in range(len(value_list))]

                    # print(hour_diff_list)
                    
                    # print(key,': ',hour_diff_list)
                    # hour3=hour_diff_list[0]
                    # print(hour_diff_list)
                    hour3=3


                    try: 
                        
                        # second_index = hour_diff_list.index(0,hour_diff_list.index(0)+1)
                        # print('Second Index: ', hour_diff_list.index(0))
                        hour24= 24
                        value24=value_diff_list[1]

                    except:
                        value24='na'
                        hour24='na'
                        hour3='na'
        
                    value3=value_diff_list[1]
                    # print({'wl_date': [hour3,hour24], 'waterlevel': [value3,value24]})
                    station_value_diff_by_hour[key] = {'wl_date': [hour3,hour24], 'waterlevel': [value3,value24]}


        # for key in waterlevelDict.keys():
        #     lengthOfDateList = len(waterlevelDict[key]['wl_date'])
        #     for index in range(lengthOfDateList):
        #         date_list = waterlevelDict[key]['wl_date']   
        #         second_index = date_list.index('0',date_list.index('0')+1)
        #         value_list= waterlevelDict[key]['waterlevel']
        #         value24 =   value_list[second_index] 
        #         print(date_list[second_index],value24)

        # second_index = my_list.index(1, my_list.index(1) + 1)

    

        return JsonResponse(station_value_diff_by_hour,safe=False)

# Trend ViewSet
class ObservedTrendViewSet(viewsets.ModelViewSet):

    # print('Entry Date Time String in Observed Tend Viewset: ', entryDateTimeString)
    # print(stationIDs)
    # serializer_class = observedWaterlevelSerializer

    def list(self, request, *args, **kwargs):


        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        # d1 = datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")-timedelta(days=1,hours=0,minutes=0,seconds=0)

        d1 = entryDateTime-timedelta(days=0,hours=0,minutes=0,seconds=0)
        # print('Day 1 Date: ', d1)
        d2=entryDateTime-timedelta(days=1,hours=0,minutes=0,seconds=0)
        # print('Day 2 Date: ', d2)
        d3=entryDateTime-timedelta(days=0,hours=3,minutes=0,seconds=0)
        # print('Day 3 Date: ', d3)
        # d4=entryDateTime-timedelta(days=0,hours=6,minutes=0,seconds=0)
        # print('Day 4 Date: ', d4)



        q1 = WaterLevelObservations.objects.filter(
            wl_date=d1,
            ).order_by('st_id','wl_date')

        q2 = WaterLevelObservations.objects.filter(
            wl_date=d2,
            ).order_by('st_id','wl_date')

        q3 = WaterLevelObservations.objects.filter(
            wl_date=d3,
            ).order_by('st_id','wl_date')

        
        # q4 = WaterLevelObservations.objects.filter(
        #     wl_date=d4,
        #     ).order_by('st_id','wl_date')

        # q5=q3.union(q2)
        q4=q2.union(q1)


        stationIDs=[]
        stationNames={}
        dates=[]
        waterlevel=[]

        for results in q4:

            # print(results.st_id,results.wl_date,results.waterlevel)
            stationIDs.append(results.st_id)
            # station_name=FfwcStations2023.objects.filter(id=results.st_id).values_list('name',flat=True)[0]
            # stationNames[results.st_id]=station_name
            # print(station_name)
            dates.append(results.wl_date.strftime("%d-%m-%Y %H"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(list)
        # waterlevelByStationDict=defaultdict(list)

        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i].append({j:k})
            # # stationNames[i]={j:k}
            # waterlevelByStationDict[stationNames[i]].append({j:k})
            # waterlevelDict[i]=waterlevelByStationDict

        # print(waterlevelDict)

        previousTimestampStationIDs=[]
        previousTimestampDate=[]
        previousTimestampWaterlevel=[]
        previousTimestampWaterlevelDict = defaultdict(list)
        for results in q3:
            previousTimestampStationIDs.append(results.st_id)
            previousTimestampDate.append(results.wl_date.strftime("%d-%m-%Y %H"))
            previousTimestampWaterlevel.append(results.waterlevel)
        
        for i, j,k  in zip(previousTimestampStationIDs, previousTimestampDate,previousTimestampWaterlevel):
            previousTimestampWaterlevelDict[i].append({j:k})


        for key in waterlevelDict.keys():

            if(len(previousTimestampWaterlevelDict[key]))>0:
                waterlevelDict[key].append(previousTimestampWaterlevelDict[int(key)][0])

        
        # # print(waterlevelDict[key])

        outer_sub_list={}

        if (len(waterlevelDict))>0:

            for key in waterlevelDict.keys():

                dateValueList=waterlevelDict[key]
                valueList=[list(value.values())[0] for value in dateValueList]

                if(len(valueList))>=3:
                    sub_list = [element - valueList[i-2] for i, element in enumerate(valueList)]
                    outer_sub_list[key]=sub_list
        
        # print(outer_sub_list)

        return JsonResponse(outer_sub_list,safe=False)



# Three Days Observed Water Level
class threeDaysObservedWaterlevelViewSet(viewsets.ModelViewSet):

    hourInput='T00'
    observedDate=dateInput+hourInput+':00:00Z'

    # print('Three Days Observed Datetime: ', observedDate)

    getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=1).order_by('-wl_date').values_list('wl_date',flat=True)[0]
    lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

    serializer_class = observedWaterlevelSerializer

    def list(self, request, *args, **kwargs):


        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateTime = entryDateTime.replace(hour=6)
        print('Entry Datetime in Three Days Observed: ', entryDateTime)


        # getLastUpdateTime=WaterLevelObservations.objects.filter(st_id=60).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
        # print('Three Days Observed Datetime: ', lastUpdateDateTime)

        # # d1 = datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")-timedelta(days=0)
        # # d1 =datetime.strptime(dateInput,"%Y-%m-%d")-timedelta(days=0)

        latest_record = WaterLevelObservations.objects.latest('wl_date')


        d1 = latest_record.wl_date-timedelta(days=0)
        d2 = latest_record.wl_date-timedelta(days=1)
        d3 = latest_record.wl_date-timedelta(days=2)

        # d1 = entryDateTime-timedelta(days=0)
        # d2 = entryDateTime-timedelta(days=1)
        # d3 = entryDateTime-timedelta(days=2)

        q1 = WaterLevelObservations.objects.filter(
            wl_date=d3,
            ).order_by('st_id','wl_date')

        q2 = WaterLevelObservations.objects.filter(
            wl_date=d2,
            ).order_by('st_id','wl_date')

        q3 = WaterLevelObservations.objects.filter(
            wl_date=d1,
            ).order_by('st_id','wl_date')

        q4=q1.union(q2,q3)


        stationIDs=[]
        stationNames={}
        dates=[]
        waterlevel=[]

        for results in q4:
            stationIDs.append(results.st_id)
            station_name=FfwcStations2023.objects.filter(id=results.st_id).values_list('name',flat=True)[0]
            stationNames[results.st_id]=station_name
            # print(station_name)
            dates.append(results.wl_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(list)
        # waterlevelByStationDict=defaultdict(list)

        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i].append({j:k})
            # # stationNames[i]={j:k}
            # waterlevelByStationDict[stationNames[i]].append({j:k})
            # waterlevelDict[i]=waterlevelByStationDict

        station_keys = list(waterlevelDict.keys())
        date_length = len(waterlevelDict[station_keys[0]])
        print('Date Length: ', date_length)

        # if(date_length <3):
        #     three_days_ago = entryDateTime-timedelta(days=3)
        #     # Get the latest entries from the last three days
        #     latest_entries = WaterLevelObservations.objects.filter(wl_date__gte=three_days_ago)


        #     latest_entries_with_row_number = (
        #         latest_entries.annotate(
        #             row_number=Window(
        #                 expression=RowNumber(),
        #                 partition_by=F('st_id'),
        #                 order_by=F('wl_date').desc()
        #             )
        #         )
        #     )

        #     # Filter to get only the latest three entries for each unique_id
            # latest_three_days_data = latest_entries_with_row_number.filter(row_number__lte=3)

            # If you want to see the results
            # for entry in latest_three_days_data:
            #     # waterlevelDict = defaultdict(list)
            #     print(entry.st_id, entry.wl_date, entry.waterlevel)

        return JsonResponse(waterlevelDict,safe=False)


class modifiedForecastWaterlevelViewSet(viewsets.ModelViewSet):

# Model1.objects.raw('SELECT * FROM model1 JOIN model2 ON model1.column = model2.column')
# SELECT ffwc_stations_2023.name, water_level_observations.waterLevel FROM water_level_observations JOIN ffwc_stations_2023 ON water_level_observations.st_id = ffwc_stations_2023.id
        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")

        queryset = WaterLevelForecasts.objects.extra(
            tables=[data_load_models.FfwcStations2023],
            where=[WaterLevelForecasts.st_id == FfwcStations2023.id],
            select={'extra_field': FfwcStations2023.name}
        )
        serializer_class = serializers.forecastWaterlevelSerializer



class forecastWaterlevelViewSet(viewsets.ModelViewSet):

    entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    

    # # print('In Forecast View .. ')
    # getLastUpdateTime=WaterLevelForecasts.objects.filter(st_id=5).order_by('-fc_date').values_list('fc_date',flat=True)[0]
    # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
    # # hourPart=datetime.strftime(getLastUpdateTime,"%H:%M:%SZ")

    # hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
    # databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")
    # queryDate= datetime.combine(date.today(), hourPart)

    # print('Database Time: ' , databaseTime)
    # print('Hour Part: ', hourPart)
    # print('Query Datetime: ', queryDate)


    # queryset = WaterLevelForecasts.objects.filter(fc_date__gte=date.today()-timedelta(days=0))
    queryset = WaterLevelForecasts.objects.filter(fc_date__gte=entryDateTime)
    serializer_class = forecastWaterlevelSerializer

    # filter_class = EventFilter

    def forecastWaterlevelByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        if (WaterLevelForecasts.objects.filter(st_id=stationId)).exists():
            print('Station Forecast Exists : ', stationId)
        else:
            print('Station Forecasts Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        lastObservedTime=WaterLevelObservations.objects.filter(st_id=stationId).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        getLastUpdateTime=WaterLevelForecasts.objects.filter(st_id=stationId).order_by('-fc_date').values_list('fc_date',flat=True)[0]
        lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

        print('Forecast Waterleve Date: ',lastUpdateDateTime )
        # hourPart=datetime.strftime(getLastUpdateTime,"%H:%M:%SZ")

        hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")-timedelta(days=7,hours=0, minutes=0)
        queryDate= datetime.combine(date.today(), hourPart)


        # queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=lastObservedTime)
        queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=databaseTime)
        
        serializer= forecastWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)

    def fiveDaysForecastWaterlevel(self,request,**kwargs):
        
        # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        # entryDateTime=entryDateTime.replace(hour=6)
        # print('In Five Days Forecast Present Day: ', entryDateTime)


        latest_entry = WaterLevelForecasts.objects.latest('fc_date')
        entryDateTime = latest_entry.fc_date
        print('In Five Days Forecast Present Day: ', entryDateTime)

        # getLastUpdateTime=WaterLevelForecasts.objects.filter(st_id=40).order_by('-fc_date').values_list('fc_date',flat=True)[0]
        # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
        # lastUpdateDateTime= datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ") 

        # # lastUpdateDateTime=lastUpdateDateTime-timedelta(days=4)
        # lastUpdateDateTime=datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")
        # # print('In Five Days Forecast lastUpdateDateTime: ', lastUpdateDateTime)
        # # observedDate

        # queryDate = datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")
        # # print('Query Date Time: ',queryDate)

        # databaseEntryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        # print('Database Entry Date in Forecast View: ', databaseEntryDateTime)
        # d1 = lastUpdateDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
  
        d1 = entryDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        # d1 = datetime.strptime(lastForecastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")+timedelta(days=0,hours=0,minutes=0,seconds=0)

        d2=entryDateTime+timedelta(days=1,hours=0,minutes=0,seconds=0)
        d3=entryDateTime+timedelta(days=2,hours=0,minutes=0,seconds=0)
        d4=entryDateTime+timedelta(days=3,hours=0,minutes=0,seconds=0)
        d5=entryDateTime+timedelta(days=4,hours=0,minutes=0,seconds=0)



        q1 = WaterLevelForecasts.objects.filter(
            fc_date=d1,
            ).order_by('st_id','fc_date')

        q2 = WaterLevelForecasts.objects.filter(
            fc_date=d2,
            ).order_by('st_id','fc_date')

        q3 = WaterLevelForecasts.objects.filter(
            fc_date=d3,
            ).order_by('st_id','fc_date')
        

        q4 = WaterLevelForecasts.objects.filter(
            fc_date=d4,
            ).order_by('st_id','fc_date')
        

        q5 = WaterLevelForecasts.objects.filter(
            fc_date=d5,
            ).order_by('st_id','fc_date')


        q6=q1.union(q2,q3,q4,q5)
        # q5=q4.union(q3)

        # q2.union(q1)

        # q1.union(q2,q3)

        waterlevel=[]
        stationIDs=[]
        dates=[]

        for results in q6:

            stationIDs.append(results.st_id)
            dates.append(results.fc_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(list)
        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i].append({j:k})

        return JsonResponse(waterlevelDict,safe=False)


    # Five Days 24 Hourly
    def fiveDaysForecastWaterlevelForEvery24Hours(self,request,**kwargs):
        
        # print('Entry ')
        # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")

        latest_entry = WaterLevelForecasts.objects.latest('fc_date')
        entryDateTime = latest_entry.fc_date
        # entryDateTime = entryDateTime.replace(hour=6)
        print('In Five Days Forecast(From): ', entryDateTime)

        d1 = entryDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        d2=d1+timedelta(days=1,hours=0,minutes=0,seconds=0)
        d3=d1+timedelta(days=2,hours=0,minutes=0,seconds=0)
        d4=d1+timedelta(days=3,hours=0,minutes=0,seconds=0)
        d5=d1+timedelta(days=4,hours=0,minutes=0,seconds=0)
        d6=d1+timedelta(days=5,hours=0,minutes=0,seconds=0)
        # d7=d1+timedelta(days=6,hours=0,minutes=0,seconds=0)


        q1 = WaterLevelForecasts.objects.filter(
            fc_date=d1
            ).order_by('st_id','fc_date')

        # for results in q1:
        #     print(results.fc_date)
        q2 = WaterLevelForecasts.objects.filter(
            fc_date=d2,
            ).order_by('st_id','fc_date')

        q3 = WaterLevelForecasts.objects.filter(
            fc_date=d3,
            ).order_by('st_id','fc_date')
        

        q4 = WaterLevelForecasts.objects.filter(
            fc_date=d4,
            ).order_by('st_id','fc_date')
        

        q5 = WaterLevelForecasts.objects.filter(
            fc_date=d5,
            ).order_by('st_id','fc_date')

        q6 = WaterLevelForecasts.objects.filter(
            fc_date=d6,
            ).order_by('st_id','fc_date')

    
        # q7 = WaterLevelForecasts.objects.filter(
        #     fc_date=d7,
        #     ).order_by('st_id','fc_date')


        q7=q1.union(q2,q3,q4,q5,q5,q6)

        waterlevel=[]
        stationIDs=[]
        dates=[]

        for results in q7:

            stationIDs.append(results.st_id)
            dates.append(results.fc_date.strftime("%m-%d-%Y"))
            # dates.append(results.fc_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(dict)
        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i][j]=k

        return JsonResponse(waterlevelDict,safe=False)



    def sevenDaysForecastWaterlevelForEvery24Hours(self,request,**kwargs):
        
        # print('Entry ')
        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateTime = entryDateTime.replace(hour=6)
        print('In Seven Days Forecast(From): ', entryDateTime)

        most_recent_date = WaterLevelForecasts.objects.aggregate(max_date=Max('fc_date'))['max_date']
        print('Most Recent Date: ',most_recent_date )

        # d1 = entryDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        d1 = most_recent_date+timedelta(days=0,hours=0,minutes=0,seconds=0)
        # d1 = datetime.strptime(lastForecastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")+timedelta(days=0,hours=0,minutes=0,seconds=0)

        d2=d1+timedelta(days=1,hours=0,minutes=0,seconds=0)
        d3=d1+timedelta(days=2,hours=0,minutes=0,seconds=0)
        d4=d1+timedelta(days=3,hours=0,minutes=0,seconds=0)
        d5=d1+timedelta(days=4,hours=0,minutes=0,seconds=0)
        d6=d1+timedelta(days=5,hours=0,minutes=0,seconds=0)
        d7=d1+timedelta(days=6,hours=0,minutes=0,seconds=0)


        q1 = WaterLevelForecasts.objects.filter(
            fc_date=d1
            ).order_by('st_id','fc_date')

        # for results in q1:
        #     print(results.fc_date)
        q2 = WaterLevelForecasts.objects.filter(
            fc_date=d2,
            ).order_by('st_id','fc_date')

        q3 = WaterLevelForecasts.objects.filter(
            fc_date=d3,
            ).order_by('st_id','fc_date')
        

        q4 = WaterLevelForecasts.objects.filter(
            fc_date=d4,
            ).order_by('st_id','fc_date')
        

        q5 = WaterLevelForecasts.objects.filter(
            fc_date=d5,
            ).order_by('st_id','fc_date')

        q6 = WaterLevelForecasts.objects.filter(
            fc_date=d6,
            ).order_by('st_id','fc_date')

    
        q7 = WaterLevelForecasts.objects.filter(
            fc_date=d7,
            ).order_by('st_id','fc_date')


        q8=q1.union(q2,q3,q4,q5,q5,q6,q7)

        waterlevel=[]
        stationIDs=[]
        dates=[]

        for results in q8:

            stationIDs.append(results.st_id)
            dates.append(results.fc_date.strftime("%m-%d-%Y"))
            # dates.append(results.fc_date.strftime("%d-%m-%Y"))
            waterlevel.append(results.waterlevel)
           
        waterlevelDict = defaultdict(dict)
        for i, j,k  in zip(stationIDs, dates,waterlevel):
            waterlevelDict[i][j]=k

        return JsonResponse(waterlevelDict,safe=False)


    def SevenDaysForecastWaterlevelByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        if (WaterLevelForecasts.objects.filter(st_id=stationId)).exists():
            print('Station Forecast Exists : ', stationId)
        else:
            print('Station Forecasts Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        lastObservedTime=WaterLevelObservations.objects.filter(st_id=stationId).order_by('-wl_date').values_list('wl_date',flat=True)[0]
        getLastUpdateTime=WaterLevelForecasts.objects.filter(st_id=stationId).order_by('-fc_date').values_list('fc_date',flat=True)[0]
        lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

        print('Forecast Waterleve Date: ',lastUpdateDateTime )
        # hourPart=datetime.strftime(getLastUpdateTime,"%H:%M:%SZ")

        hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")-timedelta(days=9,hours=0, minutes=0)
        queryDate= datetime.combine(date.today(), hourPart)


        # queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=lastObservedTime)
        queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=databaseTime)
        
        serializer= forecastWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)


    # Ten Days Forecast 24 Hours
    def tenDaysForecastWaterlevelForEvery24Hours(self,request,**kwargs):
        
        experimentalLastUpdateDate=datetime.strptime(experimentalLastUpdateDatestring,"%Y-%m-%d")
        print('Last Update Date in Ten Days Forecast:  ', experimentalLastUpdateDate)
        # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        experimentalLastUpdateDateTime = experimentalLastUpdateDate.replace(hour=6)
        print('Last Update Date-Time in Ten Days Forecast:  ', experimentalLastUpdateDateTime)

        d1 = experimentalLastUpdateDateTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
        d2=d1+timedelta(days=1,hours=0,minutes=0,seconds=0)
        d3=d1+timedelta(days=2,hours=0,minutes=0,seconds=0)
        d4=d1+timedelta(days=3,hours=0,minutes=0,seconds=0)
        d5=d1+timedelta(days=4,hours=0,minutes=0,seconds=0)
        d6=d1+timedelta(days=5,hours=0,minutes=0,seconds=0)
        d7=d1+timedelta(days=6,hours=0,minutes=0,seconds=0)
        d8=d1+timedelta(days=7,hours=0,minutes=0,seconds=0)
        d9=d1+timedelta(days=8,hours=0,minutes=0,seconds=0)
        d10=d1+timedelta(days=9,hours=0,minutes=0,seconds=0)
        d11=d1+timedelta(days=10,hours=0,minutes=0,seconds=0)

        # print(d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11)



        q1 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d1
            ).order_by('st_id','fc_date')

        q2 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d2,
            ).order_by('st_id','fc_date')

        q3 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d3,
            ).order_by('st_id','fc_date')
        

        q4 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d4,
            ).order_by('st_id','fc_date')
        

        q5 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d5,
            ).order_by('st_id','fc_date')

        q6 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d6,
            ).order_by('st_id','fc_date')

    
        q7 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d7,
            ).order_by('st_id','fc_date')

        q8 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d8,
            ).order_by('st_id','fc_date')



        q9 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d9,
            ).order_by('st_id','fc_date')


        q10 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d10,
            ).order_by('st_id','fc_date')


        q11 = data_load_models.WaterLevelForecastsExperimentals.objects.filter(
            fc_date=d11,
            ).order_by('st_id','fc_date')
            
        q12=q1.union(q2,q3,q4,q5,q5,q6,q7,q8,q9,q10,q11)

        # q3 = q1.union(q2)

        stationIDs=[]
        dates=[]
        minWaterlevel=[]
        maxWaterlevel=[]
        meanWaterlevel=[]

        for results in q12:
            # print(results.st_id,results.fc_date,results.waterlevel_min,results.waterlevel_max,results.waterlevel_mean)

            stationIDs.append(results.st_id)
            dates.append(results.fc_date.strftime("%m-%d-%Y"))
            # # dates.append(results.fc_date.strftime("%d-%m-%Y"))
            minWaterlevel.append(results.waterlevel_min)
            maxWaterlevel.append(results.waterlevel_max)
            meanWaterlevel.append(results.waterlevel_mean)
           
        waterlevelDict = defaultdict(dict)

        for st_id,date,minlevel,maxlevel,meanlevel  in zip(stationIDs, dates,minWaterlevel,maxWaterlevel,meanWaterlevel):
            waterlevelDict[st_id][date]={'min':minlevel, 'max':maxlevel,'mean':meanlevel}

        return JsonResponse(waterlevelDict,safe=False)




forecast_waterlevel_by_station=forecastWaterlevelViewSet.as_view({'get':'forecastWaterlevelByStation'})
seven_days_forecast_waterlevel_by_station=forecastWaterlevelViewSet.as_view({'get':'SevenDaysForecastWaterlevelByStation'})

five_days_forecast_waterlevel=forecastWaterlevelViewSet.as_view({'get':'fiveDaysForecastWaterlevel'})
five_days_forecast_waterlevel_24_hours=forecastWaterlevelViewSet.as_view({'get':'fiveDaysForecastWaterlevelForEvery24Hours'})
seven_days_forecast_waterlevel_24_hours=forecastWaterlevelViewSet.as_view({'get':'sevenDaysForecastWaterlevelForEvery24Hours'})
ten_days_forecast_waterlevel_24_hours=forecastWaterlevelViewSet.as_view({'get':'tenDaysForecastWaterlevelForEvery24Hours'})


# 

class observedRainfallViewSet(viewsets.ModelViewSet):

    # print('Entry Date Time String in Observed Rainfall: ', entryDateTimeString)
    latest_entry = RainfallObservations.objects.latest('rf_date')
    entryDateTime = latest_entry.rf_date
    entryDate = entryDateTime.replace(day=1,hour=6)
    # entryDate = datetime.strptime(entryDateTimeString,'%Y-%m-%dT%H:%M:%SZ').replace(day=1,hour=6)

    print('Entry Date Time in Observed Rainfall: ', entryDate)

    queryset=RainfallObservations.objects.filter(rf_date__gte=entryDate
    ).values('st_id').annotate(total_rainfall=models.Sum('rainfall')
    ).order_by('st_id')
            
    serializer_class=rainfallObservationSerializer

    def rainfallByStation(self,request,**kwargs):

        print('In Rainfall by Station .. ')
        stationId=self.kwargs['st_id']

        entryDate = datetime.strptime(entryDateTimeString,'%Y-%m-%dT%H:%M:%SZ').replace(hour=6)
        print('Entry Date in Rainfall By Station: ', entryDate)

        latest_record = RainfallObservations.objects.filter(st_id=stationId).latest('rf_date')
        print('Latest Rainfall Record :', latest_record.rf_date)
        entryDate = latest_record.rf_date

        queryset = RainfallObservations.objects.filter(
            st_id=stationId,rf_date__gte=entryDate-timedelta(days=40)
            ).order_by('-rf_date')
        # queryset = WaterLevelForecasts.objects.filter(st_id=stationId,fc_date__gte=databaseTime)
        
        serializer= threeDaysObservedRainfallSerializer(queryset,many=True)
        
        return Response(serializer.data)

    def rainfallByStationAndDate(self,request,**kwargs):

        print(' . . In Rainfall by Station And Date . . ')
        stationId=self.kwargs['st_id']
        startDate=self.kwargs['startDate']
        startDate=startDate+'T06:00:00Z'
        
        # getLastUpdateTime=RainfallObservations.objects.filter(st_id=1).order_by('-rf_date').values_list('rf_date',flat=True)[0]
        # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
        lastUpdateDateTime= datetime.strptime(startDate,"%Y-%m-%dT%H:%M:%SZ") 

        # hourPart=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ").time()
        # databaseTime=datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ")
        # queryDate= datetime.combine(date.today(), hourPart)

        queryset = RainfallObservations.objects.filter(
            st_id=stationId,
            rf_date__gte=lastUpdateDateTime-timedelta(days=40)
            ).filter(rf_date__lte=lastUpdateDateTime-timedelta(days=0))
        
        serializer= threeDaysObservedRainfallSerializer(queryset,many=True)
        
        return Response(serializer.data)

    
    def rainfallSumByStationAndYear(self,request,**kwargs):

        stationId=self.kwargs['st_id']
        year=int(self.kwargs['year'])
        months=[4,5,6,7,8,9,10]
        
        rainfallDict={}

        for month in months:

            queryset= RainfallObservations.objects\
            .filter(st_id=stationId)\
            .filter(rf_date__year__gte=year,rf_date__month__gte=month)\
            .filter(rf_date__year__lte=year,rf_date__month__lte=month)\
            .aggregate(Avg("rainfall"))

            rainfallDict[month]=queryset

        return JsonResponse(rainfallDict,safe=False)

    
    def rainfallAvgByStationAndYear(self,request,**kwargs):

        stationId=self.kwargs['st_id']
        year=int(self.kwargs['year'])
        months=[4,5,6,7,8,9,10]
        
        rainfallDict={}

        for month in months:

            queryset= RainfallObservations.objects\
            .filter(st_id=stationId)\
            .filter(rf_date__year__gte=year,rf_date__month__gte=month)\
            .filter(rf_date__year__lte=year,rf_date__month__lte=month)\
            .aggregate(Max("rainfall"))

            rainfallDict[month]=queryset

        return JsonResponse(rainfallDict,safe=False)


rainfall_by_station=observedRainfallViewSet.as_view({'get':'rainfallByStation'})
rainfall_by_station_and_date=observedRainfallViewSet.as_view({'get':'rainfallByStationAndDate'})

rainfall_sum_by_station_and_year=observedRainfallViewSet.as_view({'get':'rainfallSumByStationAndYear'})
rainfall_avg_by_station_and_year=observedRainfallViewSet.as_view({'get':'rainfallAvgByStationAndYear'})



class threeDaysObservedRainfallViewSet(viewsets.ModelViewSet):

    getLastUpdateTime=RainfallObservations.objects.filter(st_id=1).order_by('-rf_date').values_list('rf_date',flat=True)[0]
    lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")

    serializer_class = threeDaysObservedRainfallSerializer

    def list(self, request, *args, **kwargs):

        latest_entry = RainfallObservations.objects.latest('rf_date')
        latest_entry_date_time = latest_entry.rf_date
        print('Latest Entry : ', latest_entry.rf_date)
        # entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ").replace(hour=6)
        # entryDateTime = datetime.strptime(latest_entry.rf_date,"%Y-%m-%dT%H:%M:%SZ").replace(hour=6)

        # entryDateTime = entryDateTime

        # hourInput='T06'
        # observedDate=dateInput+hourInput+':00:00Z'
        # observedDate= datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")

        # print('Three Days Observed Rainfall Datetime: ', observedDate)


        # lastForecastUpdateDateTime

        # getLastUpdateTime=RainfallObservations.objects.filter(st_id=1).order_by('-rf_date').values_list('rf_date',flat=True)[0]
        # lastUpdateDateTime=datetime.strftime(getLastUpdateTime,"%Y-%m-%dT%H:%M:%SZ")
        # lastUpdateDateTime= datetime.strptime(lastUpdateDateTime,"%Y-%m-%dT%H:%M:%SZ") 

        # print('Last Update Time in Rainfall: ',lastUpdateDateTime)

        # lastUpdateDateTime=lastUpdateDateTime-timedelta(days=10)

    

        # d1 = datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")
        # d1 = datetime.strptime(fixedDate,"%Y-%m-%dT%H:%M:%SZ")
        # d1 = datetime.strptime(observedDate,"%Y-%m-%dT%H:%M:%SZ")
        # d2=d1-timedelta(days=1,hours=0,minutes=0,seconds=0)
        # d3=d2-timedelta(days=1,hours=0,minutes=0,seconds=0)

        # today = datetime.today()
        # days=today.day
        
        queryset=RainfallObservations.objects.filter(rf_date__gte=latest_entry_date_time-timedelta(days=10)).order_by('st_id','rf_date')
        # queryset=RainfallObservations.objects.filter(rf_date__gte=today-timedelta(days=4)).order_by('st_id','rf_date')

        rainfall=[]
        stationIDs=[]
        dates=[]
        basinOrder=[]

        rainfallDict={}

        for results in queryset:
            rainfallDict[results.st_id]=results.rainfall
            stationIDs.append(results.st_id)
            # print(results.rf_date.strftime("%d-%m-%Y"))
            dates.append(results.rf_date.strftime("%d-%m-%Y"))
            rainfall.append(results.rainfall)
           

        results = defaultdict(list)
        # print({'results':queryset.values()})
        # for i, j in zip(stationIDs,rainfall):
        #     results[i].append(j)

        for i, j,k  in zip(stationIDs, dates,rainfall):
            results[i].append({j:k})

        # queryDict=zip(stationIDs,rainfall)
        return JsonResponse(results,safe=False)


# Three Days Observed Rainfall for Morning Bulletin
class threeDaysObservedRainfalForMorningBulltetinlViewSet(viewsets.ModelViewSet):

    # serializer_class = threeDaysObservedRainfallSerializer

    def list(self, request, *args, **kwargs):

        entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        entryDateTime = entryDateTime.replace(hour=6)
        print('In three days observed rainfall for morning bulltein: ', entryDateTime)

        queryset=RainfallObservations.objects.filter(rf_date__gte=entryDateTime-timedelta(days=2)).order_by('st_id','rf_date')

        rainfall=[]
        stationIDs=[]
        dates=[]
        basinOrder=[]

        rainfallDict={}

        for results in queryset:
            rainfallDict[results.st_id]=results.rainfall
            stationIDs.append(results.st_id)
            dates.append(results.rf_date.strftime("%d-%m-%Y"))
            rainfall.append(results.rainfall)

        results = defaultdict(dict)
        for i, j,k  in zip(stationIDs, dates,rainfall):results[i][j]=k


        # stationDetailsQueryset = data_load_models.FfwcRainfallStations.objects.all()
        # for stationResults in stationDetailsQueryset:
        #     results[stationResults.id]['station']=results[stationResults.name]
        #     results[stationResults.id]['station']=results[stationResults.name]


        return JsonResponse(results,safe=False)

@api_view()
#     """
#     This function retrieves transboundary river data from a database based on a specified station code
#     and end date.
    
#     :param request: The code snippet you provided is a Django view function that retrieves transboundary
#     river data from a database based on the station code provided as a URL parameter. It fetches the
#     latest record from the database, extracts the date from that record, and then filters the database
#     records based on the station code and the
#     :return: The code snippet provided is a Django view function that retrieves the latest record from
#     the IndianWaterLevelObservations database table, prints the last date from the database, and then
#     filters the records based on the station code and end date before serializing the data and returning
#     it as a response.
#     """
def transboundary_river_data_from_database(request,**kwargs):

    latest_record = data_load_models.IndianWaterLevelObservations.objects.latest('data_time')
    latest_record = latest_record.data_time - timedelta(days=15)
    # print('Last Date-Time Date from Database: ', latest_record.data_time - timedelta(days=1))
    # print('Last Date String from Database: ', latest_record.data_time.strftime('%Y-%m-%d'))
    print('Last Date String from Database: ', latest_record.strftime('%Y-%m-%d'))

    # latest_record_sting = latest_record.data_time.strftime('%Y-%m-%d')
    latest_record_sting = latest_record.strftime('%Y-%m-%d')

    station_code=kwargs['st_code']
    # end_date =str(kwargs['end_date'])+f'T00:00:00.000'
    end_date= latest_record_sting +f'T00:00:00.000'

    # end_date =str(kwargs['end_date'])+f'T{hourNow}:00:00.000'

    # IndianWaterLevelObservations

    queryset = data_load_models.IndianWaterLevelObservations.objects.filter(
    station_code=station_code,
    data_time__gte=end_date
    ).order_by('data_time') 

    serializer = serializers.indianStationWaterlevelSerializer(queryset,many=True)
    return Response(serializer.data)


    # data_json = {'Hello ': ' You'}
    # return Response(data_json)

@api_view()
def transboundary_river_data_timely(request,**kwargs):

    dateToday = datetime.now()+timedelta(hours=6)
    hourNow = dateToday.strftime("%H")
    # hourNow = dateToday.hour
    # printing current hour using hour
    # class
    print("Current hour ", hourNow)

    station_code=kwargs['st_code']
    start_date=str(kwargs['start_date'])+'T00:00:00.000'
    end_date =str(kwargs['end_date'])+f'T{hourNow}:00:00.000'

    print('Transboundary River End Date: ', end_date)

    # apiURL=f'https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria=%7B%22sortOrderDtos%22:%5B%7B%22sortDirection%22:%22ASC%22,%22field%22:%22id.dataTime%22%7D%5D%7D&specification=%7B%22where%22:%7B%22where%22:%7B%22where%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.stationCode%22,%22operator%22:%22eq%22,%22value%22:%22 \
    # {station_code}%22%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.datatypeCode%22,%22operator%22:%22eq%22,%22value%22:%22HHS%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22dataValue%22,%22operator%22:%22null%22,%22value%22:%22false%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.dataTime%22,%22operator%22:%22btn%22,%22value%22:%22\
    # {start_date},{end_date}%22%7D%7D%7D'

    
    # url= "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria={"sortOrderDtos":[{"sortDirection":"ASC","field":"id.dataTime"}]}&specification={"where":{"where":{"where":{"expression":{"valueIsRelationField":false,"fieldName":"id.stationCode","operator":"eq","value":"023-LBDJPG"}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"id.datatypeCode","operator":"eq","value":"HHS"}}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"dataValue","operator":"null","value":"false"}}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"id.dataTime","operator":"btn","value":"2023-12-07T14:28:18.215,2023-12-10T14:28:18.215"}}}"


    baseUrl = 'https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria='
    

    sortCriteria = quote('{"sortOrderDtos"')+':'+quote('[{"sortDirection"')+':'+quote('"ASC"')+','+ quote('"field"')+':'+quote('"id.dataTime"}]}')
    # {"sortOrderDtos":[{"sortDirection":"ASC","field":"id.dataTime"}]}
    # specification={"where":{"where":{"where":{"expression":{"valueIsRelationField":"false","fieldName":"id.stationCode","operator":"eq","value":"023-LBDJPG"}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"id.datatypeCode","operator":"eq","value":"HHS"}}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"dataValue","operator":"null","value":"false"}}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"id.dataTime","operator":"btn","value":"2023-12-07T14:28:18.215,2023-12-10T14:28:18.215"}}}
    
    specification=quote('{"where"')+':'+quote('{"where"')+ ':'+quote('{"where"')+':'+quote('{"expression"')+':'+quote('{"valueIsRelationField"')+':'+ \
    quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.stationCode"')+','+quote('"operator"')+':'+quote('"eq"')+','+quote('"value"')+\
    ':'+quote('"')+station_code+quote('"}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+quote('{"valueIsRelationField"')+':'+\
    quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.datatypeCode"')+','+quote('"operator"')+':'+quote('"eq"')+','+\
    quote('"value"')+':'+quote('"HHS"}}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+ quote('{"valueIsRelationField"')+\
    ':'+quote('"false"')+','+quote('"fieldName"')+':'+quote('"dataValue"')+','+quote('"operator"')+':'+quote('"null"')+','+\
    quote('"value"')+':'+quote('"false"}}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+\
    quote('{"valueIsRelationField"')+':'+quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.dataTime"')+','+quote('"operator"')+\
    ':'+quote('"btn"')+','+quote('"value"')+':'+quote('"')+f'{end_date},{start_date}'+quote('"}}}')

    # url = f'{baseUrl}{sortCriteria}{specification}'
    # url = baseUrl+urllib.parse.quote(str(sortCriteria),safe='')+urllib.parse.quote(str(specification),safe='')

    url = baseUrl+sortCriteria+'&specification='+specification

    # print('Indian Station URL: ', url)

    response = urlopen(url)
    data_json = json.loads(response.read()) 

    valueDict={}
    dataDict={}
    dataDate=datetime.fromisoformat(data_json[0]['id']['dataTime']).date()
    # dataKeys=list(data_json[0].keys())
    # print(dataKeys)

    for dataDicts in data_json[:len(data_json)-1]:
        dt_object = datetime.fromisoformat(dataDicts['id']['dataTime'])
        hour = dt_object.hour
        valueDict[hour]=dataDicts['dataValue']
        # print(dataDict['id']['dataTime'])
        # print(dataDict['dataValue'])
    # urlEncode= urllib.parse.urlencode(url)
    # dataDict['date']=datetime.strftime(dataDate,"%Y-%m-%d")
    dataDict[datetime.strftime(dataDate,"%Y-%m-%d")]=valueDict
    # print(dataDict)
    # print(valueDict)
    return Response(dataDict)

    # return Response({"url":urlEncode})

    # return Response({"message": "Hello, world!"})


@api_view()
def transboundary_river_data(request,**kwargs):

    dateToday = datetime.now()+timedelta(hours=6)
    hourNow = dateToday.strftime("%H")
    # hourNow = dateToday.hour
    # printing current hour using hour
    # class
    print("Current hour ", hourNow)

    station_code=kwargs['st_code']
    start_date=str(kwargs['start_date'])+'T00:00:00.000'
    end_date =str(kwargs['end_date'])+f'T{hourNow}:00:00.000'

    print('Transboundary River End Date: ', end_date)

    # apiURL=f'https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria=%7B%22sortOrderDtos%22:%5B%7B%22sortDirection%22:%22ASC%22,%22field%22:%22id.dataTime%22%7D%5D%7D&specification=%7B%22where%22:%7B%22where%22:%7B%22where%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.stationCode%22,%22operator%22:%22eq%22,%22value%22:%22 \
    # {station_code}%22%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.datatypeCode%22,%22operator%22:%22eq%22,%22value%22:%22HHS%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22dataValue%22,%22operator%22:%22null%22,%22value%22:%22false%22%7D%7D%7D,%22and%22:%7B%22expression%22:%7B%22valueIsRelationField%22:false,%22fieldName%22:%22id.dataTime%22,%22operator%22:%22btn%22,%22value%22:%22\
    # {start_date},{end_date}%22%7D%7D%7D'

    
    # url= "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria={"sortOrderDtos":[{"sortDirection":"ASC","field":"id.dataTime"}]}&specification={"where":{"where":{"where":{"expression":{"valueIsRelationField":false,"fieldName":"id.stationCode","operator":"eq","value":"023-LBDJPG"}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"id.datatypeCode","operator":"eq","value":"HHS"}}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"dataValue","operator":"null","value":"false"}}},"and":{"expression":{"valueIsRelationField":false,"fieldName":"id.dataTime","operator":"btn","value":"2023-12-07T14:28:18.215,2023-12-10T14:28:18.215"}}}"


    baseUrl = 'https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria='
    

    sortCriteria = quote('{"sortOrderDtos"')+':'+quote('[{"sortDirection"')+':'+quote('"ASC"')+','+ quote('"field"')+':'+quote('"id.dataTime"}]}')
    # {"sortOrderDtos":[{"sortDirection":"ASC","field":"id.dataTime"}]}
    # specification={"where":{"where":{"where":{"expression":{"valueIsRelationField":"false","fieldName":"id.stationCode","operator":"eq","value":"023-LBDJPG"}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"id.datatypeCode","operator":"eq","value":"HHS"}}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"dataValue","operator":"null","value":"false"}}},"and":{"expression":{"valueIsRelationField":"false","fieldName":"id.dataTime","operator":"btn","value":"2023-12-07T14:28:18.215,2023-12-10T14:28:18.215"}}}
    
    specification=quote('{"where"')+':'+quote('{"where"')+ ':'+quote('{"where"')+':'+quote('{"expression"')+':'+quote('{"valueIsRelationField"')+':'+ \
    quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.stationCode"')+','+quote('"operator"')+':'+quote('"eq"')+','+quote('"value"')+\
    ':'+quote('"')+station_code+quote('"}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+quote('{"valueIsRelationField"')+':'+\
    quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.datatypeCode"')+','+quote('"operator"')+':'+quote('"eq"')+','+\
    quote('"value"')+':'+quote('"HHS"}}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+ quote('{"valueIsRelationField"')+\
    ':'+quote('"false"')+','+quote('"fieldName"')+':'+quote('"dataValue"')+','+quote('"operator"')+':'+quote('"null"')+','+\
    quote('"value"')+':'+quote('"false"}}}')+','+quote('"and"')+':'+quote('{"expression"')+':'+\
    quote('{"valueIsRelationField"')+':'+quote('"false"')+','+quote('"fieldName"')+':'+quote('"id.dataTime"')+','+quote('"operator"')+\
    ':'+quote('"btn"')+','+quote('"value"')+':'+quote('"')+f'{end_date},{start_date}'+quote('"}}}')

    # url = f'{baseUrl}{sortCriteria}{specification}'
    # url = baseUrl+urllib.parse.quote(str(sortCriteria),safe='')+urllib.parse.quote(str(specification),safe='')

    url = baseUrl+sortCriteria+'&specification='+specification

    print('Indian Station URL: ', url)

    response = urlopen(url)
    data_json = json.loads(response.read()) 

    # urlEncode= urllib.parse.urlencode(url)

    return Response(data_json)

    # return Response({"url":urlEncode})

    # return Response({"message": "Hello, world!"})

@api_view()
def transboundary_river_onClick_data(request,**kwargs):

    station_code=kwargs['st_code']
    baseUrl = 'https://ffs.india-water.gov.in/iam/api/layer-station/'
    url=baseUrl+station_code


    response = urlopen(url)
    data_json = json.loads(response.read()) 

    return Response(data_json)


class feedbackViewSet(viewsets.ModelViewSet):

    queryset = Feedback.objects.all()
    serializer_class = feedbackSerializer


# @api_view(['POST'])
@api_view()
def create_feedback(request,**kwargs):
    
    name=kwargs['name']
    email=kwargs['email']
    comments=kwargs['comments']

    feedback = Feedback(name=name, email=email,comments=comments)
    feedback.save()

    return HttpResponse("Data successfully inserted!")

@api_view()
def feedback(request):

    name = request.query_params.get('name')
    email = request.query_params.get('email')
    comments = request.query_params.get('comments')

    feedback = Feedback(name=name, email=email,comments=comments)
    feedback.save()

    # return HttpResponse("Data successfully inserted!")

    return Response({"Print": "name = {}, email={}, comments={}".format(name,email,comments)})


class userViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = userSerializer
    
    permission_classes = (AllowAny, )

    def get_queryset(self):                                            # added string
        return super().get_queryset().filter(id=self.request.user.id)



# User Profile View
@api_view()
def profile(request):
    current_user=request.user
    user_id = current_user.id
    users=User.objects.all().values_list('username',flat=True)

    return Response(users)

    # all_result = super(ProfileAdmin, self).get_queryset(request)

    # if request.user.is_superuser: return all_result
    # else:
    #     user_id = request.user.id
    #     return all_result.filter(user_id=user_id)


# Indian Station ViewSet

class indainStationViewSet(viewsets.ModelViewSet):

    queryset = IndianStations.objects.all()
    serializer_class = indianStationSerializer

    def stationById(self,request,**kwargs):
        station_id=self.kwargs['station_id']
        queryset=IndianStations.objects.filter(id=station_id, status=1)
        serializer = indianStationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def stationByName(self,request,**kwargs):
        station_name=self.kwargs['station_name']
        queryset=IndianStations.objects.filter(name=station_name)
        serializer = indianStationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def stationByCode(self,request,**kwargs):
        station_code=self.kwargs['station_code']
        queryset=IndianStations.objects.filter(station_code=station_code)
        serializer = indianStationSerializer(queryset, many=True)
        return Response(serializer.data)

indian_station_by_id=indainStationViewSet.as_view({'get':'stationById'})
indian_station_by_name=indainStationViewSet.as_view({'get':'stationByName'})
indian_station_by_code=indainStationViewSet.as_view({'get':'stationByCode'})


class UpdateUserProfileAPIView(generics.CreateAPIView):
  permission_classes = (AllowAny,)
  serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer


class UserprofilestationsViewSet(viewsets.ModelViewSet):

    queryset = data_load_models.DataLoadProfileUserprofilestations.objects.all()
    serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer

    # def list(self, request, *args, **kwargs):
    #     mydata = FfwcLastUpdateDate.objects.values_list('last_update_date')
    #     return Response(mydata[0])

class UserFfwcStationsList(generics.ListCreateAPIView):
    serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer

    def get_queryset(self):
        queryset = data_load_models.DataLoadProfileUserprofilestations.objects.all()
        profile_id = self.request.query_params.get('profile_id')
        if profile_id is not None:
            queryset = queryset.filter(profile_id=profile_id)
        return queryset

class UserFfwcStationsDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer
    queryset = data_load_models.DataLoadProfileUserprofilestations.objects.all()


class DeleteUserFfwcStationsDetails(generics.DestroyAPIView):

    queryset = data_load_models.DataLoadProfileUserprofilestations.objects.all()
    serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer

# Insert BD Stations by user
class InsertUserStationView(generics.CreateAPIView):
  permission_classes = (AllowAny,)
  serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer

# Insert Indian Stations by user
class InsertUserIndianStationView(generics.CreateAPIView):
  permission_classes = (AllowAny,)
  serializer_class = serializers.DataLoadProfileUserprofileIndianStationsSerializer

# Delete FFWC Stations from User Profile
@api_view(['DELETE'])
def deleteProfileStationsByUserId(request,pk):

    id=int(pk)
    try:
        instance = data_load_models.DataLoadProfileUserprofilestations.objects.get(id=id)
        instance.delete()
        return Response({'Status':'Deleted'})
    except instance.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

# Delete Indian Stations from User Profile
@api_view(['DELETE'])
def deleteProfileIndianStationsByUserId(request,pk):

    id=int(pk)
    try:
        instance = data_load_models.DataLoadProfileUserprofileindianstations.objects.get(id=id)
        instance.delete()
        return Response({'Status':'Deleted'})
    except instance.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def DeleteProfileID(request,**kwargs):

    profile_id = kwargs['profile_id']
    station_id = kwargs['station_id']

    queryset= data_load_models.DataLoadProfileUserprofilestations.objects\
    .filter(profile_id=profile_id)\
    .filter(ffwcstations2023_id=station_id)\
    .values()[0]

    # context={"id":queryset}

    return Response(queryset["id"])


@api_view(['GET'])
def DeleteIndianProfileID(request,**kwargs):

    profile_id = kwargs['profile_id']
    station_id = kwargs['station_id']

    queryset= data_load_models.DataLoadProfileUserprofileindianstations.objects\
    .filter(profile_id=profile_id)\
    .filter(indianstations_id=station_id)\
    .values()[0]

    # context={"id":queryset}

    return Response(queryset["id"])

# class UpdateViewSet(viewsets.ModelViewSet):
#       queryset = data_load_models.DataLoadProfileUserprofilestations.objects.all()
#       serializer_class = serializers.DataLoadProfileUserprofilestationsSerializer

#       def get_object(self):
#           if self.request.method == 'PUT':
#               obj, created = data_load_models.DataLoadProfileUserprofilestations.objects.get_or_create(pk=self.kwargs.get('id'))
#               return obj
#           else:
#               return super(UpdateViewSet, self).get_object()



# API View for Flash Flood Forecast
def generateDownloadFileNameList(downloadYear):
    
    fileNameList=[]
    
    dayOfTheYear=datetime.now().timetuple().tm_yday
    today=datetime.now()
    todayDateString=today.strftime("%Y-%m-%d")
    print('Date Today: ', todayDateString, 'Day of the Year: ', dayOfTheYear)

    for i in range(1,11):
        
        downloadDay=dayOfTheYear-i
        numberOfDigits = int(math.log10(downloadDay))+1
        if numberOfDigits==2:downloadDay = str(downloadDay).rjust(3, '0')
        else: downloadDay = str(downloadDay)
        dowanloadFileName=str(downloadYear)+downloadDay+'.nc'

        fileNameList.append(dowanloadFileName)
    
    return fileNameList

def computeDailyBasinWiseMeanPrecipitation(fileName,stationName,dailyPrecipitationDict):

    dir_path = os.getcwd()
    basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
    stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")
    
    # print('Station CRS: ', stationGDF.crs)
    # print('Station GDF: ', stationGDF.geometry)

    
    observed_file_path=os.path.join(dir_path,f"observed/{fileName}")
    dataset=xr.open_dataset(observed_file_path)

    dataset.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    dataset.rio.write_crs("epsg:4326", inplace=True)
    basinClipped = dataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)

    observedDate=basinClipped.indexes['time'][0].strftime('%Y-%m-%d')

    # print('Observed Date: ', observedDate)

    # # meanPrecipitation=basinClipped['precipitation'].mean().values.tolist()

    weights = np.cos(np.deg2rad(basinClipped.lat))
    weights.name = "weights"
    rainfall_weighted = basinClipped.weighted(weights)
    weighted_mean = rainfall_weighted.mean(("lon", "lat"))
    meanPrecipitation=weighted_mean['precipitation'].values.tolist()[0]

    dailyPrecipitationDict[observedDate]=meanPrecipitation
    # print('Mean Precipitation For: ', observedDate,'Is :', meanPrecipitation ,'(mm)')

    return dailyPrecipitationDict

def generateObservedDataframe(dailyPrecipitationDict):


    dateList=list(dailyPrecipitationDict.keys())
    rainfallList=list(dailyPrecipitationDict.values())
    dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
    observedRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
    observedRainfallDF.sort_values(by='Date',inplace=True)
    observedRainfallDF.reset_index(drop=True,inplace=True)

    return observedRainfallDF

def computeBasinWiseForecast(stationName,givenDate):

    dir_path = os.getcwd()

    basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
    stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")



    print('Given Forecast Date: ', givenDate, 'For station: ', stationName)

    dateString = givenDate[8:10]+givenDate[5:7]+givenDate[:4]

    fileName=dateString+'.nc'

    if stationName !='cambodia':
        forecast_file_path = os.path.join(dir_path,f'forecast/{fileName}')
    elif stationName =='cambodia':
        print('In cambodia Forecast ....')
        forecast_file_path = os.path.join(dir_path,f'cambodiaForecast/{fileName}')


    fileExist = os.path.isfile(forecast_file_path)

    if fileExist: 
        print('File Exists : ', fileExist)
        pass
    else:
        print('Forecast File Does Not Exist ')
        previousDate = datetime.strptime(givenDate,'%Y-%m-%d') 
        previousDate = previousDate - timedelta(days=1)
        previousDate = datetime.strftime(previousDate,'%Y-%m-%d')

        dateString = previousDate[8:10]+previousDate[5:7]+previousDate[:4]

        fileName=dateString+'.nc'

        if stationName !='cambodia':
            forecast_file_path = os.path.join(dir_path,f'forecast/{fileName}')
        elif stationName =='cambodia':
            print('In cambodia Forecast ....')
            forecast_file_path = os.path.join(dir_path,f'cambodiaForecast/{fileName}')

        # forecast_file_path = os.path.join(dir_path,f'forecast/{fileName}')

        print('Previous Date: ', forecast_file_path)

    print('Forecast File Path: ', forecast_file_path)
    forecastDataset=xr.open_dataset(forecast_file_path)

    print('Forecast Dataset File Path: ', forecast_file_path)
    # print(forecastDataset)

    forecastDataset.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
    forecastDataset.rio.write_crs("epsg:4326", inplace=True)
    clippedForecast = forecastDataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)

    # print(clippedForecast)



    dateList=list(clippedForecast.indexes['time'].strftime('%Y-%m-%d %H:%M:%S'))
    # dateList=list(dailyForecast.indexes['time'].strftime('%Y-%m-%d'))

    forecastPrecipitationDict={}
    dateIndex=0

    for day in range(0,len(dateList),4):
        totalPrecipitation=0
        # thisDay=dateList[dateIndex]
        thisDay=dateList[day]

        # print(thisDay)
        oneDayData=clippedForecast.sel(time=thisDay)
        # oneDayData=clippedForecast.sel(time=thisDay[:11])

        weights = np.cos(np.deg2rad(oneDayData.latitude))
        weights.name = "weights"
        rainfall_weighted = oneDayData.weighted(weights)
        weighted_mean = oneDayData.mean(("longitude", "latitude"))
        
        meancpValue=weighted_mean['cp'].values.tolist()
        meanlspValue=weighted_mean['lsp'].values.tolist()

        # totalPrecipitation= np.nansum(meancpValue)+np.nansum(meanlspValue)

        totalPrecipitation= meancpValue+meanlspValue
        if math.isnan(totalPrecipitation):totalPrecipitation=0.00

        forecastPrecipitationDict[dateList[dateIndex]]=totalPrecipitation*1000
        dateIndex=dateIndex+4

    rainfallValues=list(forecastPrecipitationDict.values())
    dateValues=list(forecastPrecipitationDict.keys())
    dateValues=[date[:-9] for date in dateValues]

    dailyRainfallValue=[]
    for i in range(8):
        rainfallAmount=round((rainfallValues[i+1]-rainfallValues[i]),4)
        dailyRainfallValue.append(rainfallAmount)

    forecastPrecipitationDict=dict(zip(dateValues,dailyRainfallValue))

    return forecastPrecipitationDict

def generateForecastDataframe(forecastPrecipitationDict):

    dateList=list(forecastPrecipitationDict.keys())
    rainfallList=list(forecastPrecipitationDict.values())
    dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
    forecastRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
    forecastRainfallDF.sort_values(by='Date',inplace=True)
    forecastRainfallDF.reset_index(drop=True,inplace=True)

    return forecastRainfallDF

def returnDesiredDataframe(observedRainfallDF,forecastRainfallDF):
    requiredDF=pd.concat([observedRainfallDF,forecastRainfallDF])
    requiredDF.reset_index(drop=True,inplace=True)

    return requiredDF

def returnRainfallRecords(stationName,givenDate):

    fileNameList = generateDownloadFileNameList(2025)
    # print(fileNameList)

    dailyPrecipitationDict={}
    for fileName in fileNameList:
        try:
            dailyPrecipitationDict= computeDailyBasinWiseMeanPrecipitation(fileName,stationName,dailyPrecipitationDict)
        except:
            print(f'Observed File {fileName} Does Not Exist')


    observedRainfallDF=generateObservedDataframe(dailyPrecipitationDict)

    print('Observed Rainfall DF')
    print(observedRainfallDF)

    forecastPrecipitationDict=computeBasinWiseForecast(stationName,givenDate)
    forecastRainfallDF = generateForecastDataframe(forecastPrecipitationDict)

    print('Forecast Rainfall DF')
    print(forecastRainfallDF)

    rainfallRecords = returnDesiredDataframe(observedRainfallDF,forecastRainfallDF)
    # rainfallRecords=[]
    return rainfallRecords

def processDateTimeDictRainfall(givenDate,rainfallRecords,indexedHourThresholdDict):

    # print(rainfallRecords)

    rangeStart = rainfallRecords.iloc[0]['Date']
    rangeStart = datetime.strptime(rangeStart,'%Y-%m-%d')
    rangeEnd = rainfallRecords.iloc[len(rainfallRecords)-1]['Date']
    rangeEnd=datetime.strptime(rangeEnd,'%Y-%m-%d')

    print('Range Start: ', rangeStart , ' Range End: ',rangeEnd)

    dictRainfall=rainfallRecords.to_dict()
    # dictRainfall.keys()
    timeList=list(dictRainfall['Date'].values())
    rainfallList=list(dictRainfall['Rainfall'].values())
    dictRainfall={}
    for i,j in zip(timeList,rainfallList):
        # dateString=datetime.strftime(i,'%Y-%m-%d')
        # print(i)
        dictRainfall[i]=j


    indexedHourThresholdDict={0:[24,25], 1:[48,40.5], 2:[72,53.5], 3:[120,76], 4:[168,96], 5:[240,123]}
    intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Threshold'])
    givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
    
    noOfDayWithinRange=(rangeEnd-givenDateInDateTime).days
    print('No. of Days in range: ', noOfDayWithinRange)

    dateTimeRangeFromGivenDateTime=[givenDateInDateTime+timedelta(days=day) for day in range (0,noOfDayWithinRange+1)]

    return intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall

def returnCumulativeRainfall(givenDateInDateTime,hourThresholdDict,hourList,rangeStart,dictRainfall):
    
    # givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
    totalRainfall= []

    for hour in hourList:
        thresholdOfThatHour=hourThresholdDict[hour]
        noOfDays=int(hour/24)
        cumulativeRainfallList=[]

        for day in range(noOfDays):
            calculatingDate= givenDateInDateTime-timedelta(days=day)
            if (calculatingDate>rangeStart):
                # print('Calculating Date: ', calculatingDate)
                calculatingDateString=datetime.strftime(calculatingDate,'%Y-%m-%d')
                rainfallOnThatDay= dictRainfall[calculatingDateString]
                cumulativeRainfallList.append(rainfallOnThatDay)
            else : continue
        # print('----------------------------------------------------------------------')
        sumOfRainfallIntensity=sum(cumulativeRainfallList)
        totalRainfall.append(round(sumOfRainfallIntensity,2))

    return totalRainfall


@api_view(['GET'])
def PredictFlood(request,**kwargs):

    from tensorflow import keras
    import numpy as np
    from keras.losses import MeanSquaredError
    mse = MeanSquaredError()
    
    month = kwargs['month']
    day = kwargs['day']
    hour = kwargs['hour']
    diff1 = kwargs['diff1']
    diff2 = kwargs['diff2']
    diff3 = kwargs['diff3']
    diff4 = kwargs['diff4']

        # Retrieving Threshold Dict   
    dir_path = os.getcwd()
    model_path=os.path.join(dir_path,'trainedModels/noonkhawa_lstm_model.h5')
    loaded_model = keras.models.load_model(model_path,custom_objects={'mse': mse})

    predict_this=np.array([[month, day,hour, diff1, diff2, diff3, diff4]])
    predicted_value = loaded_model.predict(predict_this)
    # print(predicted_value)

    jsonResult ={'input':[month,day,hour,diff1,diff2,diff3,diff4],'waterlevel':predicted_value}
    return Response(jsonResult)


@api_view(['GET'])
def NewFlashFlood(request,**kwargs):

    forecast_date = kwargs['forecast_date']
    basin_id = kwargs['basin_id']

    latest_record = data_load_models.Basin_Wise_Flash_Flood_Forecast.objects.latest('prediction_date')
    latest_date = latest_record.prediction_date  # Access the date field

    first_query =  data_load_models.Basin_Wise_Flash_Flood_Forecast.objects.filter(prediction_date=forecast_date, basin_id=basin_id)
    
    if not first_query.exists():
        forecast_date = latest_date
        second_query =  data_load_models.Basin_Wise_Flash_Flood_Forecast.objects.filter(prediction_date=forecast_date, basin_id=basin_id)
        forecasts = second_query
    else:
        forecasts = first_query


    # Initialize the response structure
    response_data = {

        "Hours": {
            "0": 24,
            "1": 48,
            "2": 72,
            "3": 120,
            "4": 168,
            "5": 240
        },

        "Threshold": defaultdict(float),
    }

    threshold_list=[]

    date_value_dict = defaultdict(list)
    # Populate the response data with values from the database
    for forecast in forecasts:
        threshold_list.append(forecast.thresholds)
        date_value_dict[forecast.date].append(forecast.value)
 
    # Convert defaultdict to regular dict
    threshold_dict={}
    for i,threshold in enumerate(sorted(set(threshold_list))):threshold_dict[str(i)]=threshold
    response_data["Threshold"] = threshold_dict
  
    for key in date_value_dict.keys():
        string_date = key.strftime("%Y-%m-%d")
        response_data[string_date] = {str(i): value for i, value in enumerate(date_value_dict[key])}

    return Response(response_data)

@api_view(['GET'])
def FlashFlood(request,**kwargs):

    # stationThresholds = {
    #     1:{24: 51.45, 48: 77.5, 72: 98.3, 120: 133, 168: 162, 240: 200},
    #     2:{24: 24.5, 48: 41.5, 72: 56.5, 120: 83, 168: 107.5, 240: 141},
    #     3:{24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123},
    #     4:{24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123},
    #     5:{24: 34, 48: 46.3, 72: 55.4, 120: 69.37, 168: 80.5, 240: 94},
    # }


    # stationThresholdsList = {
    #         1: {0:[24,51.45], 1:[48,77.5], 2:[72,98.3], 3:[120,133], 4:[168,162], 5:[240,200]},
    #         2: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
    #         3: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
    #         4: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
    #         5: {0:[24,34], 1:[48,46.3], 2:[72,55.4], 3:[120,69.37], 4:[168,80.5], 5:[240,94]}
    # }


    forecast_date = kwargs['forecast_date']
    basin_id = kwargs['basin_id']

    print('Basin Id : ', basin_id)
    stationDict={ 
        1:'khaliajhuri', 
        2:'gowainghat', 
        3:'dharmapasha',
        4:'userbasin',
        5:'laurergarh',
        6:'muslimpur',
        
        7:'debidwar',
        8:'ballah',
        9:'habiganj',
        10:'parshuram',
        11:'cumilla'
        }


    # Retrieving Threshold Dict   
    dir_path = os.getcwd()
    station_threshold_path=os.path.join(dir_path,'floodForecastStations/stationThresholds.txt')

    with open(station_threshold_path) as f: 
        data = f.read() 

    stationThresholdsText = ast.literal_eval(data) 

    newStationThresholdsText = {}
    for key,value in stationThresholdsText.items():
        newDict = {int(innerKey):innerValue for innerKey,innerValue in stationThresholdsText[key].items()}
        newStationThresholdsText[int(key)]=newDict

    # print('Station Threshold Dict {}')
    # print(newStationThresholdsText)
    stationThresholds = newStationThresholdsText


    # Retrieving Threshold List   
    # Retrieving Threshold List    

    dir_path = os.getcwd()
    station_threshold_list_path=os.path.join(dir_path,'floodForecastStations/stationThresholdsList.txt')

    with open(station_threshold_list_path) as f: 
        data = f.read() 
        # print(data)

    stationThresholdsListText = ast.literal_eval(data) 
    # print('Station Threshold List []: ')
    # print(stationThresholdsListText)

    newStationThresholdsListTextDict = {}

    for key,value in stationThresholdsListText.items():
        # newStationThresholdsListText[int(key)]=stationThresholdsListText[key]
        # print(int(key),stationThresholdsListText[key])
        innerDict={}
        for innerKey,innerValue in stationThresholdsListText[key].items():
            # print(int(key),int(innerKey),[int(value) if isinstance(value,str) else value for value in innerValue ])
            innerDict[int(innerKey)]=[int(value) if isinstance(value,str) else value for value in innerValue ]
        # print(innerDict)
        newStationThresholdsListTextDict[int(key)]=innerDict
            # newStationThresholdsListText[int(key)]={int(innerKey):[int(value) if isinstance(value,str) else value for value in innerValue ]}
        # newDict = {int(innerKey):innerValue for innerKey,innerValue in stationThresholdsText[key].items()}
        # print('New Dict: ',  newDict)
        # newStationThresholdsListText[int(key)]=newDict

    # print(newStationThresholdsListTextDict)

    stationThresholdsList = newStationThresholdsListTextDict
    # Main Computatin for Basin Wise Flash Flood 
    givenDate = forecast_date
    stationName=stationDict[basin_id]
    hourThresholdDict=stationThresholds[basin_id]
    indexedHourThresholdDict=stationThresholdsList[basin_id]

    print('Station Name: ', stationName)

    rainfallRecords=returnRainfallRecords(stationName,givenDate)
    print('Rainfall Records: ')
    print(rainfallRecords)

    intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall = processDateTimeDictRainfall(givenDate,rainfallRecords,indexedHourThresholdDict)
    
    # print('Intensity Threshold DataFrame: ', intensityThresholdDataframe)
    # hourThresholdDict={24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123}
    hourList=[24, 48, 72, 120, 168, 240]

    print('Date Time Range: ', dateTimeRangeFromGivenDateTime)

    for dateTime in dateTimeRangeFromGivenDateTime:

        print(dateTime)
        totalRainfall=returnCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
        dateString=datetime.strftime(dateTime,'%Y-%m-%d')
        intensityThresholdDataframe[dateString]=totalRainfall

    # print(intensityThresholdDataframe)
    jsonResult=intensityThresholdDataframe.to_dict()

    # jsonResult={}

    return Response(jsonResult)

@api_view(['GET'])
def CambodiaFlashFlood(request,**kwargs):

    forecast_date = kwargs['forecast_date']
    basin_id = kwargs['basin_id']

    print('Basin Id : ', basin_id)
    stationDict={ 
        1:'cambodia', 
        5:'cambodia', 
        10:'cambodia', 
        }


    # Retrieving Threshold Dict   
    dir_path = os.getcwd()
    station_threshold_path=os.path.join(dir_path,'floodForecastStations/cambodiaStationThresholds.txt')

    with open(station_threshold_path) as f: 
        data = f.read() 

    stationThresholdsText = ast.literal_eval(data) 

    newStationThresholdsText = {}
    for key,value in stationThresholdsText.items():
        newDict = {int(innerKey):innerValue for innerKey,innerValue in stationThresholdsText[key].items()}
        newStationThresholdsText[int(key)]=newDict

    print('Station Threshold Dict {}')
    print(newStationThresholdsText)
    stationThresholds = newStationThresholdsText


    # Retrieving Threshold List   
    # Retrieving Threshold List    

    dir_path = os.getcwd()
    station_threshold_list_path=os.path.join(dir_path,'floodForecastStations/cambodiaStationThresholdsList.txt')

    with open(station_threshold_list_path) as f: 
        data = f.read() 
        # print(data)

    stationThresholdsListText = ast.literal_eval(data) 
    print('Station Threshold List []: ')
    # print(stationThresholdsListText)

    newStationThresholdsListTextDict = {}

    for key,value in stationThresholdsListText.items():
        # newStationThresholdsListText[int(key)]=stationThresholdsListText[key]
        # print(int(key),stationThresholdsListText[key])
        innerDict={}
        for innerKey,innerValue in stationThresholdsListText[key].items():
            # print(int(key),int(innerKey),[int(value) if isinstance(value,str) else value for value in innerValue ])
            innerDict[int(innerKey)]=[int(value) if isinstance(value,str) else value for value in innerValue ]
        # print(innerDict)
        newStationThresholdsListTextDict[int(key)]=innerDict
            # newStationThresholdsListText[int(key)]={int(innerKey):[int(value) if isinstance(value,str) else value for value in innerValue ]}
        # newDict = {int(innerKey):innerValue for innerKey,innerValue in stationThresholdsText[key].items()}
        # print('New Dict: ',  newDict)
        # newStationThresholdsListText[int(key)]=newDict

    print(newStationThresholdsListTextDict)

    stationThresholdsList = newStationThresholdsListTextDict
    # Main Computatin for Basin Wise Flash Flood 
    givenDate = forecast_date
    stationName=stationDict[basin_id]
    hourThresholdDict=stationThresholds[basin_id]
    indexedHourThresholdDict=stationThresholdsList[basin_id]

    print('Station Name: ', stationName)

    rainfallRecords=returnRainfallRecords(stationName,givenDate)
    intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall = processDateTimeDictRainfall(givenDate,rainfallRecords,indexedHourThresholdDict)
    # print(intensityThresholdDataframe)
    # hourThresholdDict={24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123}
    hourList=[24, 48, 72, 120, 168, 240]

    for dateTime in dateTimeRangeFromGivenDateTime:

        totalRainfall=returnCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
        dateString=datetime.strftime(dateTime,'%Y-%m-%d')
        intensityThresholdDataframe[dateString]=totalRainfall

    # print(intensityThresholdDataframe)
    jsonResult=intensityThresholdDataframe.to_dict()

    # jsonResult={}

    return Response(jsonResult)


# Functions Required for Probabilistc Flash Flood Forecast
# Cambodia Probabilistic 
# API View for Probabilistic Flash Flood Forecast
def returnCambodiaRequired(basin_id=1):
    
    stationDict={ 
    1:'cambodia'
    }

    hourList=[24, 48, 72, 120, 168, 240]
    
    stationThresholdsList = {
        1: {0:[24,25.00], 1:[48,40.00], 2:[72,53.00], 3:[120,76.00], 4:[168,96.00], 5:[240,123.00]},
    }
    


  



    stationThresholds = {
        1:{24: 25.00, 48: 40.00, 72: 53.00, 120: 76.00, 168: 96.00, 240: 123.00},

    }
    

    
    stationName=stationDict[basin_id]
    hourThresholdDict=stationThresholds[basin_id]
    indexedHourThresholdDict=stationThresholdsList[basin_id]
    
    
    dir_path = os.getcwd()
    basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
    stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")

    print('Station GDF: ', stationGDF)

    # stationGDF=gpd.read_file(f'floodForecastStations/{stationName}.json',crs="epsg:4326")

    return hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF

# API View for Probabilistic Flash Flood Forecast
def returnRequired(basin_id=1):
    
    stationDict={ 
    1:'khaliajhuri', 
    2:'gowainghat', 
    3:'dharmapasha',
    4:'userbasin',
    5:'laurergarh',
    6:'muslimpur',

    7:'debidwar',
    8:'ballah',
    9:'habiganj',
    10:'parshuram',
    11:'cumilla'
    }

    hourList=[24, 48, 72, 120, 168, 240]
    
    stationThresholdsList = {
        1: {0:[24,51.45], 1:[48,77.5], 2:[72,98.3], 3:[120,133], 4:[168,162], 5:[240,200]},
        2: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
        3: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
        4: {0:[24,25], 1:[48,40.5], 2:[72,53.5], 3:[120,76], 4:[168,96], 5:[240,123]},
        5: {0:[24,34], 1:[48,46.3], 2:[72,55.4], 3:[120,69.37], 4:[168,80.5], 5:[240,94]},
        6: {0:[24,33.50], 1:[48,51.84], 2:[72,66.93], 3:[120,92.34], 4:[168,114.14], 5:[240,142.90]},

        7: {0:[24,17], 1:[48,27], 2:[72,36], 3:[120,49], 4:[168,61], 5:[240,77]},
        8: {0:[24,9], 1:[48,14], 2:[72,17], 3:[120,23], 4:[168,28], 5:[240,34]},
        9: {0:[24,10], 1:[48,17], 2:[72,23], 3:[120,33], 4:[168,42], 5:[240,55]},
        10: {0:[24,17], 1:[48,26], 2:[72,33], 3:[120,45], 4:[168,55], 5:[240,69]},
        11: {0:[24,16], 1:[48,30], 2:[72,42], 3:[120,66], 4:[168,89], 5:[240,121]},

    }
    

#   // 7:{24: 17, 48: 27, 72: 36, 120: 49, 168: 61, 240: 77},
#   // 8:{24: 9, 48: 14, 72: 17, 120: 23, 168: 28, 240: 34},

#   // 9:{24: 10, 48: 17, 72: 23, 120: 33, 168: 42, 240: 55},
#   // 10:{24: 17, 48: 26, 72: 33, 120: 45, 168: 55, 240: 69},
#   // 11:{24: 16, 48: 30, 72: 42, 120: 66, 168: 89, 240: 121},
  



    stationThresholds = {
        1:{24: 51.45, 48: 77.5, 72: 98.3, 120: 133, 168: 162, 240: 200},
        2:{24: 24.5, 48: 41.5, 72: 56.5, 120: 83, 168: 107.5, 240: 141},
        3:{24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123},
        4:{24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123},
        5:{24: 34, 48: 46.3, 72: 55.4, 120: 69.37, 168: 80.5, 240: 94},
        6:{24: 33.50, 48: 51.84, 72: 66.93, 120: 92.34, 168: 114.14, 240: 142.90},

        7:{24: 17, 48: 27, 72: 36, 120: 49, 168: 61, 240: 77},
        8:{24: 9, 48: 14, 72: 17, 120: 23, 168: 28, 240: 34},
        9:{24: 10, 48: 17, 72: 23, 120: 33, 168: 42, 240: 55},
        10:{24: 17, 48: 26, 72: 33, 120: 45, 168: 55, 240: 69},
        11:{24: 16, 48: 30, 72: 42, 120: 66, 168: 89, 240: 121},
    }
    

    
    stationName=stationDict[basin_id]
    hourThresholdDict=stationThresholds[basin_id]
    indexedHourThresholdDict=stationThresholdsList[basin_id]
    
    
    dir_path = os.getcwd()
    basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
    stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")

    print('Station GDF: ', stationGDF)

    # stationGDF=gpd.read_file(f'floodForecastStations/{stationName}.json',crs="epsg:4326")

    return hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF

def generateObservedFileNameList(downloadYear):
    
    today = datetime.now()
    dayOfTheYear = int(today.strftime('%j'))-1
    pastTenDaysOfTheYear = dayOfTheYear-10

    # print('Day of the Year: ', int(dayOfTheYear), 'Minus Ten: ',int(dayOfTheYear)-10 )

    fileNameList=[]
    dayOfTheYearList=[i for i in range(dayOfTheYear,pastTenDaysOfTheYear,-1)]
    print()
    dayOfTheYearList.reverse()

    for day in dayOfTheYearList:
        dowanloadFileName=str(downloadYear)+str(day).rjust(3, '0')+'.nc'
        fileNameList.append(dowanloadFileName)
    
    return fileNameList


def computeDailyProbabilisticMeanPrecipitation(stationGDF,fileName,dailyPrecipitationDict={}):

    dir_path = os.getcwd()
    observed_file_path=os.path.join(dir_path,f"observed/{fileName}")
    dataset=xr.open_dataset(observed_file_path)

    # dataset=xr.open_dataset(f"probabilisticObserved/{fileName}")

    dataset.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    dataset.rio.write_crs("epsg:4326", inplace=True)
    basinClipped = dataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)
    observedDate=basinClipped.indexes['time'][0].strftime('%Y-%m-%d')
    
    weights = np.cos(np.deg2rad(basinClipped.lat))
    weights.name = "weights"
    rainfall_weighted = basinClipped.weighted(weights)
    weighted_mean = rainfall_weighted.mean(("lon", "lat"))
    meanPrecipitation=weighted_mean['precipitation'].values.tolist()[0]
    dailyPrecipitationDict[observedDate]=meanPrecipitation

    return dailyPrecipitationDict


def probabilisticObservedDataframe(dailyPrecipitationDict):

    dateList=list(dailyPrecipitationDict.keys())
    rainfallList=list(dailyPrecipitationDict.values())
    dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
    observedRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
    observedRainfallDF.sort_values(by='Date',inplace=True)
    observedRainfallDF.reset_index(drop=True,inplace=True)

    return observedRainfallDF


def genObservedDataFrame(stationGDF):
    
    observedFileNameList = generateObservedFileNameList(2025)
    
    for fileName in observedFileNameList:
        print('Observed File Name List: ', fileName)
        try:
            dailyPrecipitationDict=computeDailyProbabilisticMeanPrecipitation(stationGDF,fileName)
        except:
            print(f'File {fileName} Does Not Exist')
            
    observedRainfallDF = probabilisticObservedDataframe(dailyPrecipitationDict)

    return observedRainfallDF


def returnModelFilenames(givenDate):

    print('Given Date: ', givenDate)
    print('Given Year: ', givenDate[:4], 'Given Month: ', givenDate[5:7],'Given Day: ',givenDate[8:])
    
    filenameList=[]
    # year,month,day=datetime.now().year,datetime.now().month,datetime.now().day
    # year,month,day=2024,3,31

    year,month,day=int(givenDate[:4]),int(givenDate[5:7]),int(givenDate[8:])
    
    if((int(math.log10(month))+1) == 2): month = str(month)
    elif(int(math.log10(month))+1) != 2 :  month = str(month).rjust(2, '0')
    if ((int(math.log10(day))+1) == 2): day= str(day)
    elif ((int(math.log10(day))+1) != 2): day = str(day).rjust(2, '0') 
    
    dateString=str(year)+month+day
    folderName= dateString
    
    for modelNumber in range(0,51):
        modelNumber=str(modelNumber).rjust(2, '0')
        fileName='R1E.'+dateString+'.en_'+modelNumber+'.nc'
        filenameList.append(fileName)
        
    return filenameList,folderName



def computeProbabilisticForecast(stationGDF,folderName,fileName,forecastPrecipitationDict={}):

    dir_path = os.getcwd()

    try:
        forecast_file_path = os.path.join(dir_path,f"{folderName}/{fileName}")
        forecastDataset=xr.open_dataset(forecast_file_path)
    except FileNotFoundError:
        fileNamelength=len(fileName)
        date_int=fileName[4:fileNamelength-9]
        date_str = str(date_int)
        date_object = datetime.strptime(date_str, '%Y%m%d')-timedelta(days=1)
        date_string = date_object.strftime('%Y%m%d')
        folderName = date_string
        fileName = fileName[0:4]+date_string+fileName[fileNamelength-9:]
        print('Chaning File Name (Error Occured): ', fileName)

        forecast_file_path = os.path.join(dir_path,f"{folderName}/{fileName}")
        forecastDataset=xr.open_dataset(forecast_file_path)
    except Exception as e:
        # Handle any other exceptions that may occur
        print(f"An error occurred: {e}")





    forecastDataset.rio.write_crs("epsg:4326", inplace=True)
    clippedForecast = forecastDataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)
    dateList=list(clippedForecast.indexes['time'].strftime('%Y-%m-%d %H:%M:%S'))

    dateIndex=0
    for index in range(0,len(dateList),4):
        
        thisDay=dateList[index]
        oneDayData=clippedForecast.sel(time=thisDay)
    
        weights = np.cos(np.deg2rad(oneDayData.latitude))
        weights.name = "weights"
        rainfall_weighted = oneDayData.weighted(weights)
        weighted_mean = oneDayData.mean(("longitude", "latitude"))
        
        meancpValue=weighted_mean['cp'].values
        meanlspValue=weighted_mean['lsp'].values
    
        if math.isnan(meancpValue):meancpValue=0.00
        if math.isnan(meanlspValue):meanlspValue=0.00
        totalPrecipitation= meancpValue+meanlspValue
    
        forecastPrecipitationDict[dateList[dateIndex]]=round(totalPrecipitation*1000,2)
        dateIndex=dateIndex+4
    
        rainfallValues=list(forecastPrecipitationDict.values())
        dateValues=list(forecastPrecipitationDict.keys())
        
        dateValues=[date[:-9] for date in dateValues]
        
        dailyRainfallValue=[]
    
    for i in range(len(dateValues)-7):
        rainfallAmount=round((rainfallValues[i+1]-rainfallValues[i]),4)
        dailyRainfallValue.append(rainfallAmount)
    
    forecastPrecipitationDict=dict(zip(dateValues,dailyRainfallValue))

    return forecastPrecipitationDict
    


def probabilisticForecastDataframe(forecastPrecipitationDict):

    dateList=list(forecastPrecipitationDict.keys())
    rainfallList=list(forecastPrecipitationDict.values())
    dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
    forecastRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
    forecastRainfallDF.sort_values(by='Date',inplace=True)
    forecastRainfallDF.reset_index(drop=True,inplace=True)

    return forecastRainfallDF

def probabilisticDesiredDataframe(observedRainfallDF,forecastRainfallDF):
    
    requiredDF=pd.concat([observedRainfallDF,forecastRainfallDF])
    requiredDF.reset_index(drop=True,inplace=True)

    return requiredDF



def returnRequiredDateTime(rainfallRecords,givenDate):
    
    rangeStart = rainfallRecords.iloc[0]['Date']
    rangeStart = datetime.strptime(rangeStart,'%Y-%m-%d')
    rangeEnd = rainfallRecords.iloc[len(rainfallRecords)-1]['Date']

    print(rainfallRecords)

    rangeEnd=datetime.strptime(rangeEnd,'%Y-%m-%d')
    # rangeEnd = rangeEnd - timedelta(days=5)
    print('Range end in Probabilistic: ', rangeEnd)

    dictRainfall=rainfallRecords.to_dict()
    dictRainfall.keys()
    timeList=list(dictRainfall['Date'].values())
    rainfallList=list(dictRainfall['Rainfall'].values())
    dictRainfall={}
    for i,j in zip(timeList,rainfallList):
        dictRainfall[i]=j
    
    givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
    noOfDayWithinRange=(rangeEnd-givenDateInDateTime).days
    dateTimeRangeFromGivenDateTime=[givenDateInDateTime+timedelta(days=day) for day in range (0,noOfDayWithinRange+1)]

    return rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime


def probabilisticCumulativeRainfall(givenDateInDateTime,hourThresholdDict,hourList,rangeStart,dictRainfall):

    # print('Printing Dict Rainfall : ')
    # print(dictRainfall)
    
    totalRainfall= []

    for hour in hourList:

        thresholdOfThatHour=hourThresholdDict[hour]
        noOfDays=int(hour/24)
        cumulativeRainfallList=[]

        for day in range(noOfDays):

            calculatingDate= givenDateInDateTime-timedelta(days=day)
            if (calculatingDate>rangeStart):
                calculatingDateString=datetime.strftime(calculatingDate,'%Y-%m-%d')
                rainfallOnThatDay= dictRainfall[calculatingDateString]
                cumulativeRainfallList.append(rainfallOnThatDay)
            else : continue
        # print('----------------------------------------------------------------------')
        sumOfRainfallIntensity=sum(cumulativeRainfallList)
        totalRainfall.append(round(sumOfRainfallIntensity,2))
    
    return totalRainfall



@api_view(['GET'])
def ProbabilisticFlashFlood(request,**kwargs):

    givenDate = kwargs['givenDate']
    basin_id = kwargs['basin_id']

    allModelDataFrameList=[]

    hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF=returnRequired(basin_id)



    observedRainfallDF = genObservedDataFrame(stationGDF)

    modelFilenameList,folderName = returnModelFilenames(givenDate)
    model_no=0

    for fileName in modelFilenameList:

        print('Ensamble Model File Name: ', fileName)

        forecastPrecipitationDict= computeProbabilisticForecast(stationGDF,folderName,fileName)
        forecastRainfallDF = probabilisticForecastDataframe(forecastPrecipitationDict)
        rainfallRecords = probabilisticDesiredDataframe(observedRainfallDF,forecastRainfallDF)

        rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime = returnRequiredDateTime(rainfallRecords,givenDate)
        intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Threshold'])
        

        print('Date Time Range in Probabilistic: ')
        print(dateTimeRangeFromGivenDateTime)


        modelCountDF=pd.DataFrame()
        for dateTime in dateTimeRangeFromGivenDateTime:
            dateString=datetime.strftime(dateTime,'%Y-%m-%d')
            totalRainfall=probabilisticCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
            intensityThresholdDataframe[dateString]=totalRainfall
            # print(intensityThresholdDataframe)


            # Computing Frequency of Count based on threshold
            frequencyRecord=(intensityThresholdDataframe[dateString]>(intensityThresholdDataframe['Threshold']))
            modelCountDF[dateString]=frequencyRecord
            # print(modelCountDF)

            lastIndex=len(hourList)
            frequencyCountDF = modelCountDF.T
            frequencyCountDF.columns=hourList
            noOfRows = len(frequencyCountDF)
            frequencyCountDF.insert(lastIndex,'ens_model',[model_no]*noOfRows,True)

            # print(frequencyCountDF)

        model_no+=1
        allModelDataFrameList.append(frequencyCountDF)

    length = len(allModelDataFrameList)
    print('All Model DataFrame List ',length)
    print(allModelDataFrameList)


    dateWiseProbabilityDistributionDictt={}
    hourlyDistributionList=[]

    print('Date Time Range Later: ', dateTimeRangeFromGivenDateTime)

    for dateTime in dateTimeRangeFromGivenDateTime[:-1]:
        dateString=datetime.strftime(dateTime,'%Y-%m-%d')
        frameIndex=[]
        for modelIndex in range(len(allModelDataFrameList)-1):
            frameIndex.append(allModelDataFrameList[modelIndex].loc[[dateString]])
            mergedFrequencyDistribution=pd.concat(frameIndex)
            hourlyDistributionList=list(mergedFrequencyDistribution.sum().values)
            percentageList=[round(i/51*100,2) for i in hourlyDistributionList[:-1]]
            dateWiseProbabilityDistributionDictt[dateString]=percentageList
            # print({dateString:[round(i/51,2)*100 for i in hourlyDistributionList[:-1]]})
            # print(allModelDataFrameList[modelIndex].loc[[dateString]])

    probabilityDataframe=pd.DataFrame(dateWiseProbabilityDistributionDictt)
    probabilityDataframe.insert(0,'Hours',hourList,True)
    thresholds=list(hourThresholdDict.values())
    probabilityDataframe.insert(1,'Thresholds',thresholds,True)

    # print('The Cimplete Probability Dataframe: ')
    print(probabilityDataframe)
    jsonResult=probabilityDataframe.to_dict()

    # context = {'Given Date': givenDate, 'Basin Id':basin_id }
    return Response(jsonResult)



@api_view(['GET'])
def NewProbabilisticFlashFlood(request,**kwargs):

    forecast_date = kwargs['givenDate']
    basin_id = kwargs['basin_id']

    latest_record = data_load_models.Probabilistic_Flash_Flood_Forecast.objects.latest('prediction_date')
    latest_date = latest_record.prediction_date  # Access the date field

    first_query =  data_load_models.Probabilistic_Flash_Flood_Forecast.objects.filter(prediction_date=forecast_date, basin_id=basin_id)
    
    if not first_query.exists():
        forecast_date = latest_date
        second_query =  data_load_models.Probabilistic_Flash_Flood_Forecast.objects.filter(prediction_date=forecast_date, basin_id=basin_id)
        forecasts = second_query
    else:
        forecasts = first_query


    # Initialize the response structure
    response_data = {

        "Hours": {
            "0": 24,
            "1": 48,
            "2": 72,
            "3": 120,
            "4": 168,
            "5": 240
        },

        "Thresholds": defaultdict(float),
    }

    threshold_list=[]

    date_value_dict = defaultdict(list)
    # Populate the response data with values from the database
    for forecast in forecasts:
        threshold_list.append(forecast.thresholds)
        date_value_dict[forecast.date].append(forecast.value)
 
    # Convert defaultdict to regular dict
    threshold_dict={}
    for i,threshold in enumerate(sorted(set(threshold_list))):threshold_dict[str(i)]=threshold
    response_data["Thresholds"] = threshold_dict
  
    for key in date_value_dict.keys():
        string_date = key.strftime("%Y-%m-%d")
        response_data[string_date] = {str(i): value for i, value in enumerate(date_value_dict[key])}

    return Response(response_data)
# Cambodia Probabilistic 
@api_view(['GET'])
def CambodiaProbabilisticFlashFlood(request,**kwargs):

    givenDate = kwargs['givenDate']
    basin_id = kwargs['basin_id']

    allModelDataFrameList=[]

    hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF=returnCambodiaRequired(basin_id)



    observedRainfallDF = genObservedDataFrame(stationGDF)

    modelFilenameList,folderName = returnModelFilenames(givenDate)
    model_no=0

    for fileName in modelFilenameList:

        print('Ensamble Model File Name: ', fileName)

        forecastPrecipitationDict= computeProbabilisticForecast(stationGDF,folderName,fileName)
        forecastRainfallDF = probabilisticForecastDataframe(forecastPrecipitationDict)
        rainfallRecords = probabilisticDesiredDataframe(observedRainfallDF,forecastRainfallDF)

        rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime = returnRequiredDateTime(rainfallRecords,givenDate)
        intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Threshold'])
        

        modelCountDF=pd.DataFrame()
        for dateTime in dateTimeRangeFromGivenDateTime:
            dateString=datetime.strftime(dateTime,'%Y-%m-%d')
            totalRainfall=probabilisticCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
            intensityThresholdDataframe[dateString]=totalRainfall
            # print(intensityThresholdDataframe)


            # Computing Frequency of Count based on threshold
            frequencyRecord=(intensityThresholdDataframe[dateString]>(intensityThresholdDataframe['Threshold']))
            modelCountDF[dateString]=frequencyRecord
            # print(modelCountDF)

            lastIndex=len(hourList)
            frequencyCountDF = modelCountDF.T
            frequencyCountDF.columns=hourList
            noOfRows = len(frequencyCountDF)
            frequencyCountDF.insert(lastIndex,'ens_model',[model_no]*noOfRows,True)

            # print(frequencyCountDF)

        model_no+=1
        allModelDataFrameList.append(frequencyCountDF)


    dateWiseProbabilityDistributionDictt={}
    hourlyDistributionList=[]
    for dateTime in dateTimeRangeFromGivenDateTime:
        dateString=datetime.strftime(dateTime,'%Y-%m-%d')
        frameIndex=[]
        for modelIndex in range(len(allModelDataFrameList)):
            frameIndex.append(allModelDataFrameList[modelIndex].loc[[dateString]])
            mergedFrequencyDistribution=pd.concat(frameIndex)
            hourlyDistributionList=list(mergedFrequencyDistribution.sum().values)
            percentageList=[round(i/51*100,2) for i in hourlyDistributionList[:-1]]
            dateWiseProbabilityDistributionDictt[dateString]=percentageList
            # print({dateString:[round(i/51,2)*100 for i in hourlyDistributionList[:-1]]})
            # print(allModelDataFrameList[modelIndex].loc[[dateString]])

    probabilityDataframe=pd.DataFrame(dateWiseProbabilityDistributionDictt)
    probabilityDataframe.insert(0,'Hours',hourList,True)
    thresholds=list(hourThresholdDict.values())
    probabilityDataframe.insert(1,'Thresholds',thresholds,True)

    print(probabilityDataframe)
    jsonResult=probabilityDataframe.to_dict()

    # context = {'Given Date': givenDate, 'Basin Id':basin_id }
    return Response(jsonResult)



# UPDTE BASIN  THRESHOLD


@api_view(['GET'])
def updateBasinThreshold(request,hourThresholdDict):

    jsonResult = ast.literal_eval(hourThresholdDict) 

    basinId= list(jsonResult.keys())[0]
    # basinId = int(basinId)
    # print(basinId)

    # Reading the threshold text File
    dir_path = os.getcwd()
    station_threshold_path=os.path.join(dir_path,'floodForecastStations/stationThresholds.txt')

    with open(station_threshold_path) as f: 
        data = f.read() 

    d = ast.literal_eval(data) 
    # print('Before: ' , d)

    # return {int(k): v for k, v in pairs}
    jsonResult[basinId]={int(k): v for k, v in jsonResult[basinId].items()}
    # print(jsonResult[basinId])
    d[basinId]=jsonResult[basinId]

    
    # print(d[basinId])
    # print('After: ',d )
    # print(d)

    fname = 'floodForecastStations/stationThresholds.txt'
    with open(fname, 'w') as f:
        f.write(json.dumps(d))
        print('File Written . .')

    # jsonResult={'threshold':hourThresholdDict}
    # jsonResult = {'basinID':basinId}
    return Response(jsonResult[basinId])



@api_view(['GET'])
def updateBasinThresholdList(request,hourThresholdDictList):


    jsonResult = ast.literal_eval(hourThresholdDictList) 
    basinId= list(jsonResult.keys())[0]

    print('Basin Id: ', basinId)

    dir_path = os.getcwd()
    station_threshold_path=os.path.join(dir_path,'floodForecastStations/stationThresholdsList.txt')

    with open(station_threshold_path) as f: 
        data = f.read() 

    d = ast.literal_eval(data) 

    # print('Before: ' , d[basinId])
    jsonResult[basinId]={int(k): v for k, v in jsonResult[basinId].items()}

    # print('Before: ' , d)

    d[basinId]=jsonResult[basinId]

    
    # print(d[basinId])

    # print('After: ',d )
    # # print(d)

    fname = 'floodForecastStations/stationThresholdsList.txt'
    with open(fname, 'w') as f:
        f.write(json.dumps(d))
        print('File Written . .')

    # jsonResult={'threshold':hourThresholdDict}
    # jsonResult = {'basinID':basinId}
    return Response(jsonResult)

# def writeUserDefinedJson():

#     dir_path = os.getcwd()
#     basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
#     stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")

@api_view(['GET'])
def UserDefinedBasin(request,lat,lng):
    # from geopy.distance import distance

    # print('In User Defined Basin')

    # # coordinates = []
    # reference_point = (lat, lng)
    # nearest_point = None
    # min_distance = float('inf')

    # dir_path = os.getcwd()
    # river_points=os.path.join(dir_path,'assets/river-points.json')

    # with open(river_points, 'r') as file:
    #     coordinates = json.load(file)

    # for point_coords in coordinates:
    #     dist = distance(reference_point, point_coords).miles  # You can also use .km for kilometers
    #     print(dist)

    #     if dist < min_distance:
    #         min_distance = dist
    #         nearest_point = point_coords

    # print('Nearest Point: ', nearest_point)

    # for feature in feature_collection['features']:
        
    #     if(feature['geometry'] is not None):
    #         geom = feature['geometry']
    #         if geom['type'] in ['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']:
    #             coords = geom['coordinates']
    #             coordinates.extend(coords)

    # print(coordinates)
        # if geom['type'] == 'Point':
        #     coordinates.append(geom['coordinates'])
        # elif geom['type'] == 'MultiPoint':
        #     coordinates.extend(geom['coordinates'])
        # elif geom['type'] in ['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']:
        #     # For LineString and Polygon, you might want to extract all points
        #     coords = geom['coordinates']
        #     if geom['type'] == 'Polygon':
        #         # For polygons, coordinates are nested
        #         for ring in coords:
        #             coordinates.extend(ring)
        #     else:
        #         coordinates.extend(coords)

        # for geometry in feature:
        #     print(geometry['coordinates'])

    # print(data['features']['geometry'])

    # # reading the data from the file 
    # with open(station_threshold_path) as f: 
    #     data = f.read() 

    # d = ast.literal_eval(data) 
    # print(d)


    lat = float(lat)
    lng = float(lng)

    # lat = float(nearest_point[0])
    # lng = float(nearest_point[1])

    # nearest_point

    # # Request the Watershed via the API
    url = "https://mghydro.com/app/watershed_api?lat={}&lng={}&precision=high".format(lat, lng)
    print(url)
    r = requests.get(url=url)

    if r.status_code == 400 or r.status_code == 404:
        jsonResult = r.text

    if r.status_code == 500:
        jsonResult= {'error': "Server error. Please contact the developer."}

    # Status code of 200 means everything was OK!
    if r.status_code == 200: 
        jsonResult = r.json()  
    #     fname = 'floodForecastStations/userbasin.json'
    #     with open(fname, 'w') as f:
    #         f.write(r.text)
    #         print('File Written . .')

    # jsonResult= {'lat':lat,'lng':lng}
    return Response(jsonResult)



@api_view(['GET'])
def FlowPath(request,lat,lng):

    print('In Flow Path API')

    lat = float(lat)
    lng = float(lng)

    # # Request the Watershed via the API
    url = "https://mghydro.com/app/flowpath_api?lat={}&lng={}&precision=high".format(lat, lng)
    r = requests.get(url=url)

    if r.status_code == 400 or r.status_code == 404:
        jsonResult = r.text

    if r.status_code == 500:
        jsonResult= {'error': "Server error. Please contact the developer."}

    # Status code of 200 means everything was OK!
    if r.status_code == 200: 
        jsonResult = r.json()  
        fname = 'floodForecastStations/userbasin.json'
        with open(fname, 'w') as f:
            f.write(r.text)
            print('File Written . .')

    # jsonResult= {'lat':lat,'lng':lng}
    return Response(jsonResult)


# Sub Bain Wise Precipitation

@api_view(['GET'])
def SubBasinPrecipiation(request,lat,lng):

    print('In Basin Wise Precipitation')

    dir_path = os.getcwd()
    station_threshold_path=os.path.join(dir_path,'floodForecastStations/stationThresholdsList.txt')

    # reading the data from the file 
    with open(station_threshold_path) as f: 
        data = f.read() 

    d = ast.literal_eval(data) 
    
    # print(d)


    lat = float(lat)
    lng = float(lng)

    jsonResult= {'lat':lat,'lng':lng}

    jsonResult = d[1]
    return Response(jsonResult)



    # Changes By SHAIF

    

    # Experimental Forecast Waterlevel Viewset

class experimentalForecastWaterlevelViewSet(viewsets.ModelViewSet):

    entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
    
    databaseUpdateDate = data_load_models.FfwcLastUpdateDateExperimental.objects.values_list('last_update_date')[0]

    dateInput=datetime.strftime(databaseUpdateDate[0],'%Y-%m-%d')
    hourInput='T00'
    forecastDateString=dateInput+hourInput+':00:00Z'
    forecastDate=datetime.strptime(forecastDateString,"%Y-%m-%dT%H:%M:%SZ")
    

    # print('In Experimental View: ', forecastDate)


    # queryset = WaterLevelForecasts.objects.filter(fc_date__gte=date.today()-timedelta(days=0))
    queryset = WaterLevelForecastsExperimentals.objects.filter(fc_date__gte=forecastDate)
    serializer_class = experimentalForecastWaterlevelSerializer

    def mediumRangeForecastWaterlevelByStation(self,request,**kwargs):
        
        stationId=self.kwargs['st_id']

        if (WaterLevelForecastsExperimentals.objects.filter(st_id=stationId)).exists():
            print('Station Forecast Exists : ', stationId)
        else:
            print('Station Forecasts Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        databaseUpdateDate = data_load_models.FfwcLastUpdateDateExperimental.objects.values_list('last_update_date')[0]

        dateInput=datetime.strftime(databaseUpdateDate[0],'%Y-%m-%d')
        hourInput='T00'
        forecastDateString=dateInput+hourInput+':00:00Z'
        forecastDate=datetime.strptime(forecastDateString,"%Y-%m-%dT%H:%M:%SZ")

        queryset = WaterLevelForecastsExperimentals.objects.filter(st_id=stationId,fc_date__gte=forecastDate)
        
        serializer= experimentalForecastWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)
    

    def sevenDaysobservedWaterlevelForMediumRangeForecastByStation(self,request,**kwargs):
        
        experimentalUpdateDateTime = datetime.strptime(experimentalEntryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
        print('Observed For Medium Range Forecast in Work: ', experimentalUpdateDateTime)

        # print(experimental_entry_date_time)

        stationId=self.kwargs['st_id']

        if (WaterLevelObservations.objects.filter(st_id=stationId)).exists():
            print('Station Observed Exists : ', stationId)
        else:
            print('Station Observed Does Not Exists : ', stationId)
            return JsonResponse(None,safe=False)

        databaseUpdateDate = data_load_models.FfwcLastUpdateDateExperimental.objects.values_list('last_update_date')[0]
        
        print('Experimental Forecast Database Update Date: ',databaseUpdateDate )
        startDateForObserved = databaseUpdateDate[0] - timedelta(days=7)
        print('Observed Date for Experimental Forecast : ',startDateForObserved )



        dateInput=datetime.strftime(databaseUpdateDate[0],'%Y-%m-%d')
        forecastDateString=dateInput+' 06:00:00'
        print('Medium Range Forecast Date String: ', forecastDateString)

        forecastDate=datetime.strptime(forecastDateString,"%Y-%m-%d %H:%M:%S")
        
        # startObservedDate = datetime.strftime(forecastDate-timedelta(days=7),"%Y-%m-%d %H:%M:%S")
        # endObservedDate = datetime.strftime(forecastDate-timedelta(days=1),"%Y-%m-%d %H:%M:%S")

        # print('Medium Range Starting Observed Date: ', startObservedDate)
        # print('Medium Range Ending Observed Date: ', endObservedDate)


        start =  startDateForObserved
        # datetime.strptime('2023-06-24 00:00:00',"%Y-%m-%d %H:%M:%S")
        # end = datetime.strptime('2023-10-13 18:00:00',"%Y-%m-%d %H:%M:%S")
        end = forecastDate
        


        queryset = WaterLevelObservations.objects.filter(
            st_id=stationId,
            wl_date__range=[start,end]
            )

        serializer = observedWaterlevelSerializer(queryset,many=True)
        return Response(serializer.data)



medium_range_forecast_waterlevel_by_station=experimentalForecastWaterlevelViewSet.as_view({'get':'mediumRangeForecastWaterlevelByStation'})
observed_for_medium_range_forecast_waterlevel_by_station=experimentalForecastWaterlevelViewSet.as_view({'get':'sevenDaysobservedWaterlevelForMediumRangeForecastByStation'})
# sevenDaysobservedWaterlevelForMediumRangeForecastByStation



class stationInfoViewSet(viewsets.ModelViewSet):

    # print('Base Directory:  ', BASE_DIR)

    queryset = data_load_models.FfwcStationInfo.objects.all()
    # queryset = FfwcStations2023.objects.all()
    serializer_class = serializers.FfwcStationInfoSerializer