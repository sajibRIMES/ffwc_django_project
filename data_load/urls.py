from django.urls import path,include
from rest_framework import routers
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import os

from data_load import views
from data_load.views import forecast_waterlevel_by_station,five_days_forecast_waterlevel
from data_load.views import rainfall_by_station,rainfall_by_station_and_date,rainfall_sum_by_station_and_year,rainfall_avg_by_station_and_year
from data_load.views import observed_waterlevel_by_station,observed_waterlevel_by_station_and_date,observed_waterlevel_sum_by_station_and_year,observed_waterlevel_max_by_station_and_year

from data_load.views import station_by_id,station_by_name
from data_load.views import indian_station_by_id ,indian_station_by_name

from data_load.views import medium_range_forecast_waterlevel_by_station,observed_for_medium_range_forecast_waterlevel_by_station


from data_load.views import feedback
from data_load.views import home

from django.contrib import admin

from .converters import FloatUrlParameterConverter


router = routers.DefaultRouter()
router.register(r'update-date',views.updateDateViewSet,basename='update')
router.register(r'experimental-update-date',views.experimentalUpdateDateViewSet,basename='update-experimental')
router.register(r'stations',views.stationViewSet,basename='stations')
router.register(r'stations-2023',views.station2023ViewSet,basename='stations-2023')
router.register(r'station-info',views.stationInfoViewSet,basename='station-info')
router.register(r'rainfall-stations',views.rainfallStationsViewSet,basename='rainfall-station-info')


router.register(r'observed',views.observedWaterlevelViewSet,basename='observed')
router.register(r'modified-observed',views.modifiedObservedViewSet,basename='modified-observed')
router.register(r'recent-observed',views.recentObservedWaterlevelViewSet,basename='recent-observed')
router.register(r'morning-observed',views.morningWaterlevelViewSet,basename='morning-observed')
router.register(r'afternoon-observed',views.afternoonWaterlevelViewSet,basename='afternoon-observed')


router.register(r'three-days-observed',views.threeDaysObservedWaterlevelViewSet,basename='three-days-observed')
router.register(r'observed-trend',views.ObservedTrendViewSet,basename='observed-trend')
router.register(r'annotate-observed-trend',views.AnnotatedObservedTrendViewSet,basename='annotae-observed-trend')
# ObservedTrendViewSet
# threeDaysObservedWaterlevelViewSet

router.register(r'forecast',views.forecastWaterlevelViewSet,basename='forecast')
router.register(r'medium-range-forecast',views.experimentalForecastWaterlevelViewSet,basename='medium-range-forecast')
router.register(r'modified-forecast',views.modifiedForecastWaterlevelViewSet,basename='modified-forecast')


router.register(r'observed-rainfall',views.observedRainfallViewSet,basename='rainfall')
router.register(r'three-days-observed-rainfall',views.threeDaysObservedRainfallViewSet,basename='three-days-rainfall')
router.register(r'three-days-observed-rainfall-for-morning-bulletin',views.threeDaysObservedRainfalForMorningBulltetinlViewSet,basename='three-days-rainfall')

router.register(r'feedbacks',views.feedbackViewSet,basename='feedback')
router.register(r'users',views.userViewSet,basename='user')

router.register(r'indian-stations',views.indainStationViewSet,basename='indian-stations'),


