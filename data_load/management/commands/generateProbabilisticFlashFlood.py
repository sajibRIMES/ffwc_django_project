from django.core.management import BaseCommand, CommandError
from django.conf import settings

from rest_framework.response import Response
import os
import math

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

from data_load.models import Probabilistic_Flash_Flood_Forecast

class Command(BaseCommand):

    help='Generate Rainfall Distributon Map by Date'

    def add_arguments(self,parser):
        parser.add_argument('date',type=str, help='date for generating Rainfall Distribution Map')

        
    def handle(self, *args, **kwargs):
        
        try :
            dateInput = kwargs['date']
            # print('Date Input Form Parameter', dateInput)

        except:
            updateDate=datetime.today()-timedelta(days=0)
            dateInput=datetime.strftime(updateDate,'%Y-%m-%d')
            # print('Date Input Without Parameter : ', dateInput)

        self.main(dateInput)  
    
    def generateGeoRainfall(self,dateInput):
        
        # self.open_ssh_tunnel()
        # self.mysql_connect()

        retrievedDF=self.fromSql(dateInput)
        rainfallDF=retrievedDF[['st_id','rainFall']].copy(deep=True)
        rainfallDF.sort_values(by=["st_id"],inplace=True)
        rainfallDF.reset_index(drop=True,inplace=True)
        # print('Rainfall Dataframe ... ')
        # print(rainfallDF)

        json_path='data_load/management/commands/shapes/rfStations.json'
        rainfallStations=pd.read_json(json_path)
        # print('Rainfall Stations ...')
        # print(rainfallStations)

        rainfallStations=rainfallStations.merge(rainfallDF,how='inner',on='st_id')
        geoRainfall = gpd.GeoDataFrame(rainfallStations, 
        geometry=gpd.points_from_xy(rainfallStations.Longitude, rainfallStations.Latitude))
        geoRainfall = geoRainfall.set_crs(4326, allow_override=True)
        # print(geoRainfall)

        self.mysql_disconnect()
        self.close_ssh_tunnel()
        
        return geoRainfall
    
    def generateTiff(self,extent_shapefile,geoRainfall,dateInput):
    
        idw.blank_raster(extent_shapefile)
        blank_filename = extent_shapefile.rsplit('.', 1)[0] + '_blank.tif'
        
        output_resolution=250
        idw.crop_resize(input_raster_filename=blank_filename,
                    extent_shapefile_name=extent_shapefile,
                    max_height_or_width=output_resolution)
        
        resized_raster_name = blank_filename.rsplit('.', 1)[0] + '_resized.tif'
        
        column_name='rainFall'
        power=2
        search_radious=4

        with rasterio.open(resized_raster_name) as baseRasterFile:

            obser_df=geoRainfall[['Station']]
            lons, lats = baseRasterFile.index(
                [lon for lon in geoRainfall.geometry.x],[lat for lat in geoRainfall.geometry.y])
            obser_df['lon_index'] = lons
            obser_df['lat_index'] = lats
            obser_df['data_value'] = geoRainfall[column_name]

            idw_array = baseRasterFile.read(1)
            for x in range(baseRasterFile.height):
                for y in range(baseRasterFile.width):
                    if baseRasterFile.read(1)[x][y] == 32767:
                        continue
                    else:
                        idw_array[x][y] = idw.standard_idw(
                            lon=x,
                            lat=y,
                            longs=obser_df.lon_index,
                            lats=obser_df.lat_index,
                            d_values=obser_df.data_value,
                            id_power=power,
                            s_radious=search_radious)

        #     output_filename = input_point_shapefile.rsplit('.', 1)[0] + '_idw.tif'
        # /var/www/prod/ffwc.rimes.int/assets/geotiff
            output_filename=f'/var/www/prod/ffwc_django/ffwc_django_project/assets/tiffOutput/rainfall_distribution_idw_{dateInput}.tif'
            # output_filename=f'static/tiffOutput/rainfall_distribution_idw_{dateInput}.tif'
            with rasterio.open(output_filename, 'w', **baseRasterFile.meta) as std_idw:
                std_idw.write(idw_array, 1)
    
    def returnRequired(self,basin_id=1):
        
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

    def genObservedDataFrame(self,stationGDF):
    
        observedFileNameList = self.generateObservedFileNameList(2025)
        
        for fileName in observedFileNameList:
            print('Observed File Name List: ', fileName)
            try:
                dailyPrecipitationDict=self.computeDailyProbabilisticMeanPrecipitation(stationGDF,fileName)
            except:
                print(f'File {fileName} Does Not Exist')
                
        observedRainfallDF = self.probabilisticObservedDataframe(dailyPrecipitationDict)

        return observedRainfallDF

    def generateObservedFileNameList(self,downloadYear):
        
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

    def computeDailyProbabilisticMeanPrecipitation(self,stationGDF,fileName,dailyPrecipitationDict={}):

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

    def probabilisticObservedDataframe(self,dailyPrecipitationDict):

        dateList=list(dailyPrecipitationDict.keys())
        rainfallList=list(dailyPrecipitationDict.values())
        dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
        observedRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
        observedRainfallDF.sort_values(by='Date',inplace=True)
        observedRainfallDF.reset_index(drop=True,inplace=True)

        return observedRainfallDF

    def returnModelFilenames(self,givenDate):

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


    def computeProbabilisticForecast(self,stationGDF,folderName,fileName,forecastPrecipitationDict={}):

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
        
    def probabilisticForecastDataframe(self,forecastPrecipitationDict):

        dateList=list(forecastPrecipitationDict.keys())
        rainfallList=list(forecastPrecipitationDict.values())
        dailyRainfallDict={'Date':dateList,'Rainfall':rainfallList}
        forecastRainfallDF=pd.DataFrame.from_dict(dailyRainfallDict,orient='columns')
        forecastRainfallDF.sort_values(by='Date',inplace=True)
        forecastRainfallDF.reset_index(drop=True,inplace=True)

        return forecastRainfallDF

    def probabilisticDesiredDataframe(self,observedRainfallDF,forecastRainfallDF):
        
        requiredDF=pd.concat([observedRainfallDF,forecastRainfallDF])
        requiredDF.reset_index(drop=True,inplace=True)

        return requiredDF

    def returnRequiredDateTime(self,rainfallRecords,givenDate):
    
        rangeStart = rainfallRecords.iloc[0]['Date']
        rangeStart = datetime.strptime(rangeStart,'%Y-%m-%d')
        rangeEnd = rainfallRecords.iloc[len(rainfallRecords)-1]['Date']

        # print(rainfallRecords)

        rangeEnd=datetime.strptime(rangeEnd,'%Y-%m-%d')
        # rangeEnd = rangeEnd - timedelta(days=5)
        # print('Range end in Probabilistic: ', rangeEnd)

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


    def probabilisticCumulativeRainfall(self,givenDateInDateTime,hourThresholdDict,hourList,rangeStart,dictRainfall):

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

    def ProbabilisticFlashFlood(self,givenDate,basin_id ):

        print('Given Date and Basin Id in Probabilistic Flash Flood: ', givenDate, ': ', basin_id)

        # givenDate = dateInput
        # basin_id = basin

        allModelDataFrameList=[]

        hourList,stationName,hourThresholdDict,indexedHourThresholdDict,stationGDF=self.returnRequired(basin_id)



        observedRainfallDF = self.genObservedDataFrame(stationGDF)

        modelFilenameList,folderName = self.returnModelFilenames(givenDate)
        model_no=0

        for fileName in modelFilenameList:

            # print('Ensamble Model File Name: ', fileName)

            forecastPrecipitationDict= self.computeProbabilisticForecast(stationGDF,folderName,fileName)
            forecastRainfallDF = self.probabilisticForecastDataframe(forecastPrecipitationDict)
            rainfallRecords = self.probabilisticDesiredDataframe(observedRainfallDF,forecastRainfallDF)

            rangeStart,dictRainfall,givenDateInDateTime,dateTimeRangeFromGivenDateTime = self.returnRequiredDateTime(rainfallRecords,givenDate)
            intensityThresholdDataframe=pd.DataFrame.from_dict(indexedHourThresholdDict,orient='index',columns=['Hours','Threshold'])
            

            # print('Date Time Range in Probabilistic: ')
            # print(dateTimeRangeFromGivenDateTime)


            modelCountDF=pd.DataFrame()
            for dateTime in dateTimeRangeFromGivenDateTime:
                dateString=datetime.strftime(dateTime,'%Y-%m-%d')
                totalRainfall=self.probabilisticCumulativeRainfall(dateTime,hourThresholdDict,hourList,rangeStart,dictRainfall)
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

        # length = len(allModelDataFrameList)
        # print('All Model DataFrame List ',length)
        # print(allModelDataFrameList)


        dateWiseProbabilityDistributionDictt={}
        hourlyDistributionList=[]

        # print('Date Time Range Later: ', dateTimeRangeFromGivenDateTime)

        # for dateTime in dateTimeRangeFromGivenDateTime[:-1]:
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

        # print(probabilityDataframe)
        jsonResult=probabilityDataframe.to_dict()
        station_id_dict={}
        # context = {'Given Date': givenDate, 'Basin Id':basin_id }
        return jsonResult

    def transformIntoDataFrame(self,data_dict,dateInput,basin_id):

        # Prepare a list to hold the rows of data
        rows = []

        # Fixed station_id

        # Iterate through the dictionary
        for date_key, values in data_dict.items():
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
            forecast = Probabilistic_Flash_Flood_Forecast(
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
            response = self.ProbabilisticFlashFlood(dateInput,basin_id)
            df = self.transformIntoDataFrame(response,dateInput,basin_id)
            self.insert_dataframe(df)

