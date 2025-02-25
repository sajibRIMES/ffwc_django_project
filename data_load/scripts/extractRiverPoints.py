
import os
import json

coordinates = []

# dir_path = os.getcwd()
# river_json_file_path=os.path.join(dir_path,'assets/rivers-level-2.json')

river_json_file_path='/var/www/prod/ffwc_django/ffwc_django_project/assets/rivers-level-2.json'

with open(river_json_file_path, 'r') as file:
    feature_collection = json.load(file)

for feature in feature_collection['features']:
    
    if(feature['geometry'] is not None):
        geom = feature['geometry']
        if geom['type'] in ['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']:
            coords = tuple(geom['coordinates'])
            coordinates.extend(coords)
# print(coordinates)
# content={'points':coordinates}
swapped_coordinates = [[lat, lon] for lon, lat in coordinates]
fname = '/var/www/prod/ffwc_django/ffwc_django_project/assets/river-points.json'
with open(fname, 'w') as f:
    json.dump(swapped_coordinates, f)