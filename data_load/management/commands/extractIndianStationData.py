from django.core.management import BaseCommand, CommandError
from django.conf import settings

from datetime import date, datetime, timedelta
import urllib.parse
from urllib.parse import quote
from urllib.request import urlopen 
import json
import sys
import os

from data_load.models import IndianStations
from data_load.models import IndianWaterLevelObservations

class Command(BaseCommand):

    help='Extract and Update Indian Staion Data'


    def handle(self, *args, **kwargs):

        dateYesterday=datetime.today()
        dateYesterday=datetime.strftime(dateYesterday,'%Y-%m-%d')
        start_date=dateYesterday+'T00:00:00.000'


        dateToday=datetime.today()+timedelta(days=1)
        dateToday=datetime.strftime(dateToday,'%Y-%m-%d')
        end_date=dateToday+'T00:00:00.000'

        print('Start Date: ', start_date, 'End Date: ', end_date )

        self.main(start_date,end_date)
    
    def extractData(self,station_code,start_date,end_date):

        # dateToday = datetime.now()+timedelta(hours=6)
        # hourNow = dateToday.strftime("%H")

        # station_codes=['005-LBDJPG','002-MBDGHY','025-MBDGHY','001-MBDGHY']
        # station_code=station_codes[0]
        # start_date='2018-01-01'+'T00:00:00.000'
        # end_date = '2019-01-01'+'T00:00:00.000'

        queryset = IndianStations.objects.filter(station_code=station_code)
        for results in queryset:
            station_id=results.id



        baseUrl = 'https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/sorted?sort-criteria='
        sortCriteria = quote('{"sortOrderDtos"')+':'+quote('[{"sortDirection"')+':'+quote('"ASC"')+','+ quote('"field"')+':'+quote('"id.dataTime"}]}')
            
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


            
        try:
            with urllib.request.urlopen(url) as response:
                json_data = json.loads(response.read().decode())

            # response = urlopen(url)
            # data = response.read()
            # print(data)
        except urllib.error.HTTPError as e:
            if e.code == 500:
                print("Internal server error occurred!")
            else:
                print(f"An HTTP error occurred: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"A URL error occurred: {e.reason}")


        for data in json_data:

            station_code = data['stationCode']
            data_time = data['id']['dataTime']
            data_time = datetime.strptime(data_time,'%Y-%m-%dT%H:%M:%S')
            waterlevel = data['dataValue']
            
            print(station_id,station_code,data_time,waterlevel)
            new_entry= IndianWaterLevelObservations(station_id=station_id,station_code=station_code,data_time=data_time,waterlevel=waterlevel)
            new_entry.save()  # Save the instance to the database
            print("Data inserted successfully!")


    # def insert_data():
    #     # Create an instance of MyModel
    #     new_entry = MyModel(field1='value1', field2='value2')  # Replace with your model fields and values
    #     new_entry.save()  # Save the instance to the database
    #     print("Data inserted successfully!")

    def main(self,start_date,end_date):
        
        # station_codes=['005-LBDJPG','002-MBDGHY','025-MBDGHY','001-MBDGHY']


        station_codes =[
            '005-LBDJPG',
            '002-MBDGHY',
            '025-MBDGHY',
            '001-MBDGHY',

            "031-UBDDIB",
            "022-UBDDIB",
            "019-UBDDIB",
            "010-UBDDIB",
            "068-UBDDIB",
            "005-UBDDIB",
            "007-UBDDIB",
            "047-LBDJPG",
            "028-LBDJPG",
            "027-LBDJPG",
            "023-LBDJPG",
            "022-LBDJPG",
            "021-LBDJPG",
            "016-LBDJPG",
            "042-LBDJPG",
            "030-LBDJPG",
            "028-MGD5PTN",
            "008-MGD5PTN",
            "025-mgd4ptn",
            "044-MGD4PTN",
            "023-mgd4ptn",
            "006-mgd5ptn",
            "034-MGD5PTN",
            "005-MGD5PTN",
            "004-MGD5PTN",
            "011-MGD5PTN",
            "003-MGD5PTN",
            "027-MGD5PTN",
            "014-MGD5PTN",
            "013-MGD5PTN",
            "046-MGD1LKN",
            "001-MGD5PTN",
            "01-11-01-008",
            "013-MBDGHY",
            "017-MGD3VNS",
            "01-11-13-001",
            "027- MDSIL",
            "01-11-01-006",
            "015-MDSIL",
            "01-11-01-007",
            "028- MDSIL",
            "021-MBDGHY",
            "S014-MDSIL",
            "023-MBDGHY",
            "001-MDSIL",
            "022-MBDGHY",
            "004-mdsil",
            "01-10-18-001",
            "01-10-21-001",
            "01-10-01-001",
            "01-10-02-001",
            "01-10-16-001",
            "01-10-25-001",
            "01-10-15-001",
            "01-10-09-001",
            "001-MIDSHL",
            "002-midshl",
            "012-MDSIL",
            "022-MDSIL",
            "019-MBDGHY",
            "029-MDSIL",
            "023-MDSIL",
            "013-MDSIL",
            "005-mdsil"
            
            ]

        start_date='2024-11-03'+'T00:00:00.000'
        end_date = '2024-11-05'+'T00:00:00.000'

        # station_code=station_codes[0]
        for station_code in station_codes[:1]:
            # print(station_code)
            try:
                self.extractData(station_code,start_date,end_date)
            except:
                continue

        os._exit(0)

