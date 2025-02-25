from rest_framework import serializers
from rest_framework.serializers import Serializer,FileField
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum,Avg,Max,Min

from data_load.models import FfwcLastUpdateDate,FfwcStations2023,WaterLevelForecasts,WaterLevelObservations,WaterLevelForecastsExperimentals
from data_load.models import FfwcRainfallStations,RainfallObservations,MonthlyRainfall
from data_load.models import DataHeader

from data_load.models import IndianStations,IndianWaterLevelObservations

from data_load.models import Feedback
from data_load.models import AuthUser

from data_load.models import RainfallObservations as ro

from datetime import date, datetime, timedelta

from data_load import models as data_load_models


def returnDate():

    entry_date_time = FfwcLastUpdateDate.objects.all().values_list('entry_date',flat=True)[0]
    entry_date = str(entry_date_time.date())
    entry_hour = str(entry_date_time.hour)

    hourIndexDict={
        '06':['06','07','08'],  '09':['09','10','11'], '12':['12','13','14'], '15':['15','16','17'],'18':['18','19','20','21','22','23']
    }

    for key in hourIndexDict.keys():
        if entry_hour in hourIndexDict[key]:
            entry_hour='T'+key

    entryDateTimeString=entry_date+entry_hour+':00:00Z'

    # print('Entry Date time String in Serializer: ', entryDateTimeString)

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



    return dateInput,hourInput,observedDate,forecastDate,lastForecastUpdateDateTime,entryDateTimeString

#Calling Function to return Date Today
dateInput,hourInput,observedDate,forecastDate,lastForecastUpdateDateTime,entryDateTimeString=returnDate()

class lastUpdateDateSerializer(serializers.ModelSerializer):

    class Meta:
        model=FfwcLastUpdateDate
        fields=['last_update_date']


class lastExperimentalUpdateDateSerializer(serializers.ModelSerializer):

    class Meta:
        model=data_load_models.FfwcLastUpdateDateExperimental
        fields=['last_update_date']


# FfwcLastUpdateDateExperimental
class stationSerializer(serializers.ModelSerializer):


    # waterlevel=serializers.SerializerMethodField()

    # query= WaterLevelObservations.objects.latest('wl_date')
    # wl_date = query.wl_date


    # def get_waterlevel(self,FfwcStations2023):
        
    #     waterlevel=0

    #     if (WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id)).exists():
    #         query= WaterLevelObservations.objects.latest('wl_date')
    #         self.wl_date = query.wl_date
    #         # waterlevel=WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).order_by('-wl_date').values_list('waterlevel',flat=True)[0]
    #         print(waterlevel)
    #     else:
    #         pass 
    #         print('Does Not Exist')
    #     return self.wl_date 

    class Meta:
        model=FfwcStations2023
        fields=['id','coords','name','river','basin_order','basin','dangerlevel','riverhighestwaterlevel','avglandlevel','river_chainage',
        'division','district','upazilla','union','long','order_up_down','lat','forecast_observation','status','station_order',
        'medium_range_station','unit_id','jason_2_satellie_station']


class indianStationSerializer(serializers.ModelSerializer):
    class Meta:
        model=IndianStations
        fields=['id','station_name','state_name','district','basin_name','river_name','latitude','longitude','division_name',
        'type_of_site','distance','within_ganges','within_brahmaputra','within_meghna','station_code',
        'dangerlevel','warning_level','highest_flow_level']

class indianStationWaterlevelSerializer(serializers.ModelSerializer):
    class Meta:
        model=IndianWaterLevelObservations
        fields=['station_id','station_code','data_time','waterlevel']


# class StationObservedCombinedSerializer(serializers.ModelSerializer):

#     waterlevel=serializers.SerializerMethodField()

#     entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
#     # print('Entry Date Time in Combined Serializer : ', entryDateTime)
#     queryset = WaterLevelObservations.objects.values('waterlevel').filter(wl_date=entryDateTime).order_by('st_id','wl_date')




#     def get_waterlevel(self,FfwcStations2023):


#         entryDateTime = datetime.strptime(entryDateTimeString,"%Y-%m-%dT%H:%M:%SZ")
#         waterlevel =  ''

#         try:
#              q1 = WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).latest('waterlevel')
#              waterlevel = q1.waterlevel
#         except:
#             waterlevel='na'

#         # if WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).exists():
#         #     q1 = WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).latest('waterlevel')
#         #     print(q1.waterlevel)
#         # else :
#         #     q1='na'
        
#         # # q1 = WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).latest('waterlevel')
#         # q1 = WaterLevelObservations.objects.filter(st_id=FfwcStations2023.id).annotate(recent_date=Max('wl_date')
#         # ).order_by('-wl_date').values('wl_date','waterlevel')[0]

#         # queryset = WaterLevelObservations.objects.filter(
#         #     st_id=FfwcStations2023.id,
#         #     wl_date = entryDateTime
#         #     ).values('waterlevel').annotate(recent_date=Max('wl_date'))
#         # lastObservedWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d1)[0]



