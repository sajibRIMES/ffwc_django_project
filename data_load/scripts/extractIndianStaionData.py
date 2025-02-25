from datetime import date, datetime, timedelta
import urllib.parse
from urllib.parse import quote
from urllib.request import urlopen 
import json
import sys
import os

# # Step 1: Set the path to your Django project
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# # Step 2: Set the Django settings module
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffwc_django_project.settings")

# # Step 3: Initialize Django
# import django
# django.setup()


# queryset = data_load_models.IndianStations.objects.all()
# for results in queryset:
#     print(results.station_name)

dateToday = datetime.now()+timedelta(hours=6)
hourNow = dateToday.strftime("%H")
# hourNow = dateToday.hour
# printing current hour using hour
# class
# print("Current hour ", hourNow)

# station_code=kwargs['st_code']
# start_date=str(kwargs['start_date'])+'T00:00:00.000'
# end_date =str(kwargs['end_date'])+f'T{hourNow}:00:00.000'

station_code_dict={
    
    'Dhubri':'005-LBDJPG',
    'Goalpara':'002-MBDGHY',
    'Pandu':'025-MBDGHY',
    'Guwahati(D.C.Court)':'001-MBDGHY',
}
station_codes=['005-LBDJPG','002-MBDGHY','025-MBDGHY','001-MBDGHY']

station_code=station_codes[0]

start_date='2024-11-16'+'T00:00:00.000'
end_date = '2024-11-17'+'T00:00:00.000'


for station_code in station_codes:

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

        stationCode = data['stationCode']
        data_time = data['id']['dataTime']
        dataTime = datetime.strptime(data_time,'%Y-%m-%dT%H:%M:%S')
        waterlevel = data['dataValue']

        print(stationCode,dataTime,waterlevel)
