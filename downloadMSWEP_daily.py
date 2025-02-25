from Google import Create_Service
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from datetime import datetime

CLIENT_SECRET_FILE = 'hasanCredentials.json'  # Path to your credentials file
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

# Create the service
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

# Specify the folder ID and the file name to download
folder_id = '1aehP6YDNOO73ab3tvTZet2Sh5uPdG9I_'



# Get the current date
# current_date = datetime.now()

# Get the day number of the year
current_year = datetime.now().year
current_year_str = str(current_year)
day_of_year = datetime.now().timetuple().tm_yday-1
day_of_year_str = f"{day_of_year:03}"

# Generate the filename
# filename = f"{current_year_str+day_of_year_str}.nc"
# print('Generated File Name: ', filename)

# file_name_to_download = '2025048.nc'
file_name_to_download = f"{current_year_str+day_of_year_str}.nc"


# Query to find the specific file in the folder
query = f"'{folder_id}' in parents and name='{file_name_to_download}'"
response = service.files().list(q=query, fields="files(id, name)").execute()
files = response.get('files', [])

if not files:
    print(f'File {file_name_to_download} not found in the specified folder.')
else:
    file_id = files[0].get('id')
    print(f'Downloading {file_name_to_download} with ID: {file_id}')

    # Download the file
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fd=fh, request=request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f'Download progress: {status.progress() * 100:.2f}% for file {file_name_to_download}')

    fh.seek(0)
    # Save the file to the current directory

    with open(os.path.join('./observed',file_name_to_download),'wb') as f:
        f.write(fh.read())
        f.close()

    print(f'Downloaded {file_name_to_download} successfully.')