#         return waterlevel



#     class Meta:
#         model=FfwcStations2023
#         fields=['id','coords','name','river','basin_order','basin','dangerlevel','riverhighestwaterlevel','avglandlevel','river_chainage',
#         'division','district','upazilla','union','long','order_up_down','lat','forecast_observation','status','station_order',
#         'medium_range_station','unit_id','jason_2_satellie_station','waterlevel']
        
class observedWaterlevelSerializer(serializers.ModelSerializer):

    class Meta:
        model=WaterLevelObservations
        fields=[
            'st_id','name','lat','long',
            'river','basin_order','basin',
            'division','district','upazilla','union',
            'wl_date','waterlevel','dangerlevel','riverhighestwaterlevel'
            ]
    # waterlevel=serializers.SerializerMethodField()

    # query= WaterLevelObservations.objects.latest('wl_date')
    # wl_date = query.wl_date
    # print('Waterlevel Observed Date in Serializer: ', wl_date)
    # qs=WaterLevelObservations.objects.filter(wl_date=wl_date)[0]
    # print('Query :', qs.waterlevel)

    # def get_waterlevel(self):

    

    # print('In Observed Serializer ')

    name=serializers.SerializerMethodField()
    river=serializers.SerializerMethodField()
    basin_order=serializers.SerializerMethodField()
    basin=serializers.SerializerMethodField()

    lat=serializers.SerializerMethodField()
    long=serializers.SerializerMethodField()

    division=serializers.SerializerMethodField()
    district=serializers.SerializerMethodField()
    upazilla=serializers.SerializerMethodField()
    union=serializers.SerializerMethodField()


    dangerlevel=serializers.SerializerMethodField()
    riverhighestwaterlevel=serializers.SerializerMethodField()

    # foo = serializers.SerializerMethodField()

    # def get_foo(self,WaterLevelObservations):

    #     return ''

    # lastObserved =  serializers.SerializerMethodField()


    # d1 = databaseTime+timedelta(days=0,hours=0,minutes=0,seconds=0)
    # lastObservedWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d1)[0]
    # lastObservedWaterlevel= float(lastObservedWaterlevelQ.waterlevel)
    # print('Last Observed Waterlevel: ', lastObservedWaterlevel)

    # d2 = d1-timedelta(days=0,hours=3,minutes=0,seconds=0)
    # lastLastObservedWaterlevelQ= WaterLevelObservations.objects.filter(st_id=stationId,wl_date=d2)[0]
    # lastLastObservedWaterlevel= float(lastLastObservedWaterlevelQ.waterlevel)
    # print('Second to Last Observed Waterlevel: ', lastLastObservedWaterlevel)

    # def get_today(self,WaterLevelObservations):
    #     # getLastUpdateTime=WaterLevelObservations.objects.filter(id=WaterLevelObservations.st_id).order_by('-wl_date').values_list('wl_date',flat=True)[0]
    #     # print('Station Id: ', stationId, 'Last Update Time: ',getLastUpdateTime)
    #     today = date.today()
    #     return today

    # waterlevel1=serializers.SerializerMethodField()

    # def get_waterlevel1(self,WaterLevelObservations):
        
    #     waterlevel1 = WaterLevelObservations.objects.filter(wl_date=self.wl_date).values_list('waterlevel1', flat=True)[0]
    
    #     return waterlevel1


    def get_name(self,WaterLevelObservations):

        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            name = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('name', flat=True)[0]
            return name

    def get_lat(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            lat = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('lat', flat=True)[0]
            return lat

    def get_long(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            long = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('long', flat=True)[0]
            return long

    def get_river(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            river = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('river', flat=True)[0]
            return river
    
    def get_basin_order(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            basin_order = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('basin_order', flat=True)[0]
            return basin_order

    def get_basin(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            basin = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('basin', flat=True)[0]
            return basin

    def get_dangerlevel(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            dangerlevel = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('dangerlevel', flat=True)[0]
            return dangerlevel

    def get_riverhighestwaterlevel(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            riverhighestwaterlevel = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('riverhighestwaterlevel', flat=True)[0]
            return riverhighestwaterlevel

    def get_division(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            division = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('division', flat=True)[0]
            return division

    def get_district(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            district = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('district', flat=True)[0]
            return district


    def get_upazilla(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            upazilla = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('upazilla', flat=True)[0]
            return upazilla


    def get_union(self,WaterLevelObservations):
        if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
            union = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('union', flat=True)[0]
            return union


class forecastWaterlevelSerializer(serializers.ModelSerializer):

    id= serializers.SerializerMethodField()

    def get_id(self, WaterLevelForecasts):
        id = FfwcStations2023.objects.filter(id=WaterLevelForecasts.st_id).values_list('id', flat=True)[0]
        return id

    class Meta:
        model=WaterLevelForecasts
        fields=['id','st_id','fc_date','fc_id','waterlevel']


# class modifiedForecastWaterlevelSerializer(serializers.ModelSerializer):

#     names = serializers.SlugRelatedField(
#         many=True,slug_field = 'stationame', 
#         queryset=data_load_models.ForecastWithStationDetails.objects.filter(id=20)
#         )
    


    # id= serializers.SerializerMethodField()
    # name=serializers.SerializerMethodField()


    # def get_id(self, WaterLevelForecasts):
    #     id = FfwcStations2023.objects.filter(id=WaterLevelForecasts.st_id).values_list('id', flat=True)[0]
    #     return id

    # def get_name(self,WaterLevelObservations):

    #     if FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).exists():
    #         name = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('name', flat=True)[0]
    #         return name

    # class Meta:
    #     model=WaterLevelForecasts
    #     fields=['st_id','fc_date','waterlevel','names']

# Experimental Forecast Watelevel Serializer


class experimentalForecastWaterlevelSerializer(serializers.ModelSerializer):

    # id= serializers.SerializerMethodField()

    # def get_id(self, exper):
    #     id = FfwcStations2023.objects.filter(id=WaterLevelForecastsExperimentals.st_id).values_list('id', flat=True)[0]
    #     return id

    class Meta:
        model=WaterLevelForecastsExperimentals
        fields=['st_id','fc_date','fc_id','waterlevel_min','waterlevel_max','waterlevel_mean']


class rainfallStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FfwcRainfallStations
        fields='__all__'


class rainfallObservationSerializer(serializers.ModelSerializer):

    name=serializers.SerializerMethodField()
    basin_order=serializers.SerializerMethodField()
    basin=serializers.SerializerMethodField()
    normal_rainfall=serializers.SerializerMethodField()
    max_rainfall=serializers.SerializerMethodField()

    total_rainfall = serializers.IntegerField()

    def get_name(self,RainfallObservations):
        name = FfwcRainfallStations.objects.filter(id=RainfallObservations['st_id']).values_list('name', flat=True)[0]
        return name
    
    def get_basin_order(self,RainfallObservations):
        basin_order = FfwcRainfallStations.objects.filter(id=RainfallObservations['st_id']).values_list('basin_order', flat=True)[0]
        return basin_order

    def get_basin(self,RainfallObservations):
        basin = FfwcRainfallStations.objects.filter(id=RainfallObservations['st_id']).values_list('basin', flat=True)[0]
        return basin
    
    def get_normal_rainfall(self,RainfallObservations):
        today = datetime.today()
        month = today.month
        normal_rainfall = MonthlyRainfall.objects.filter(
            station_id=RainfallObservations['st_id'],month_serial=month).values_list('normal_rainfall', flat=True)
        return normal_rainfall

    def get_max_rainfall(self,RainfallObservations):
        today = datetime.today()
        month = today.month
        max_rainfall = MonthlyRainfall.objects.filter(
            station_id=RainfallObservations['st_id'],month_serial=month).values_list('max_rainfall', flat=True)
        return max_rainfall
    
    class Meta:
        model = RainfallObservations
        fields=['st_id','name','basin_order','basin','normal_rainfall','max_rainfall','total_rainfall']


class morningRainfallBulletinSerializer(serializers.ModelSerializer):

    name=serializers.SerializerMethodField()
    basin_order=serializers.SerializerMethodField()
    normal_rainfall=serializers.SerializerMethodField()

    total_rainfall = serializers.IntegerField()

    def get_name(self,RainfallObservations):
        name = FfwcRainfallStations.objects.filter(id=RainfallObservations['st_id']).values_list('name', flat=True)[0]
        return name
    
    def get_basin_order(self,RainfallObservations):
        basin_order = FfwcStations2023.objects.filter(id=RainfallObservations['st_id']).values_list('basin_order', flat=True)[0]
        return basin_order
    
    def get_normal_rainfall(self,RainfallObservations):
        today = datetime.today()
        month = today.month
        normal_rainfall = MonthlyRainfall.objects.filter(
            station_id=RainfallObservations['st_id'],month_serial=month).values_list('normal_rainfall', flat=True)
        return normal_rainfall
    
    class Meta:
        model = RainfallObservations
        fields=['st_id','name','basin_order','normal_rainfall','total_rainfall']

class threeDaysObservedRainfallSerializer(serializers.ModelSerializer):

    class Meta:
        model = RainfallObservations
        fields=['st_id','rf_date','rainfall']


class monthlyRainfallSerializer(serializers.ModelSerializer):

    class Meta:
        model=MonthlyRainfall
        fields=['station_id','month_serial','month_name','max_rainfall','normal_rainfall','min_rainfall']


class feedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model=Feedback
        fields=['id','name','email','comments']

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}


class DataLoadProfileUserprofilestationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = data_load_models.DataLoadProfileUserprofilestations
        fields = ('id', 'profile_id', 'ffwcstations2023_id')
        

class DataLoadProfileUserprofileIndianStationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = data_load_models.DataLoadProfileUserprofileindianstations
        fields = ('id', 'profile_id', 'indianstations_id')



class FfwcStationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = data_load_models.FfwcStationInfo
        fields = ('__all__')