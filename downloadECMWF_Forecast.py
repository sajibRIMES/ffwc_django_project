from datetime import datetime
import subprocess

dateToday=datetime.now()
fileName=dateToday.strftime('%d')+dateToday.strftime('%m')+str(dateToday.year)+'.nc'

subprocess.call([
    'dataex_netcdf_subset.py', 
    '--model_type','ecmwf_hres',
    '--ecmwf_hres_params','cp,lsp',
    '--latbounds','24.68208','25.72625',
    '--lonbounds','90.64792','92.73375',
    '--output', f'forecast/{fileName}'
    ])

      

