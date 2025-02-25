from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.views.main import ChangeList
from django import forms
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import redirect

from django.views.generic.edit import FormView
import re

from data_load import models
from data_load.models import FfwcStations2023,WaterLevelObservations,DataHeader
from data_load.models import WaterLevelForecasts

from .models import Profile



from import_export import resources
from import_export.admin import ImportExportModelAdmin,ExportActionMixin

from data_load.forms import StationChangeListForm

import csv
import io
from django.http import HttpResponse,HttpResponseRedirect, JsonResponse
from django.urls import include, path

from datetime import datetime
import pandas as pd

from data_load.tasks import go_to_sleep,read_file_and_insert,import_forecast_files

from django_celery_results.admin import TaskResult, GroupResult

from django.http import StreamingHttpResponse
from django.template import Context, Template,loader
import time

import os

admin.site.unregister(TaskResult)
admin.site.unregister(GroupResult)

admin.site.disable_action("delete_selected")
# Unregister the provided model admin
admin.site.unregister(User)



# Register out own model admin, based on the default UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = ["delete_selected"]



class StationAdminInline(admin.TabularInline):
    model=Profile.userProfileStations.through
    search_fields=['id']

class IndianStationAdminInline(admin.TabularInline):
    model=Profile.userProfileIndianStations.through

class StationFilter(admin.SimpleListFilter):

   def get_queryset(self, request):
    all_result = super(StationFilter, self).get_queryset(request)
    return all_result

@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):

    # IndianStationAdminInline
    # inlines=[StationAdminInline,IndianStationAdminInline]
    # list_filter = (StationFilter,)

    list_display= [field.name for field in models.Profile._meta.get_fields() if not field.many_to_many]
    raw_id_fields=['user']
    ordering = ('id',)


    def get_queryset(self, request):
        all_result = super(ProfileAdmin, self).get_queryset(request)
        if request.user.is_superuser: return all_result
        
        else:
            user_id = request.user.id
            return all_result.filter(user_id=user_id)


@admin.register(models.FfwcStations2023)
class StationAdmin(admin.ModelAdmin):
    ordering = ('id',)
    search_fields =['name','basin']

    def get_data_header(obj):
        print(obj.id)
        data_header =  DataHeader.objects.filter(web_id=obj.id).values_list('data_header', flat=True)[0]
        # .values_list('data_header', flat=True)[0]

        return ("%s" % (data_header))

    get_data_header.short_description = 'Data Header'

    # def get_station_name(obj):
    #     name = models.FfwcStations2023.objects.filter(id=obj.st_id).values_list('name', flat=True)[0]
    #     return ("%s" % (name))

    # get_station_name.short_description = 'Station Name'

    # 'id','coords','name','river','basin_order','basin','dangerlevel','riverhighestwaterlevel','avglandlevel','river_chainage',
    #     'division','district','upazilla','union','long','order_up_down','lat','forecast_observation','status','station_order',
    #     'medium_range_station','unit_id','jason_2_satellie_station'

    # list_display=[f.name for f in models.FfwcStations2023._meta.get_fields() if not f.many_to_many]
    list_display=[
        'id','name','river','basin','dangerlevel','riverhighestwaterlevel',
        'division','district','upazilla','union','long','lat',get_data_header
    ]



class FeedbackResources(resources.ModelResource):
    class Meta:
        model = models.Feedback

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'comments')


# admin.site.register(models.FfwcStations2023,StationAdmin)

class IndianStationAdmin(admin.ModelAdmin):
    ordering = ('id',)
    search_fields =['station_name','basin_name']
    list_display=[f.name for f in models.IndianStations._meta.get_fields() if not f.many_to_many]
admin.site.register(models.IndianStations,IndianStationAdmin)


class IndianWaterLevelObservationsResources(resources.ModelResource):
    class Meta:
        model = models.IndianWaterLevelObservations

