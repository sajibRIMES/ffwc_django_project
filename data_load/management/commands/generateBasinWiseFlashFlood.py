from django.core.management import BaseCommand, CommandError
from django.conf import settings

from rest_framework.response import Response
import os
import math
import json
import ast 

from datetime import date, datetime, timedelta
import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray
import shapely
import netCDF4
import numpy as np
from pyidw import idw
import rasterio

from datetime import date, datetime, timedelta

import sshtunnel
from sshtunnel import SSHTunnelForwarder

from sqlalchemy import create_engine
import pymysql

from data_load.models import Basin_Wise_Flash_Flood_Forecast

class Command(BaseCommand):

    help='Generate Rainfall Distributon Map by Date'

    # def add_arguments(self,parser):
    #     parser.add_argument('date',type=str, help='date for generating Rainfall Distribution Map')

        
    def handle(self, *args, **kwargs):
        
        try :
            dateInput = kwargs['date']
            # print('Date Input Form Parameter', dateInput)

        except:
            updateDate=datetime.today()-timedelta(days=0)
            dateInput=datetime.strftime(updateDate,'%Y-%m-%d')
            # print('Date Input Without Parameter : ', dateInput)

        self.main(dateInput)  

    def generateDownloadFileNameList(self,downloadYear):
        
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

    def generateObservedDataframe(self,dailyPrecipitationDict):


        dateList=list(dailyPrecipitationDict.keys())
        rainfallList=list(dailyPrecipitationDict.values())
        dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
        observedRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
        observedRainfallDF.sort_values(by='Date',inplace=True)
        observedRainfallDF.reset_index(drop=True,inplace=True)

        return observedRainfallDF

    def computeBasinWiseForecast(self, stationName,givenDate):

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

    def generateForecastDataframe(self,forecastPrecipitationDict):

        dateList=list(forecastPrecipitationDict.keys())
        rainfallList=list(forecastPrecipitationDict.values())
        dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
        forecastRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
        forecastRainfallDF.sort_values(by='Date',inplace=True)
        forecastRainfallDF.reset_index(drop=True,inplace=True)

        return forecastRainfallDF

    def returnDesiredDataframe(self,observedRainfallDF,forecastRainfallDF):
        requiredDF=pd.concat([observedRainfallDF,forecastRainfallDF])
        requiredDF.reset_index(drop=True,inplace=True)

        return requiredDF

    def returnRainfallRecords(self,stationName,givenDate):
            current_year = str(datetime.now().year)
            fileNameList = self.generateDownloadFileNameList(current_year)
            # print(fileNameList)

            dailyPrecipitationDict={}
            for fileName in fileNameList:
                try:
                    dailyPrecipitationDict= computeDailyBasinWiseMeanPrecipitation(fileName,stationName,dailyPrecipitationDict)
                except:
                    print(f'Observed File {fileName} Does Not Exist')


            observedRainfallDF=self.generateObservedDataframe(dailyPrecipitationDict)

            print('Observed Rainfall DF')
            print(observedRainfallDF)

            forecastPrecipitationDict=self.computeBasinWiseForecast(stationName,givenDate)
            forecastRainfallDF = self.generateForecastDataframe(forecastPrecipitationDict)

            print('Forecast Rainfall DF')
            print(forecastRainfallDF)

            rainfallRecords = self.returnDesiredDataframe(observedRainfallDF,forecastRainfallDF)
            # rainfallRecords=[]
            return rainfallRecords

    def processDateTimeDictRainfall(self,givenDate,rainfallRecords,indexedHourThresholdDict):

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
        intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Thresholds'])
        givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
        
        noOfDayWithinRange=(rangeEnd-givenDateInDateTime).days
        print('No. of Days in range: ', noOfDayWithinRange)

        dateTimeRangeFromGivenDateTime=[givenDateInDateTime+timedelta(days=day) for day in range (0,noOfDayWithinRange+1)]

        return intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall


    def returnCumulativeRainfall(self,givenDateInDateTime,hourThresholdDict,hourList,rangeStart,dictRainfall):
        
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



    def FlashFlood(self,forecast_date,basin_id):

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

        stationThresholds = newStationThresholdsText
        dir_path = os.getcwd()
        station_threshold_list_path=os.path.join(dir_path,'floodForecastStations/stationThresholdsList.txt')

        with open(station_threshold_list_path) as f: 
            data = f.read() 

        stationThresholdsListText = ast.literal_eval(data) 
        newStationThresholdsListTextDict = {}

        for key,value in stationThresholdsListText.items():
            innerDict={}
            for innerKey,innerValue in stationThresholdsListText[key].items():
                innerDict[int(innerKey)]=[int(value) if isinstance(value,str) else value for value in innerValue ]
            newStationThresholdsListTextDict[int(key)]=innerDict

        stationThresholdsList = newStationThresholdsListTextDict
        givenDate = forecast_date
        stationName=stationDict[basin_id]
        hourThresholdDict=stationThresholds[basin_id]
        indexedHourThresholdDict=stationThresholdsList[basin_id]

        print('Station Name: ', stationName)

        rainfallRecords=self.returnRainfallRecords(stationName,givenDate)
        print('Rainfall Records: ')
        print(rainfallRecords)

        intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall = self.processDateTimeDictRainfall(givenDate,rainfallRecords,indexedHourThresholdDict)
        hourList=[24, 48, 72, 120, 168, 240]

        print('Date Time Range: ', dateTimeRangeFromGivenDateTime)

        for dateTime in dateTimeRangeFromGivenDateTime:

            print(dateTime)
            totalRainfall=self.returnCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
            dateString=datetime.strftime(dateTime,'%Y-%m-%d')
            intensityThresholdDataframe[dateString]=totalRainfall

        # print(intensityThresholdDataframe)
        jsonResult=intensityThresholdDataframe.to_dict()

        # jsonResult={}

        return jsonResult


    def transformIntoDataFrame(self,data_dict,dateInput,basin_id):

        # Prepare a list to hold the rows of data
        rows = []

        # Fixed station_id

        # Iterate through the dictionary
        for date_key, values in data_dict.items():
            # print(data_dict)
            if date_key not in ["Hours", "Thresholds"]:  # Skip the Hours and Thresholds keys
                for index, value in values.items():
                    # Get corresponding hours and thresholds
                    hours = data_dict["Hours"][index]
                    thresholds = data_dict["Thresholds"][index]
                    
                    # Append the row to the list
                    rows.append({
                        'prediction_date':dateInput,
                        'basin_id': basin_id,
                        'hours': hours,
                        'thresholds': thresholds,
                        'date': datetime.strptime(date_key, "%Y-%m-%d").date(),
                        'value': value
                    })

        # Create a DataFrame
        df = pd.DataFrame(rows)

        return df

    def insert_dataframe(self, df):

        df_to_insert = df[['prediction_date','basin_id','date','hours','thresholds','value']].copy(deep=True)

        for index, row in df_to_insert.iterrows():
            forecast = Basin_Wise_Flash_Flood_Forecast(
                prediction_date=row['prediction_date'],
                basin_id=row['basin_id'],
                date=row['date'],
                hours=row['hours'],
                thresholds=row['thresholds'],
                value=row['value']
            )
            forecast.save()  # Save the instance to the database

    def main(self,dateInput):
        basin_id_list=[1,2,3,5,6,7,8,9,10,11]

        for basin_id in basin_id_list:
            response = self.FlashFlood(dateInput,basin_id)
            df = self.transformIntoDataFrame(response,dateInput,basin_id)
            # print(df)
            self.insert_dataframe(df)
