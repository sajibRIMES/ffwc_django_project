from Google import Create_Service

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.oauth2 import service_account

from googleapiclient.http import MediaIoBaseDownload
import io
import os
import pandas as pd


CLIENT_SECRET_FILE = 'hasanCredentials.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES=['https://www.googleapis.com/auth/drive']


service = Create_Service(CLIENT_SECRET_FILE,API_NAME,API_VERSION,SCOPES)

folder_id ='1QzLe6EX4txOdf8lnY5l-ofLxKInvBgaL'
query = f"parents = '{folder_id}' "
response = service.files().list(pageSize=10,fields="nextPageToken, files(id, name)",q=query).execute()
folderIdResult = response.get('files',[])

id = folderIdResult[1].get('id')

results = service.files().list(q = "'" + id + "' in parents", pageSize=10, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])

file_ids=[]
file_names=[]

for f in range(0, len(items)):
    fId = items[f].get('id')
    file_ids.append(fId)
    fName=items[f].get('name')
    file_names.append(fName)

# print(file_ids,file_names)

for file_id,file_name in zip(file_ids,file_names):

    isFile = os.path.isfile(f'observed/{file_name}')
    if not isFile:

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=fh,request=request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f'Download progress {status.progress()*100} % for File {file_name}')


        fh.seek(0)
        with open(os.path.join('./observed',file_name),'wb') as f:
            f.write(fh.read())
            f.close()
