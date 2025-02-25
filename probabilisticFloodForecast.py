import pandas as pd
import geopandas as gpd
import shapely

import xarray as xr
import netCDF4
import rioxarray
from datetime import datetime,timedelta
import math
import numpy as np
import sys
from functools import partial
from os.path import exists

givenDate = sys.argv[1]
basin_id=int(sys.argv[2])



def returnRequired(basin_id=1):
    
    stationDict={ 1:'khaliajhuri', 2:'gowainghat', 3:'dharmapasha'}

    hourList=[24, 48, 72, 120, 168, 240]
    
    stationThresholdsList = {
        1: {0:[24,51.45], 1:[48,77.5], 2:[72,98.3], 3:[120,133], 4:[168,162], 5:[240,200]},
        2: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]},
        3: {0:[24,24.5], 1:[48,41.5], 2:[72,56.5], 3:[120,83], 4:[168,107.5], 5:[240,141]}
    }
    
    stationThresholds = {
        1:{24: 51.45, 48: 77.5, 72: 98.3, 120: 133, 168: 162, 240: 200},
        2:{24: 24.5, 48: 41.5, 72: 56.5, 120: 83, 168: 107.5, 240: 141},
        3:{24: 25, 48: 40.5, 72: 53.5, 120: 76, 168: 96, 240: 123},
    }
    
    
    stationName=stationDict[basin_id]
    hourThresholdDict=stationThresholds[basin_id]
    indexedHourThresholdDict=stationThresholdsList[basin_id]

    stationGDF=gpd.read_file(f'floodForecastStations/{stationName}.json',crs="epsg:4326")

    return hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF

def generateObservedFileNameList(downloadYear):
    
    fileNameList=[]
    dayOfTheYearList=[i for i in range(90,79,-1)]
    dayOfTheYearList.reverse()

    for day in dayOfTheYearList:
        dowanloadFileName=str(downloadYear)+str(day).rjust(3, '0')+'.nc'
        fileNameList.append(dowanloadFileName)
    
    return fileNameList


def computeDailyProbabilisticMeanPrecipitation(fileName,dailyPrecipitationDict={}):

    dataset=xr.open_dataset(f"probabilisticObserved/{fileName}")
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


def genObservedDataFrame():
    
    observedFileNameList = generateObservedFileNameList(2024)
    
    for fileName in observedFileNameList:
        try:
            dailyPrecipitationDict=computeDailyProbabilisticMeanPrecipitation(fileName)
        except:
            print(f'File {fileName} Does Not Exist')
            
    observedRainfallDF = probabilisticObservedDataframe(dailyPrecipitationDict)

    return observedRainfallDF


def returnModelFilenames():
    
    filenameList=[]
    # year,month,day=datetime.now().year,datetime.now().month,datetime.now().day
    year,month,day=2024,3,31
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



def computeProbabilisticForecast(fileName,forecastPrecipitationDict={}):
    
    forecastDataset=xr.open_dataset(f"{folderName}/{fileName}")
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
    
        forecastPrecipitationDict[dateList[dateIndex]]=totalPrecipitation*1000
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



def returnRequiredDateTime(rainfallRecords):
    
    rangeStart = rainfallRecords.iloc[0]['Date']
    rangeStart = datetime.strptime(rangeStart,'%Y-%m-%d')
    rangeEnd = rainfallRecords.iloc[len(rainfallRecords)-1]['Date']
    rangeEnd=datetime.strptime(rangeEnd,'%Y-%m-%d')
    
    
    dictRainfall=rainfallRecords.to_dict()
    # dictRainfall.keys()
    timeList=list(dictRainfall['Date'].values())
    rainfallList=list(dictRainfall['Rainfall'].values())
    dictRainfall={}
    for i,j in zip(timeList,rainfallList):
        dictRainfall[i]=j
    
    givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
    noOfDayWithinRange=(rangeEnd-givenDateInDateTime).days
    dateTimeRangeFromGivenDateTime=[givenDateInDateTime+timedelta(days=day) for day in range (0,noOfDayWithinRange+1)]

    return rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime


def probabilisticCumulativeRainfall(givenDateInDateTime,hourThresholdDict,hourList):

    
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


allModelDataFrameList=[]

hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF=returnRequired(basin_id)
observedRainfallDF = genObservedDataFrame()

modelFilenameList,folderName = returnModelFilenames()
model_no=0
for fileName in modelFilenameList:
    forecastPrecipitationDict= computeProbabilisticForecast(fileName)
    forecastRainfallDF = probabilisticForecastDataframe(forecastPrecipitationDict)
    rainfallRecords = probabilisticDesiredDataframe(observedRainfallDF,forecastRainfallDF)
    
    rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime = returnRequiredDateTime(rainfallRecords)
    intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Threshold'])
    

    modelCountDF=pd.DataFrame()
    for dateTime in dateTimeRangeFromGivenDateTime:
        dateString=datetime.strftime(dateTime,'%Y-%m-%d')
        totalRainfall=probabilisticCumulativeRainfall(dateTime,hourThresholdDict,hourList)
        intensityThresholdDataframe[dateString]=totalRainfall
        # print(intensityThresholdDataframe)



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
        percentageList=[round(i/51,2)*100 for i in hourlyDistributionList[:-1]]
        dateWiseProbabilityDistributionDictt[dateString]=percentageList
    # print({dateString:[round(i/51,2)*100 for i in hourlyDistributionList[:-1]]})
        # print(allModelDataFrameList[modelIndex].loc[[dateString]])

probabilityDataframe=pd.DataFrame(dateWiseProbabilityDistributionDictt)
probabilityDataframe.insert(0,'Hours',hourList,True)
thresholds=list(hourThresholdDict.values())
probabilityDataframe.insert(1,'Thresholds',thresholds,True)

print(probabilityDataframe)