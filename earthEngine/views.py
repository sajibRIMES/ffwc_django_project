from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

import json
import os

import ee
# from oauth2client.service_account import ServiceAccountCredentials

import geopandas as gpd


def initializeEE():
    import ee
    # Aauthorization and Initialization
    # service_account ='transportdss@transport-363010.iam.gserviceaccount.com'
    # credentials = ee.ServiceAccountCredentials(service_account, 'transport-363010-5aa27109c357.json')
    # ee.Initialize(credentials)


    service_account ='angular-ee@angular-ee-402820.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, 'angular-ee-402820-6ae0c92db72f.json')
    ee.Initialize(credentials)

    print('Initialized . . ')

def floodMapping():

    # Setting Shape Path
    absolute_path = os.path.dirname(__file__)
    relative_path='bdShapes/bangladesh-whole.shp'
    assetPath = os.path.join(absolute_path, relative_path)
    # print(assetPath)


    # Reading shape and creating EE Geometry
    bdShape = gpd.read_file(assetPath)
    bdJson = json.loads(bdShape.to_json())
    # geometry = ee.Geometry(ee.FeatureCollection(bdJson))
    geometry = ee.Geometry(ee.FeatureCollection(bdJson).geometry())
    # print('Geometry: ', geometry)

    aoi = ee.FeatureCollection(geometry)
    # print('Aoi: ', type(aoi))

    before_start= '2023-07-01'
    before_end='2023-07-07'

    after_start='2023-07-20'
    after_end='2023-07-27'


    # before_start= before_start
    # before_end=before_end

    # after_start=after_start
    # after_end=after_end

    print(before_start,before_end,after_start,after_end)

    polarization = "VH"
    pass_direction = "ASCENDING"
    difference_threshold = 1.25

    # // Load and filter Sentinel-1 GRD data by predefined parameters 

    collection= ee.ImageCollection('COPERNICUS/S1_GRD')\
    .filter(ee.Filter.eq('instrumentMode','IW'))\
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polarization))\
    .filter(ee.Filter.eq('orbitProperties_pass',pass_direction))\
    .filter(ee.Filter.eq('resolution_meters',10))\
    .filterBounds(aoi)\
    .select(polarization)


    # # // Select images by predefined dates
    before_collection = collection.filterDate(before_start, before_end)
    after_collection = collection.filterDate(after_start,after_end)

    # // Create a mosaic of selected tiles and clip to study area
    before = before_collection.mosaic().clip(aoi)
    after = after_collection.mosaic().clip(aoi)

    # // Apply reduce the radar speckle by smoothing  
    smoothing_radius = 50
    before_filtered = before.focal_mean(smoothing_radius, 'circle', 'meters')
    after_filtered = after.focal_mean(smoothing_radius, 'circle', 'meters')


    # # //------------------------------- FLOOD EXTENT CALCULATION -------------------------------//

    # # // Calculate the difference between the before and after images
    difference = after_filtered.divide(before_filtered)

    # # // Apply the predefined difference-threshold and create the flood extent mask 
    threshold = difference_threshold
    difference_binary = difference.gt(threshold)


    # # // Refine flood result using additional datasets
      
    # # // Include JRC layer on surface water seasonality to mask flood pixels from areas
    # # // of "permanent" water (where there is water > 10 months of the year)
    swater = ee.Image('JRC/GSW1_0/GlobalSurfaceWater').select('seasonality')
    swater_mask = swater.gte(10).updateMask(swater.gte(10))
    
    # # //Flooded layer where perennial water bodies (water > 10 mo/yr) is assigned a 0 value
    flooded_mask = difference_binary.where(swater_mask,0)
    # // final flooded area without pixels in perennial waterbodies
    flooded = flooded_mask.updateMask(flooded_mask)
    
    # # // Compute connectivity of pixels to eliminate those connected to 8 or fewer neighbours
    # # // This operation reduces noise of the flood extent product 
    connections = flooded.connectedPixelCount()  
    flooded = flooded.updateMask(connections.gte(8))
    
    # # // Mask out areas with more than 5 percent slope using a Digital Elevation Model 
    DEM = ee.Image('WWF/HydroSHEDS/03VFDEM')
    terrain = ee.Algorithms.Terrain(DEM)
    slope = terrain.select('slope')
    flood_rasters = flooded.updateMask(slope.lt(5))

