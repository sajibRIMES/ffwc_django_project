from datetime import datetime,timedelta
import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray
import shapely
import netCDF4
import math
import sys
import numpy as np

# dataset=xr.open_dataset('forecast/27032024.nc')
# print(dataset['cp'])

# print ("The name of this script is %s" % (sys.argv[0]))

stationDict={ 1:'khaliajhuri', 2:'gowainghat', 3:'dharmapasha'}
    
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



givenDate = sys.argv[1]
basin_id=int(sys.argv[2])
stationName=stationDict[basin_id]
hourThresholdDict=stationThresholds[basin_id]
indexedHourThresholdDict=stationThresholdsList[basin_id]

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
        else : downloadDay=str(downloadDay)
        dowanloadFileName=str(downloadYear)+downloadDay+'.nc'

        fileNameList.append(dowanloadFileName)
    
    return fileNameList

def computeDailyBasinWiseMeanPrecipitation(fileName,dailyPrecipitationDict):
    
    stationGDF=gpd.read_file(f'floodForecastStations/{stationName}.json',crs="epsg:4326")

    dataset=xr.open_dataset(f"observed/{fileName}")
    dataset.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    dataset.rio.write_crs("epsg:4326", inplace=True)
    basinClipped = dataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)


    observedDate=basinClipped.indexes['time'][0].strftime('%Y-%m-%d')
    # print('File Name: ',fileName,'Observed Date: ', observedDate)


    weights = np.cos(np.deg2rad(basinClipped.lat))
    weights.name = "weights"
    rainfall_weighted = basinClipped.weighted(weights)
    weighted_mean = rainfall_weighted.mean(("lon", "lat"))
    meanPrecipitation=weighted_mean['precipitation'].values.tolist()[0]

    dailyPrecipitationDict[observedDate]=meanPrecipitation

    return dailyPrecipitationDict

def generateObservedDataframe(dailyPrecipitationDict):

    dateList=list(dailyPrecipitationDict.keys())
    rainfallList=list(dailyPrecipitationDict.values())
    dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
    observedRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
    observedRainfallDF.sort_values(by='Date',inplace=True)
    observedRainfallDF.reset_index(drop=True,inplace=True)

    return observedRainfallDF



def computeBasinWiseForecast():

    stationGDF=gpd.read_file(f'floodForecastStations/{stationName}.json',crs="epsg:4326")

    dateString = givenDate[8:10]+givenDate[5:7]+givenDate[:4]

    dateToday=datetime.now()
    # dateString = dateToday.strftime('%d')+dateToday.strftime('%m')+str(dateToday.year)
    fileName=dateString+'.nc'


    forecastDataset=xr.open_dataset(f'forecast/{fileName}')
    forecastDataset.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
    forecastDataset.rio.write_crs("epsg:4326", inplace=True)
    clippedForecast = forecastDataset.rio.clip(stationGDF.geometry, stationGDF.crs, drop=True)

    dateList=list(clippedForecast.indexes['time'].strftime('%Y-%m-%d %H:%M:%S'))
    # dateList=list(clippedForecast.indexes['time'].strftime('%Y-%m-%d'))
    
    forecastPrecipitationDict={}
    dateIndex=0

    for day in range(0,len(dateList),4):
        totalPrecipitation=0
        thisDay=dateList[day]
        # print('This Day: ',thisDay[:11])
        oneDayData=clippedForecast.sel(time=thisDay[:11])

        weights = np.cos(np.deg2rad(oneDayData.latitude))
        weights.name = "weights"
        rainfall_weighted = oneDayData.weighted(weights)
        weighted_mean = oneDayData.mean(("longitude", "latitude"))
        
        meancpValue=weighted_mean['cp'].values.tolist()
        meanlspValue=weighted_mean['lsp'].values.tolist()

        # print('Mean CP Value ', np.nansum(meancpValue))
        # print('Mean LSP Value: ', np.nansum(meanlspValue))
        
        # cpValue=oneDayData['cp'].mean().values.tolist()
        # lspValue=oneDayData['lsp'].mean().values.tolist()

        totalPrecipitation= np.nansum(meancpValue)+np.nansum(meanlspValue)


        # cpValue=oneDayData['cp'].mean().values.tolist()
        # lspValue=oneDayData['lsp'].mean().values.tolist()
        # totalPrecipitation= cpValue+lspValue
        # if math.isnan(totalPrecipitation):totalPrecipitation=0.00
        forecastPrecipitationDict[dateList[dateIndex]]=totalPrecipitation*1000
        dateIndex=dateIndex+4


    rainfallValues=list(forecastPrecipitationDict.values())
    dateValues=list(forecastPrecipitationDict.keys())
    # print(dateValues)

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





