from datetime import datetime
import math
import pandas as pd
import geopandas as gpd
import os
import xarray as xr
import numpy as np

def generateDownloadFileNameList(downloadYear):
    
    fileNameList=[]
    
    dayOfTheYear=datetime.now().timetuple().tm_yday
    today=datetime.now()
    todayDateString=today.strftime("%Y-%m-%d")
    print('Date Today: ', todayDateString, '\nDay of the Year: ', dayOfTheYear)

    for i in range(1,11):
        
        downloadDay=dayOfTheYear-i
        numberOfDigits = int(math.log10(downloadDay))+1
        if numberOfDigits==2:downloadDay = str(downloadDay).rjust(3, '0')
        else: downloadDay = str(downloadDay)
        dowanloadFileName=str(downloadYear)+downloadDay+'.nc'

        fileNameList.append(dowanloadFileName)
    
    return fileNameList


# fileNameList = generateDownloadFileNameList(2024)
# print(fileNameList)


def computeDailyBasinWiseMeanPrecipitation(fileName,stationName,dailyPrecipitationDict):

    dir_path = os.getcwd()
    # print('Directory Path: ', dir_path)
    # dir_path = os.getcwd()
    # print('Directory Path: ', dir_path)
    dir_path=os.path.dirname(dir_path)
    # print('File Path: ', file_path)




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


def returnRainfallRecords(stationName,givenDate):

    fileNameList = generateDownloadFileNameList(2024)
    # print(fileNameList)

    dailyPrecipitationDict={}

    for fileName in fileNameList:

        # dir_path = os.getcwd()
        # dir_path=os.path.dirname(dir_path)
        # print('Directory Path: ', dir_path)
        # basin_json_file_path=os.path.join(dir_path,f'floodForecastStations/{stationName}.json')
        # print('Basin JSON File: ', basin_json_file_path)
        # stationGDF=gpd.read_file(basin_json_file_path,crs="epsg:4326")
        # print(stationGDF)
        
        dailyPrecipitationDict= computeDailyBasinWiseMeanPrecipitation(fileName,stationName,dailyPrecipitationDict)

        # except:
        #     print(f'File {fileName} Does Not Exist')


    observedRainfallDF=generateObservedDataframe(dailyPrecipitationDict)

    print(observedRainfallDF)

    # forecastPrecipitationDict=computeBasinWiseForecast(stationName,givenDate)
    # forecastRainfallDF = generateForecastDataframe(forecastPrecipitationDict)


    # rainfallRecords = returnDesiredDataframe(observedRainfallDF,forecastRainfallDF)
    # # rainfallRecords=[]
    # return rainfallRecords

def FlashFlood(forecast_date,basin_id):

    # forecast_date = kwargs['forecast_date']
    # basin_id = kwargs['basin_id']

    print('Basin Id : ', basin_id)
    stationDict={ 1:'khaliajhuri', 2:'gowainghat', 3:'dharmapasha',4:'userbasin',5:'laurergarh',6:'muslimpur'}
    

    # # Retrieving Threshold Dict   
    # dir_path = os.getcwd()
    # station_threshold_path=os.path.join(dir_path,'floodForecastStations/stationThresholds.txt')

    # with open(station_threshold_path) as f: 
    #     data = f.read() 

    # stationThresholdsText = ast.literal_eval(data) 

    # newStationThresholdsText = {}
    # for key,value in stationThresholdsText.items():
    #     newDict = {int(innerKey):innerValue for innerKey,innerValue in stationThresholdsText[key].items()}
    #     newStationThresholdsText[int(key)]=newDict

    # print('Station Threshold Dict {}')
    # print(newStationThresholdsText)
    # stationThresholds = newStationThresholdsText



    # # Retrieving Threshold List   
    # # Retrieving Threshold List    

    # dir_path = os.getcwd()
    # station_threshold_list_path=os.path.join(dir_path,'floodForecastStations/stationThresholdsList.txt')

    # with open(station_threshold_list_path) as f: 
    #     data = f.read() 
    #     # print(data)

    # stationThresholdsListText = ast.literal_eval(data) 
    # print('Station Threshold List []: ')
    # # print(stationThresholdsListText)

    # newStationThresholdsListTextDict = {}

    # for key,value in stationThresholdsListText.items():
    #     innerDict={}
    #     for innerKey,innerValue in stationThresholdsListText[key].items():
    #         innerDict[int(innerKey)]=[int(value) if isinstance(value,str) else value for value in innerValue ]
    #     newStationThresholdsListTextDict[int(key)]=innerDict



    # stationThresholdsList = newStationThresholdsListTextDict
    # # Main Computatin for Basin Wise Flash Flood 


    # hourThresholdDict=stationThresholds[basin_id]
    # indexedHourThresholdDict=stationThresholdsList[basin_id]


    givenDate = forecast_date
    stationName=stationDict[basin_id]


    print('Station Name: ', stationName)

    rainfallRecords=returnRainfallRecords(stationName,givenDate)


    # intensityThresholdDataframe,givenDateInDateTime,dateTimeRangeFromGivenDateTime,rangeStart,dictRainfall = processDateTimeDictRainfall(givenDate,rainfallRecords,indexedHourThresholdDict)
    # # print(intensityThresholdDataframe)
    # # hourThresholdDict={24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123}
    # hourList=[24, 48, 72, 120, 168, 240]

    # for dateTime in dateTimeRangeFromGivenDateTime:

    #     totalRainfall=returnCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
    #     dateString=datetime.strftime(dateTime,'%Y-%m-%d')
    #     intensityThresholdDataframe[dateString]=totalRainfall

    # # print(intensityThresholdDataframe)
    # jsonResult=intensityThresholdDataframe.to_dict()

    # jsonResult={}

    # return Response(jsonResult)



# FlashFlood(forecast_date='2024-05-19',basin_id=1)