#     flood_vectors = flood_rasters.reduceToVectors(
#     scale=10,
#     geometryType="polygon",
#     geometry=aoi,
#     eightConnected=False,
#     bestEffort=True,
#     tileScale=2,
# )
    # roi = aoi.geometry()
    # roi_jsonString=roi.getInfo()


    print('.. Done Flood Mapping .. ')

    # image=flood_rasters.select(['VH'])
    # image=flood_rasters

    # task = ee.batch.Export.image.toAsset(
    # image=image,
    # description='Flood Image of Bangladesh - 2019',
    # assetId='projects/transport-363010/assets/flood-area',  # <> modify these
    # region=aoi,
    # scale=30,
    # crs="EPSG:4326"
    # )
    # task.start()
    # print('Exported')

    # return before_filtered,after_filtered,difference,flood_rasters


        # Compute Flood Extent Area 
    # print('Computing Flood Extent Area in Hector')
    # polarization = "VH"
    # flood_pixelarea = flood_rasters.select(polarization).multiply(ee.Image.pixelArea())
    # flood_stats = flood_pixelarea.reduceRegion(
    #     reducer= ee.Reducer.sum(),              
    #     geometry=aoi,
    #     scale= 10, 
    #     maxPixels= 1e9,
    #     bestEffort= True
    #     )

    # flood_area_ha = flood_stats.getNumber(polarization).divide(10000).round(); 
    # # number2=ee.Number(0)
    # # flood_area_ha.evaluate(function(val){number2.setValue(val+' hectares')})

    # flood_area=flood_area_ha.getInfo()
    # print('Estimated Flood Extent: ',flood_area )

    return flood_rasters
    # return flood_rasters,flood_area


def image_to_mapID(image_name,vis_params):


    ee_image = ee.Image(image_name)
    map_info = ee_image.getMapId(vis_params)


    print('Map Info .. ')
    print(map_info)

    result={'url': map_info['tile_fetcher'].url_format}

    return result

# ffwc_django_project/earthEngine/bdShapes/bangladesh-whole.shp


def initEE():

    # flood_vis_params = {'bands': ['VH'],'min': 0,'max': 1,'palette': ['0000FF']}

    # # before_flood_vis_params = {'min': -25,'max': 0,'palette': ['CD5C5C']}
    # # after_flood_vis_params = {'min': -25,'max': 0,'palette': ['2ECC71']}
    # # difference_flood_vis_params={'min': 0,'max': 2,'palette': ['2ECC71']}

    # initializeEE()
    # # print('Initialized . . ')
    
    # # before_filtered,after_filtered,difference,rasterImage=floodMapping()
    # # rasterImage,flood_area_ha=floodMapping()
    # rasterImage=floodMapping()

    # # Create Raster Tile
    # raster_map_info=rasterImage.getMapId(flood_vis_params)
    # # before_map_info=before_filtered.getMapId(before_flood_vis_params)
    # # after_map_info=after_filtered.getMapId(after_flood_vis_params)
    # # difference_map_info=after_filtered.getMapId(difference_flood_vis_params)


    # # print('Estimated Flood Extent: ',flood_area_ha )

    # result={
    #     'url': raster_map_info['tile_fetcher'].url_format
    #     # 'before_url': before_map_info['tile_fetcher'].url_format,
    #     # 'after_url': after_map_info['tile_fetcher'].url_format,
    #     # 'difference_url': difference_map_info['tile_fetcher'].url_format,
    #     }

    result=''

    return result


result=initEE()

@api_view()
def ee(request):
    return Response(result)

@api_view()
def ee_with_params(request,**kwargs):
    import ee
    # Aauthorization and Initialization
    service_account ='transportdss@transport-363010.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, 'transport-363010-5aa27109c357.json')
    ee.Initialize(credentials)
    print('Initialized . . ')

    before_start=kwargs['before_start']
    before_end=kwargs['before_end']

    after_start=kwargs['after_start']
    after_end=kwargs['after_end']

        # Setting Shape Path
    absolute_path = os.path.dirname(__file__)
    relative_path='bdShapes/bangladesh-whole.shp'
    assetPath = os.path.join(absolute_path, relative_path)
    # print(assetPath)


    # Reading shape and creating EE Geometry
    bdShape = gpd.read_file(assetPath)
    bdJson = json.loads(bdShape.to_json())
    # geometry = ee.Geometry(ee.FeatureCollection(bdJson))
    geometry = ee.Geometry(ee.FeatureCollection(bdJson).geometry())
    # print('Geometry: ', geometry)

    aoi = ee.FeatureCollection(geometry)
    # print('Aoi: ', type(aoi))

    # before_start= '2020-07-20'
    # before_end='2020-07-25'

    # after_start='2020-07-26'
    # after_end='2020-08-01'


    before_start= before_start
    before_end=before_end

    after_start=after_start
    after_end=after_end

    print(before_start,before_end,after_start,after_end)

    polarization = "VH"
    pass_direction = "ASCENDING"
    difference_threshold = 1.25

    # // Load and filter Sentinel-1 GRD data by predefined parameters 

    collection= ee.ImageCollection('COPERNICUS/S1_GRD')\
    .filter(ee.Filter.eq('instrumentMode','IW'))\
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polarization))\
    .filter(ee.Filter.eq('orbitProperties_pass',pass_direction))\
    .filter(ee.Filter.eq('resolution_meters',10))\
    .filterBounds(aoi)\
    .select(polarization)


    # # // Select images by predefined dates
    before_collection = collection.filterDate(before_start, before_end)
    after_collection = collection.filterDate(after_start,after_end)

    # // Create a mosaic of selected tiles and clip to study area
    before = before_collection.mosaic().clip(aoi)
    after = after_collection.mosaic().clip(aoi)

    # // Apply reduce the radar speckle by smoothing  
    smoothing_radius = 50
    before_filtered = before.focal_mean(smoothing_radius, 'circle', 'meters')
    after_filtered = after.focal_mean(smoothing_radius, 'circle', 'meters')


    # # //------------------------------- FLOOD EXTENT CALCULATION -------------------------------//

    # # // Calculate the difference between the before and after images
    difference = after_filtered.divide(before_filtered)

    # # // Apply the predefined difference-threshold and create the flood extent mask 
    threshold = difference_threshold
    difference_binary = difference.gt(threshold)


    # # // Refine flood result using additional datasets
      
    # # // Include JRC layer on surface water seasonality to mask flood pixels from areas
    # # // of "permanent" water (where there is water > 10 months of the year)
    swater = ee.Image('JRC/GSW1_0/GlobalSurfaceWater').select('seasonality')
    swater_mask = swater.gte(10).updateMask(swater.gte(10))
    
    # # //Flooded layer where perennial water bodies (water > 10 mo/yr) is assigned a 0 value
    flooded_mask = difference_binary.where(swater_mask,0)
    # // final flooded area without pixels in perennial waterbodies
    flooded = flooded_mask.updateMask(flooded_mask)
    
    # # // Compute connectivity of pixels to eliminate those connected to 8 or fewer neighbours
    # # // This operation reduces noise of the flood extent product 
    connections = flooded.connectedPixelCount()  
    flooded = flooded.updateMask(connections.gte(8))
    
    # # // Mask out areas with more than 5 percent slope using a Digital Elevation Model 
    DEM = ee.Image('WWF/HydroSHEDS/03VFDEM')
    terrain = ee.Algorithms.Terrain(DEM)
    slope = terrain.select('slope')
    flood_rasters = flooded.updateMask(slope.lt(5))