class IndianWaterLevelObservationsAdmin(ImportExportModelAdmin):

    def get_station_name(obj):
        name = models.IndianStations.objects.filter(id=obj.station_id).values_list('station_name', flat=True)[0]
        return ("%s" % (name))
        
    get_station_name.short_description = 'Station Name'

    list_display = ('station_id','station_code',get_station_name, 'data_time', 'waterlevel')
    list_filter = ('data_time','station_id')
    search_fields = ('data_time', 'station_id')
    resource_classes = [IndianWaterLevelObservationsResources]

admin.site.register(models.IndianWaterLevelObservations,IndianWaterLevelObservationsAdmin)

# Indian Waterlevl Observations
# class IndianWaterLevelObservationsAdmin(admin.ModelAdmin):
#     ordering = ('id',)
#     search_fields =['station_id','data_time']
#     list_display=[f.name for f in models.IndianWaterLevelObservations._meta.get_fields() if not f.many_to_many]

# admin.site.register(models.IndianWaterLevelObservations,IndianWaterLevelObservationsAdmin)




class MonthlyRainfallResources(resources.ModelResource):
    class Meta:
        model = models.MonthlyRainfall
        import_id_fields = ('station_id',)

class MonthlyRainfallAdminAdmin(ImportExportModelAdmin):

    def get_station_name(obj):
        name = models.FfwcStations2023.objects.filter(id=obj.station_id).values_list('name', flat=True)[0]
        return ("%s" % (name))
    get_station_name.short_description = 'Station Name'

    list_display = ('station_id', get_station_name,'month_name', 'normal_rainfall','max_rainfall','min_rainfall','unit')
    list_filter = ('month_name','station_id')
    search_fields = ('station_id', 'month_name')
    resource_classes = [MonthlyRainfallResources]

admin.site.register(models.MonthlyRainfall,MonthlyRainfallAdminAdmin)


class RainfallObservationResources(resources.ModelResource):
    class Meta:
        model = models.RainfallObservations
        import_id_fields = ('rf_id',)

class RainfallObservationsAdmin(ImportExportModelAdmin):

    def get_station_name(obj):
        name = models.FfwcStations2023.objects.filter(id=obj.st_id).values_list('name', flat=True)[0]
        return ("%s" % (name))
        
    get_station_name.short_description = 'Station Name'

    list_display = ('st_id',get_station_name, 'rf_date', 'rainfall')
    list_filter = ('rf_date','st_id')
    search_fields = ('rf_date', 'st_id')
    resource_classes = [RainfallObservationResources]

admin.site.register(models.RainfallObservations,RainfallObservationsAdmin)


class WaterLevelObservationsResources(resources.ModelResource):

    class Meta:
        model = models.WaterLevelObservations
        import_id_fields = ('wl_id',)


# Export Mixin 
class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"



# Observation With Import CSV
class CsvImportForm(forms.Form):
    # csv_file = MultipleFileField()
    csv_file = forms.FileField()

