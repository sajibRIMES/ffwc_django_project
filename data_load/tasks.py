from celery import shared_task,current_task
from celery_progress.backend import ProgressRecorder
from time import sleep


from celery import shared_task,current_task
from celery import app

from data_load.models import WaterLevelForecasts
from datetime import datetime
import pandas as pd
import re


@shared_task(bind=True)
def  go_to_sleep(self, seconds):
    
    progress_recorder = ProgressRecorder(self)
    for i in range(10):
        sleep(seconds)
        progress_recorder.set_progress(i + 1, 100, f'On Iteration {i}')
    return 'done'


@shared_task(bind=True)
def  read_file_and_insert(self, noOfFiles):
    progress_recorder = ProgressRecorder(self)
    for i in range(noOfFiles):
        sleep(5)
        progress_recorder.set_progress(i + 1, noOfFiles, f'Working On File Number {i}')
    return 'Database Insertion In Progress . . '


@shared_task(bind=True)
def import_forecast_files(duration,forecastDF,stationNameToIdDict):
    
    sleep(duration)
    forecastDF.rename(columns={'YYYY-MM-DD HH:MM:SS':'fc_date'},inplace=True)
    forecastDF=forecastDF.iloc[:,:3:2]
    columnsList=forecastDF.columns.to_list()
    stationName=columnsList[1][:-4]
    forecastDF.rename(columns={columnsList[1]:'waterLevel'},inplace=True)


    station_id=stationNameToIdDict[stationName]
    station_id_list=[station_id]*len(forecastDF)
    forecastDF.insert(0,'st_id',station_id_list)
    forecastDF=forecastDF.drop(forecastDF[forecastDF['waterLevel'] == -9999.0].index)
    forecastDF.reset_index(drop=True,inplace=True)

    print(forecastDF.head())

    # DD/MM/YYYY or DD-MM-YYYY
    patternOne = r"\b([1-9]|[12]\d|3[01])[-/]([1-9]|1[0-2])[-/](19\d\d|\d\d) ([1-9])\b"
    # YYYY/MM/DD or YYYY-MM-DD
    patternTwo=r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01]) (0[1-9])\b"

    for index in range(len(forecastDF)):
        dateTimeString=forecastDF.iloc[index]['fc_date']
        if re.findall(patternOne,dateTimeString):
            dateTime=datetime.strptime(dateTimeString, '%d/%m/%y %H:%M')
            forecastDF.iloc[index]['fc_date']=dateTime
    #         print(dateTime)
        elif re.findall(patternTwo,dateTimeString):
            dateTime=datetime.strptime(dateTimeString, '%Y-%m-%d %H:%M:%S')
            forecastDF.iloc[index]['fc_date']=dateTime

    

    for index, row in forecastDF.iterrows():


        st_id = int(row['st_id'])
        
        # fc_date= forecastDF.iloc[index]['fc_date']
        fc_date= datetime.strptime(row['fc_date'], '%Y-%m-%d %H:%M:%S')
        waterLevel= float(row['waterLevel'])

        # st_id = int(forecastDF.iloc[index]['st_id'])
        # # fc_date= forecastDF.iloc[index]['fc_date']
        # fc_date= datetime.strptime(forecastDF.iloc[index]['fc_date'], '%Y-%m-%d %H:%M:%S') 
        # waterlevel= float(forecastDF.iloc[index]['waterlevel'])

        # print(index,forecastDF.iloc[index]['st_id'],forecastDF.iloc[index]['fc_date'],forecastDF.iloc[index]['waterlevel'])
        # st_id=row['st_id']
        # wl_date= row['fc_date']
        # waterLevel=row['waterLevel']

        # print(st_id,fc_date,waterlevel)
        print(st_id,fc_date,waterLevel)

        created = WaterLevelForecasts.objects.update_or_create(
            st_id = st_id,
            fc_date = fc_date,
            waterlevel = waterLevel
        )


    print("Completed")

    return True