#     flood_vectors = flood_rasters.reduceToVectors(
#     scale=10,
#     geometryType="polygon",
#     geometry=aoi,
#     eightConnected=False,
#     bestEffort=True,
#     tileScale=2,
# )
    # roi = aoi.geometry()
    # roi_jsonString=roi.getInfo()


    print('.. Done Flood Mapping .. ')

    flood_vis_params = {'bands': ['VH'],'min': 0,'max': 1,'palette': ['0000FF']}
    raster_map_info=flood_rasters.getMapId(flood_vis_params)
    # before_map_info=before_filtered.getMapId(before_flood_vis_params)
    # after_map_info=after_filtered.getMapId(after_flood_vis_params)
    # difference_map_info=after_filtered.getMapId(difference_flood_vis_params)

    result={
        'url': raster_map_info['tile_fetcher'].url_format
        # 'before_url': before_map_info['tile_fetcher'].url_format,
        # 'after_url': after_map_info['tile_fetcher'].url_format,
        # 'difference_url': difference_map_info['tile_fetcher'].url_format,
        }



    # result={'before_start':before_start,'before_end':before_end,'after_start':after_start,'after_end':after_end}

    return Response(result)

@api_view()
def permanentWater(request):

    import ee
    # Aauthorization and Initialization
    service_account ='transportdss@transport-363010.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account, 'transport-363010-5aa27109c357.json')
    ee.Initialize(credentials)
    print('Initialized . . ')

        # Setting Shape Path
    absolute_path = os.path.dirname(__file__)
    relative_path='bdShapes/bangladesh-whole.shp'
    assetPath = os.path.join(absolute_path, relative_path)
    # print(assetPath)


    # Reading shape and creating EE Geometry
    bdShape = gpd.read_file(assetPath)
    bdJson = json.loads(bdShape.to_json())
    # geometry = ee.Geometry(ee.FeatureCollection(bdJson))
    geometry = ee.Geometry(ee.FeatureCollection(bdJson).geometry())
    # print('Geometry: ', geometry)

    aoi = ee.FeatureCollection(geometry)


    dataset = ee.ImageCollection('GLCF/GLS_WATER').filterBounds(aoi)

    print('.. Done Water Mapping .. ')

    dataset=dataset.mosaic().clip(aoi)

    water = dataset.select('water')
    water = water.mask(water.mask().where(water.eq(0),0.0))

    waterVis = {'min': 1.0,'max': 4.0,'palette': ['fafafa', '00c5ff', 'df73ff', '828282', 'cccccc'],}

    water_map_info=water.getMapId(waterVis)
    # # before_map_info=before_filtered.getMapId(before_flood_vis_params)
    # # after_map_info=after_filtered.getMapId(after_flood_vis_params)
    # # difference_map_info=after_filtered.getMapId(difference_flood_vis_params)

    result={
        'url': water_map_info['tile_fetcher'].url_format
        # 'before_url': before_map_info['tile_fetcher'].url_format,
        # 'after_url': after_map_info['tile_fetcher'].url_format,
        # 'difference_url': difference_map_info['tile_fetcher'].url_format,
        }

    # result=''
    
    return Response(result)