urlpatterns = [

    path('home', home, name='home'),
    # path('admin/', admin.site.urls),
    path('', include((router.urls,'data_load'))),

# transboundary_river_data_from_database
    path('trans-river-data-from-database/<slug:st_code>/<slug:end_date>',views.transboundary_river_data_from_database),
    path('trans-river-data-timely/<slug:st_code>/<slug:start_date>/<slug:end_date>',views.transboundary_river_data_timely),

    path('trans-river-data/<slug:st_code>/<slug:start_date>/<slug:end_date>',views.transboundary_river_data),
    path('trans-river-onClick-data/<slug:st_code>',views.transboundary_river_onClick_data),

    # transboundary_river_onClick_data
    
    path('rainfall-by-station/<slug:st_id>',rainfall_by_station),
    path('rainfall-by-station-and-date/<slug:st_id>/<slug:startDate>',rainfall_by_station_and_date),
    path('rainfall-sum-by-station-and-year/<slug:st_id>/<slug:year>',rainfall_sum_by_station_and_year),
    path('rainfall-avg-by-station-and-year/<slug:st_id>/<slug:year>',rainfall_avg_by_station_and_year),

    # seven_days_observed_waterlevel_by_station
    path('observed-waterlevel-by-station/<slug:st_id>/',observed_waterlevel_by_station),
    path('seven-days-observed-waterlevel-by-station/<slug:st_id>/',views.seven_days_observed_waterlevel_by_station),
    path('observed-waterlevel-trend-by-station/<slug:st_id>/',views.observed_waterlevel_trend_by_station),
    # 
# observed_waterlevel_by_station_and_today

    path('observed-waterlevel-by-station-today/<slug:st_id>/<slug:startDate>',views.observed_waterlevel_by_station_and_today),
    path('observed-waterlevel-by-station-and-date/<slug:st_id>/<slug:startDate>',observed_waterlevel_by_station_and_date),
    path('observed-waterlevel-sum-by-station-and-year/<slug:st_id>/<slug:year>',observed_waterlevel_sum_by_station_and_year),
    path('observed-waterlevel-max-by-station-and-year/<slug:st_id>/<slug:year>',observed_waterlevel_max_by_station_and_year),



    path('forecast-waterlevel-by-station/<slug:st_id>/',forecast_waterlevel_by_station),
    path('five-days-forecast-waterlevel/',five_days_forecast_waterlevel),
    path('five-days-forecast-waterlevel-24-hours/',views.five_days_forecast_waterlevel_24_hours),
    path('seven-days-forecast-waterlevel-24-hours/',views.seven_days_forecast_waterlevel_24_hours),
    path('ten-days-forecast-waterlevel-24-hours/',views.ten_days_forecast_waterlevel_24_hours),

    path('seven-days-forecast-waterlevel-by-station/<slug:st_id>/',views.seven_days_forecast_waterlevel_by_station),

    # seven_days_forecast_waterlevel

# SevenDaysForecastWaterlevelByStation
    path('medium-range-forecast-by-station/<slug:st_id>/',medium_range_forecast_waterlevel_by_station),
    path('observed-for-medium-range-forecast-by-station/<slug:st_id>/',observed_for_medium_range_forecast_waterlevel_by_station),
# observed_for_medium_range_forecast_waterlevel_by_station

    path('short-range-station/',views.short_range_station),
    path('medium-range-station/',views.medium_range_station),

    path('station-by-id/<slug:station_id>/',station_by_id),
    path('station-by-name/<slug:station_name>/',station_by_name),

    path('station-by-basin/<slug:basin_order>/',views.station_by_basin),
    path('station-by-division/<slug:division>/',views.station_by_division),


    path('short-range-station-by-basin/<slug:basin_order>/',views.short_range_station_by_basin),
    path('medium-range-station-by-basin/<slug:basin_order>/',views.medium_range_station_by_basin),

    path('short-range-station-by-division/<slug:division>/',views.short_range_station_by_division),
    path('medium-range-station-by-division/<slug:division>/',views.medium_range_station_by_division),


    path('create-feedback/<slug:name>/<slug:email>/<slug:comments>', views.create_feedback, name='add-feedback'),
    path('feedback/', views.feedback, name='create-feedback'),

    path('profile/',views.profile, name='Profiles'),
    path('indian-station-by-id/<slug:station_id>/',indian_station_by_id),
    path('indian-station-by-name/<slug:station_name>/',indian_station_by_name),
    path('indian-station-by-code/<slug:station_code>/',views.indian_station_by_code),


    path('user-ffwc-stations/',views.UserFfwcStationsList.as_view()),
    path('user-ffwc-stations/<int:pk>',views.UserFfwcStationsDetails.as_view()),

    path('insert-user-ffwc-stations',views.InsertUserStationView.as_view()),
    path('get-delete-id-from-profile/<int:profile_id>/<int:station_id>',views.DeleteProfileID,name='delete-profile-id'),
    path('delete-user-ffwc-stations/<int:pk>',views.deleteProfileStationsByUserId,name='delete-stations'),

    path('insert-user-indian-stations',views.InsertUserIndianStationView.as_view()),
    path('get-delete-id-from-indian-profile/<int:profile_id>/<int:station_id>',views.DeleteIndianProfileID,name='delete-indian-profile-id'),
    path('delete-user-indian-stations/<int:pk>',views.deleteProfileIndianStationsByUserId,name='delete-indian-stations'),
    path('celery-progress/', include('celery_progress.urls')),  # add this line (the endpoint is configurable)

    
    # Flood Prediction URLs
    
    path('predict-flash-flood/<int:month>/<int:day>/<int:hour>/<float:diff1>/<float:diff2>/<float:diff3>/<float:diff4>',views.PredictFlood,name='predict-flood'), 

    # Flash Flood URLs



    path('update-threshold/<str:hourThresholdDict>',views.updateBasinThreshold,name='update-basin-threshold'),
    path('update-threshold-list/<str:hourThresholdDictList>',views.updateBasinThresholdList,name='update-basin-threshold'),


    path('cambodia-flash-flood/<slug:forecast_date>/<int:basin_id>',views.CambodiaFlashFlood,name='cambodia-flash-flood'),
    path('cambodia-probabilistic-flash-flood/<slug:givenDate>/<int:basin_id>',views.CambodiaProbabilisticFlashFlood,name='cambodia-probabilistic-flash-flood'),


    path('basin-wise-flash-flood/<slug:forecast_date>/<int:basin_id>',views.FlashFlood,name='basin-flash-flood'),
    path('probabilistic-flash-flood/<slug:givenDate>/<int:basin_id>',views.ProbabilisticFlashFlood,name='probabilistic-flash-flood'),

    # New URL for Flash Flood Predictions from Database

    path('new-basin-wise-flash-flood/<slug:forecast_date>/<int:basin_id>',views.NewFlashFlood,name='new-basin-flash-flood'),
    path('new-probabilistic-flash-flood/<slug:givenDate>/<int:basin_id>',views.NewProbabilisticFlashFlood,name='new-probabilistic-flash-flood'),



    path('user-defined-basin/<str:lat>/<str:lng>',views.UserDefinedBasin,name='user-defined-basin'),
    path('flow-path/<str:lat>/<str:lng>',views.FlowPath,name='flow-path'),
    path('sub-basin-precipitation/<str:lat>/<str:lng>',views.SubBasinPrecipiation,name='sub-basin-precipitation'),

] 


# from django.conf import settings
# from django.conf.urls.static import static
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# InsertUserIndianStationView