@admin.register(models.WaterLevelObservations)
class WaterlevelObservationsAdmin(admin.ModelAdmin,ExportCsvMixin):
# class WaterlevelObservationsAdmin(ImportExportModelAdmin,ExportActionMixin):

    # change_list_template = "data_load/custom_file_upload.html"

    def get_station_name(obj):
        name = models.FfwcStations2023.objects.filter(id=obj.st_id).values_list('name', flat=True)[0]
        return ("%s" % (name))

    get_station_name.short_description = 'Station Name'

    list_display = ['st_id', get_station_name,'wl_date', 'waterlevel']
    list_filter = ('wl_date','st_id')
    search_fields = ('st_id', 'waterlevel')

    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "Export Selected"



    def insertIntoDatabase(self,df):

        for index, row in df.iterrows():

            st_id=int(row['st_id'])
            wl_date= datetime.strptime(row['wl_date'], '%Y-%m-%d %H:%M:%S')
            waterLevel=float(row['waterLevel'])

            print(st_id,wl_date,waterLevel)

            created = WaterLevelObservations.objects.update_or_create(
                st_id = st_id,
                wl_date = wl_date,
                waterlevel = waterLevel
            )
            
            # obj = WaterLevelObservations(
            #     st_id=row['st_id'],
            #     wl_date=row['wl_date'],
            #     waterLevel=row['waterLevel'],
            # )
            # obj.save()

            # print(row['st_id'],row['wl_date'],row['waterLevel'])

    def pdProcessing(self,pd_csv):

        # task=read_file_and_insert.delay(1)
        workingDirectory =  os.getcwd()
        dataHeaderPath=os.path.join(workingDirectory,'uploads/ffDataHeader.csv')
        headerDF=pd.read_csv(dataHeaderPath)

        df=pd.read_csv(pd_csv,sep=';',skiprows=1)
        df.rename(columns={'YYYY-MM-DD HH:MM:SS':'wl_date'},inplace=True)

        observedDataStations=df.columns.to_list()[1:]
        # print(observedDataStations)

        for station in observedDataStations:
            
            if station in headerDF['ffData Header'].to_list():
                st_id=int(headerDF.where(headerDF['ffData Header']==station).dropna()['id'])
                # st_id=headerDF.where(headerDF['ffData Header']==station)['id'][0]
                print('Header Matched')
                print(st_id,station)
                stationDFtoDatabase=df[['wl_date',station]].copy(deep=True)
        #         stationDFtoDatabase.rename(columns={station:'stationName'})
                id_column=[st_id]*len(stationDFtoDatabase)
                
                stationDFtoDatabase.insert (0, "st_id", id_column)
                stationDFtoDatabase.rename(columns={station:'waterLevel'},inplace=True)
                self.insertIntoDatabase(stationDFtoDatabase)
            
            else:
                print('Header Did Not Matched',st_id,station)
                continue

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv),]
        return my_urls + urls

    def import_csv(self,request):

        # print(uploadStationsDF)

        if request.method == "POST":

            print('Action in Observed Data Upload Post')
            
            form = CsvImportForm(request.POST)
            noOfFiles=1
            # noOfFiles = len(request.FILES["csv_file"])
            # print('Number of Files: ',noOfFiles)
            ## csv_file = request.FILES.get["csv_file"]

       
            csv_file = request.FILES["csv_file"]
            file_obj = csv_file.read()
            pd_csv=io.BytesIO(file_obj)
            self.pdProcessing(pd_csv)

            task=read_file_and_insert.delay(1)

            # return redirect(".")
            return render(request, "admin/csv_upload.html",{"form": form,"noOfFiles":noOfFiles,"task_id":task})
        

        else:

            form = CsvImportForm()
            task=read_file_and_insert.delay(1)
            noOfFiles=1
            # noOfFiles = len(request.FILES["csv_file"])

 
            # # form = FileFieldForm()
            # payload = {"form": form}
            context={"form": form}
            # context={"form": form,"task_id":task,"noOfFiles":noOfFiles}

        return render(request, "admin/csv_upload.html",{"form": form,"noOfFiles":noOfFiles,"task_id":task})





    # resource_classes = [WaterLevelObservationsResources]

# admin.site.register(models.WaterLevelObservations,WaterlevelObservationsAdmin)

class WaterLevelForecastResources(resources.ModelResource):
    class Meta:
        model = models.WaterLevelForecasts
        import_id_fields = ('fc_id',)

# Import form for Forecast Moduel
class ForecastCsvImportForm(forms.Form):
    # your_name = forms.CharField(label="Your name", max_length=100)
    # forecast_csv_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
     forecast_csv_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}))