dailyPrecipitationDict={}

fileNameList = generateDownloadFileNameList(2024)
# print(fileNameList)

for fileName in fileNameList:
    try:
        # print(f'Computing Observed for {fileName}')
        dailyPrecipitationDict=computeDailyBasinWiseMeanPrecipitation(fileName,dailyPrecipitationDict)
    except:
        print(f'File {fileName} Does Not Exist')

observedRainfallDF=generateObservedDataframe(dailyPrecipitationDict)
print(observedRainfallDF)

forecastPrecipitationDict=computeBasinWiseForecast()
forecastRainfallDF = generateForecastDataframe(forecastPrecipitationDict)
print(forecastRainfallDF)

rainfallRecords = returnDesiredDataframe(observedRainfallDF,forecastRainfallDF)


print('================================== ================================= ================================== =============================    ')




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
    # dateString=datetime.strftime(i,'%Y-%m-%d')
    # print(i)
    dictRainfall[i]=j




# indexedHourThresholdDict={0:[24,25], 1:[48,40.5], 2:[72,53.5], 3:[120,76], 4:[168,96], 5:[240,123]}
intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['hours','Rain'])
intensityThresholdDataframe


givenDateInDateTime=datetime.strptime(givenDate,'%Y-%m-%d')
noOfDayWithinRange=(rangeEnd-givenDateInDateTime).days
dateTimeRangeFromGivenDateTime=[givenDateInDateTime+timedelta(days=day) for day in range (0,noOfDayWithinRange+1)]


hourList=[24, 48, 72, 120, 168, 240]


def returnCumulativeRainfall(givenDateInDateTime,hourThresholdDict,hourList):
    
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


for dateTime in dateTimeRangeFromGivenDateTime:

    dateString=datetime.strftime(dateTime,'%Y-%m-%d')
    totalRainfall=returnCumulativeRainfall(dateTime,hourThresholdDict,hourList)
    dateString=datetime.strftime(dateTime,'%Y-%m-%d')
    intensityThresholdDataframe[dateString]=totalRainfall


print(intensityThresholdDataframe)
jsonResult=intensityThresholdDataframe.to_json()
# print(jsonResult)


# print(' ===================================================================== Frequency Inttensity ==========================================')
# print(f'Station Name: {stationName}' )

floodFrequencyDict={}
frequencyList=[]

for dateTime in dateTimeRangeFromGivenDateTime:
    dateString=datetime.strftime(dateTime,'%Y-%m-%d')
    frequencyRecord=(intensityThresholdDataframe[dateString]>intensityThresholdDataframe['Rain']).value_counts()
    # print(frequencyRecord)
    frequencyList=list(frequencyRecord.keys())
    if False in frequencyList:floodFrequencyDict[dateString]=0.00
    if True in frequencyList:floodFrequencyDict[dateString]=frequencyRecord[True]/len(intensityThresholdDataframe)

# print(floodFrequencyDict)

dateList=list(floodFrequencyDict.keys())
frequency=list(floodFrequencyDict.values())

probabilityDict={'Date':dateList,'Frequency':frequency}
probabilityDF=pd.DataFrame(probabilityDict)

print(probabilityDF)