# class WaterlevelForecastAdmin(ImportExportModelAdmin,ExportActionMixin):
@admin.register(models.WaterLevelForecasts)
class WaterlevelForecastAdmin(admin.ModelAdmin,ExportCsvMixin):

    def get_station_name(obj):
        name = models.FfwcStations2023.objects.filter(id=obj.st_id).values_list('name', flat=True)[0]
        return ("%s" % (name))
    get_station_name.short_description = 'Station Name'

    list_display = ('st_id',get_station_name,'fc_date', 'waterlevel')
    list_filter = ('fc_date','st_id')
    search_fields = ('st_id', 'waterlevel')


    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "Export Selected"


    def insertThisDataFrame(self,forecastDF,station_id_list):
    
        print('Inserting Individual Forecast DataFrame . . . ')
        forecastDF.insert(0,'st_id',station_id_list)
        forecastDF=forecastDF.drop(forecastDF[forecastDF['waterLevel'] == -9999.0].index)
        
        # If Empty Data Frame
        if len(forecastDF)==0:return 
        forecastDF.reset_index(drop=True,inplace=True)

        patternOne = r"\b([1-9]|[12]\d|3[01])[-/]([1-9]|1[0-2])[-/](19\d\d|\d\d) ([0-9][0-9]|[0-9])\b"
        # YYYY/MM/DD or YYYY-MM-DD
        patternTwo=r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01]) (0[1-9])\b"

        for index in range(len(forecastDF)):
            dateTimeString=forecastDF.iloc[index]['fc_date']
            if re.findall(patternOne,dateTimeString):
                dateTime=datetime.strptime(dateTimeString, '%d/%m/%y %H:%M')
                # print(dateTime)
                # forecastDF.iloc[index]['fc_date']=dateTime
                forecastDF.iloc[index, forecastDF.columns.get_loc('fc_date')]= dateTime
        #         print(dateTime)
            elif re.findall(patternTwo,dateTimeString):
                dateTime=datetime.strptime(dateTimeString, '%Y-%m-%d %H:%M:%S')
                forecastDF.iloc[index]['fc_date']=dateTime


        print(forecastDF.head())
        print('=================================================')

        for index, row in forecastDF.iterrows():


            # print(forecastDF.iloc[index])

            st_id = int(row['st_id'])
            if type(row['fc_date']) == str: fc_date= datetime.strptime(row['fc_date'], '%Y-%m-%d %H:%M:%S')
            else:fc_date=row['fc_date']
            waterLevel= float(row['waterLevel'])

            # print(st_id,fc_date,waterLevel)


            # # # t = Template('{{ mydata }} <br />\n')

            created = WaterLevelForecasts.objects.update_or_create(
                st_id = st_id,
                fc_date = fc_date,
                waterlevel = waterLevel
            )   

            # print('Created ..... ')

        # task=read_file_and_insert.delay(noOfFiles)
        return f'Inserted for {st_id}'

    def insertForecastIntoDatabase(self,forecastDF,stationNameToIdDict,noOfFiles):


        print('Inserting Forecast DataFrame . . . ')
        # print(forecastDF.columns)
        # print(stationNameToIdDict)
        # print(forecastDF.isnull().values.any())

        if (forecastDF['YYYY-MM-DD HH:MM:SS'].isnull().values.any()):return


        forecastDF.rename(columns={'YYYY-MM-DD HH:MM:SS':'fc_date'},inplace=True)
        print(forecastDF.head())


        csvFileStationList=forecastDF.columns.to_list()[1:]

        print('Station List: ', csvFileStationList)

        for csv_file_station in csvFileStationList:
            
            stationDF=forecastDF[['fc_date',csv_file_station]].copy(deep=True)
            columnsList=stationDF.columns.to_list()
            stationName=columnsList[1][:-4]
            print('Station Name: ', stationName)
            stationDF.rename(columns={columnsList[1]:'waterLevel'},inplace=True)

            if stationName in stationNameToIdDict.keys():
                station_id=stationNameToIdDict[stationName]
                station_id_list=[station_id]*len(forecastDF)
                self.insertThisDataFrame(stationDF,station_id_list)
                print('Finished Inserting  ', station_id, stationName)
            else: return

        # =================================================== OLDS ===================================
        # print('Inserting Forecast DataFrame . . . ')
        # # print(stationNameToIdDict)
        # # print(forecastDF.isnull().values.any())

        # if (forecastDF['YYYY-MM-DD HH:MM:SS'].isnull().values.any()):return


        # forecastDF.rename(columns={'YYYY-MM-DD HH:MM:SS':'fc_date'},inplace=True)

        # # print(forecastDF)

        # forecastDF=forecastDF.iloc[:,:2]
        # columnsList=forecastDF.columns.to_list()
        # stationName=columnsList[1][:-6]
        # forecastDF.rename(columns={columnsList[1]:'waterLevel'},inplace=True)

    

        # if stationName in stationNameToIdDict.keys():
        #     station_id=stationNameToIdDict[stationName]
        #     station_id_list=[station_id]*len(forecastDF)
        # else: return
        
        # forecastDF.insert(0,'st_id',station_id_list)
        # forecastDF=forecastDF.drop(forecastDF[forecastDF['waterLevel'] == -9999.0].index)
        # # If Empty Data Frame
        # if len(forecastDF)==0:return 
        # forecastDF.reset_index(drop=True,inplace=True)
        

        # # DD/MM/YYYY or DD-MM-YYYY
        # # patternOne = r"\b([1-9]|[12]\d|3[01])[-/]([1-9]|1[0-2])[-/](19\d\d|\d\d) ([1-9])\b"
        # patternOne = r"\b([1-9]|[12]\d|3[01])[-/]([1-9]|1[0-2])[-/](19\d\d|\d\d) ([0-9][0-9]|[0-9])\b"
        # # YYYY/MM/DD or YYYY-MM-DD
        # patternTwo=r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01]) (0[1-9])\b"

        # for index in range(len(forecastDF)):
        #     dateTimeString=forecastDF.iloc[index]['fc_date']
        #     if re.findall(patternOne,dateTimeString):
        #         dateTime=datetime.strptime(dateTimeString, '%d/%m/%y %H:%M')
        #         # print(dateTime)
        #         # forecastDF.iloc[index]['fc_date']=dateTime
        #         forecastDF.iloc[index, forecastDF.columns.get_loc('fc_date')]= dateTime
        # #         print(dateTime)
        #     elif re.findall(patternTwo,dateTimeString):
        #         dateTime=datetime.strptime(dateTimeString, '%Y-%m-%d %H:%M:%S')
        #         forecastDF.iloc[index]['fc_date']=dateTime

        
        # print(forecastDF.head())
        # print('=================================================')

        # for index, row in forecastDF.iterrows():


        #     # print(forecastDF.iloc[index])

        #     st_id = int(row['st_id'])
        #     if type(row['fc_date']) == str: fc_date= datetime.strptime(row['fc_date'], '%Y-%m-%d %H:%M:%S')
        #     else:fc_date=row['fc_date']
        #     waterLevel= float(row['waterLevel'])

        #     # # fc_date= forecastDF.iloc[index]['fc_date']
        #     # fc_date= datetime.strptime(row['fc_date'], '%Y-%m-%d %H:%M:%S')


        #     # print('Index: ', index, type(row['fc_date']))
            
        #     # print(st_id,row['fc_date'],waterLevel)

        #     # st_id = int(forecastDF.iloc[index]['st_id'])
        #     # # fc_date= forecastDF.iloc[index]['fc_date']
        #     # fc_date= datetime.strptime(forecastDF.iloc[index]['fc_date'], '%Y-%m-%d %H:%M:%S') 
        #     # waterlevel= float(forecastDF.iloc[index]['waterlevel'])

        #     # # print(index,forecastDF.iloc[index]['st_id'],forecastDF.iloc[index]['fc_date'],forecastDF.iloc[index]['waterlevel'])
        #     # # st_id=row['st_id']
        #     # # wl_date= row['fc_date']
        #     # # waterLevel=row['waterLevel']

        #     # # print(st_id,fc_date,waterlevel)
        #     print(st_id,fc_date,waterLevel)


        #     # # # t = Template('{{ mydata }} <br />\n')

        #     created = WaterLevelForecasts.objects.update_or_create(
        #         st_id = st_id,
        #         fc_date = fc_date,
        #         waterlevel = waterLevel
        #     )

        # # task=read_file_and_insert.delay(noOfFiles)
        # return f'Inserted for {st_id}'


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('forecast-import-csv/', self.forecast_import_csv),]
        return my_urls + urls

    def example(self):
        for i in range(5):
            # Add <br> to break line in browser
            yield f'{i}<br>'
            time.sleep(1)


    def gen_rendered(self,msg):  
        t = Template('{{ mydata }} <br />\n')
        c = Context({'mydata': msg})
        yield t.render(c)

        # for x in range(1,11):
        #     c = Context({'mydata': x})
        #     yield t.render(c)

        # t = loader.get_template('admin/multiple_csv_upload.html') # or whatever
        # buffer = ' ' * 1024

        # yield t.render(Context({"form": form,"task_id":task,"noOfFiles":noOfFiles, 'buffer': buffer}))
        # for x in range(1,11):
        #     yield '<p>x = {}</p>{}\n'.format(x, buffer)
            
    def forecast_import_csv(self,request):

        workingDirectory =  os.getcwd()
        dataHeaderPath=os.path.join(workingDirectory,'uploads/ffDataHeader.csv')
        
        stationDetails=pd.read_csv(dataHeaderPath)

        stationNameToIdDict={}
        for index in range(len(stationDetails)):
            stationNameToIdDict[stationDetails.iloc[index]['name']]=stationDetails.iloc[index]['id']

        # if request.method == "POST" and request.FILES.getlist('forecast_csv_file'):
        if request.method == "POST":
            
            print('Action is Post')

            form = ForecastCsvImportForm(request.POST)

            noOfFiles = len(request.FILES.getlist('forecast_csv_file'))
            print('Number of Files: ',noOfFiles)
            task=read_file_and_insert.delay(noOfFiles)

            for f in request.FILES.getlist('forecast_csv_file'):
                
                print('In the Loop')

                file_obj=f.read()
                pd_csv=io.BytesIO(file_obj)
                forecastDF=pd.read_csv(pd_csv,skiprows = 1)
                # print(forecastDF.columns)
                # print('------------------------------------')

                # import_forecast_files(1,forecastDF,stationNameToIdDict)

                msg=self.insertForecastIntoDatabase(forecastDF,stationNameToIdDict,noOfFiles)


                # response = StreamingHttpResponse(self.gen_rendered(msg))
                # return response

            return render(request, "admin/multiple_csv_upload.html",{"form": form,"noOfFiles":noOfFiles,"task_id":task})
            # return redirect(".")
            # return StreamingHttpResponse(example())
            # response = StreamingHttpResponse(self.gen_rendered(msg))
            # return response


        else:

            form = ForecastCsvImportForm()
            task=read_file_and_insert.delay(1)
            noOfFiles = len(request.FILES.getlist('forecast_csv_file'))

        # return render(request, "admin/multiple_csv_upload.html",{"form": form})
        # noOfFiles = len(request.FILES.getlist('forecast_csv_file'))
        # context = {"form": form,"task_id":task,"your_name":your_name}
        # return StreamingHttpResponse(example())


        

        # response = StreamingHttpResponse(self.gen_rendered())
        # # response = StreamingHttpResponse(self.gen_rendered(form,task,noOfFiles))
        # # response = StreamingHttpResponse(self.example())
        # # response['Content-Type'] = 'text/plain'
        # return response

        return render(request, "admin/multiple_csv_upload.html",{"form": form,"task_id":task,"noOfFiles":noOfFiles})




