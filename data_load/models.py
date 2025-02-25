from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver


from datetime import datetime

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()


    class Meta:
        managed = False
        ordering = ('id',)
        db_table = 'auth_user'

    def __str__(self):
        return self.name


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class FfwcLastUpdateDate(models.Model):
    last_update_date = models.DateField(unique=True)
    entry_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ffwc_last_update_date'


class FfwcLastUpdateDateExperimental(models.Model):
    last_update_date = models.DateField(unique=True)
    entry_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ffwc_last_update_date_experimental'

class FfwcStations(models.Model):
    coords = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    river = models.CharField(max_length=50)
    basin_order = models.IntegerField()
    basin = models.CharField(max_length=100)
    dangerlevel = models.DecimalField(db_column='dangerLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    riverhighestwaterlevel = models.DecimalField(db_column='riverHighestWaterLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    avglandlevel = models.DecimalField(db_column='avgLandLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    river_chainage = models.CharField(max_length=100, blank=True, null=True)
    division = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    upazilla = models.CharField(max_length=100)
    union = models.CharField(max_length=100)
    long = models.DecimalField(max_digits=10, decimal_places=6)
    order_up_down = models.IntegerField(blank=True, null=True)
    lat = models.DecimalField(max_digits=10, decimal_places=6)
    forecast_observation = models.IntegerField()
    status = models.IntegerField()
    station_order = models.IntegerField(blank=True, null=True)
    medium_range_station = models.IntegerField()
    jason_2_satellie_station = models.IntegerField()
    unit_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ffwc_stations'
        verbose_name = "FFWC Stations"
        verbose_name_plural = "FFWC Stations"
        
    # def __str__(self):
    #     return self.name

class FfwcStations2023(models.Model):
    coords = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    river = models.CharField(max_length=50)
    basin_order = models.IntegerField()
    basin = models.CharField(max_length=100)
    dangerlevel = models.DecimalField(db_column='dangerLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    riverhighestwaterlevel = models.DecimalField(db_column='riverHighestWaterLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    avglandlevel = models.DecimalField(db_column='avgLandLevel', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    river_chainage = models.CharField(max_length=100, blank=True, null=True)
    division = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    upazilla = models.CharField(max_length=100)
    union = models.CharField(max_length=100)
    long = models.DecimalField(max_digits=10, decimal_places=6)
    order_up_down = models.IntegerField(blank=True, null=True)
    lat = models.DecimalField(max_digits=10, decimal_places=6)
    forecast_observation = models.IntegerField()
    status = models.IntegerField()
    station_order = models.IntegerField(blank=True, null=True)
    medium_range_station = models.IntegerField()
    jason_2_satellie_station = models.IntegerField()
    unit_id = models.IntegerField()



    class Meta:
        managed = False
        db_table = 'ffwc_stations_2023'
        verbose_name = "FFWC Stations(2023)"
        verbose_name_plural = "FFWC Stations(2023)"

    # def __str__(self):
    #     return '%d : %s' % (self.unit_id,self.name)


    # def __str__(self):
    #     return self.name

class WaterLevelForecasts(models.Model):
    fc_id = models.AutoField(primary_key=True)
    st_id = models.IntegerField()
    fc_date = models.DateTimeField()
    waterlevel = models.DecimalField(db_column='waterLevel', max_digits=10, decimal_places=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'water_level_forecasts'
        verbose_name = "Waterlevel (Forecast)"
        verbose_name_plural = "Waterlevel (Forecasts)"

class ForecastWithStationDetails(models.Model):
    stationName = models.OneToOneField(WaterLevelForecasts, models.DO_NOTHING,related_name='name',related_query_name='name')
    name = models.TextField()
# Medium Range Experimental Waterlevel Forecast

class WaterLevelForecastsExperimentals(models.Model):
    fc_id = models.AutoField(primary_key=True)
    st_id = models.IntegerField()
    fc_date = models.DateTimeField()
    waterlevel_min = models.DecimalField(db_column='waterLevel_min', max_digits=10, decimal_places=2)  # Field name made lowercase.
    waterlevel_max = models.DecimalField(db_column='waterLevel_max', max_digits=10, decimal_places=2)  # Field name made lowercase.
    waterlevel_mean = models.DecimalField(db_column='waterLevel_mean', max_digits=10, decimal_places=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'water_level_forecast_experimentals'
        verbose_name = "Waterlevel_forecast_experimentals(Forecast)"
        verbose_name_plural = "Waterlevel Forecast Experimentals(Forecasts)"


class WaterLevelObservations(models.Model):

    wl_id = models.AutoField(primary_key=True)
    st_id = models.IntegerField()
    wl_date = models.DateTimeField()
    waterlevel = models.DecimalField(db_column='waterLevel', max_digits=10, decimal_places=2)  # Field name made lowercase.


    # def get_name(self,FfwcStations2023):
    #     name = FfwcStations2023.objects.filter(id=WaterLevelObservations.st_id).values_list('name', flat=True)[0]
    #     return name


    class Meta:
        managed = False
        db_table = 'water_level_observations'
        verbose_name = "Observed Waterlevel"
        verbose_name_plural = "Observed Waterlevels"
        get_latest_by = 'wl_date'

    
    # def __str__(self):
    #     return self.st_id, self.wl_date, self.waterlevel

class MonthlyRainfall(models.Model):
    station_id = models.IntegerField()
    month_serial = models.IntegerField()
    month_name = models.CharField(max_length=15)
    unit = models.CharField(max_length=10, blank=True, null=True)
    max_rainfall = models.DecimalField(max_digits=8, decimal_places=2)
    normal_rainfall = models.DecimalField(max_digits=8, decimal_places=2)
    min_rainfall = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'monthly_rainfall'
        verbose_name = "Monthly Rainfall"
        verbose_name_plural = "Monthly Rainfalls"
        
class RainfallObservations(models.Model):
    rf_id = models.AutoField(primary_key=True)
    st_id = models.IntegerField()
    rf_date = models.DateTimeField()
    rainfall = models.DecimalField(db_column='rainFall', max_digits=8, decimal_places=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'rainfall_observations'
        verbose_name = "Observed Rainfall"
        verbose_name_plural = "Observed Rainfalls"


class FfwcRainfallStations(models.Model):
    name = models.CharField(unique=True, max_length=50)
    title = models.CharField(max_length=50)
    basin_order = models.IntegerField()
    basin = models.CharField(max_length=150)
    unit = models.CharField(max_length=10)
    union = models.CharField(max_length=50, blank=True, null=True)
    upazilla = models.CharField(max_length=50, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    lat_wgs84 = models.DecimalField(max_digits=12, decimal_places=8)
    long_wgs84 = models.DecimalField(max_digits=12, decimal_places=8)
    station_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ffwc_rainfall_stations_old'

    # name = models.CharField(unique=True, max_length=50)
    # basin = models.CharField(max_length=150)
    # division = models.CharField(max_length=50)
    # district = models.CharField(max_length=50, blank=True, null=True)
    # upazilla = models.CharField(max_length=50, blank=True, null=True)
    # lat = models.CharField(max_length=20)
    # long = models.CharField(max_length=20)
    # status = models.IntegerField()
    # unit = models.CharField(max_length=10)

    # class Meta:
    #     managed = False
    #     db_table = 'ffwc_rainfall_stations'

class Feedback(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    comments = models.CharField(max_length=1000)

    class Meta:
        managed = False
        db_table = 'feedback'


# Indian Transboundary Data Table
class IndianStations(models.Model):

    station_name = models.CharField(max_length=100)
    state_name = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    basin_name = models.CharField(max_length=100)
    river_name = models.CharField(max_length=100)

    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)

    division_name = models.CharField(max_length=150, blank=True, null=True)
    type_of_site = models.CharField(max_length=100, blank=True, null=True)

    distance = models.DecimalField(max_digits=10, decimal_places=6,blank=True, null=True)

    within_ganges = models.CharField(max_length=100,blank=True, null=True)
    within_brahmaputra = models.CharField(max_length=100,blank=True, null=True)
    within_meghna = models.CharField(max_length=100,blank=True, null=True)

    station_code = models.CharField(max_length=100)
    dangerlevel = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)  
    warning_level = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)  
    highest_flow_level = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)  


    class Meta:
        managed = False
        db_table = 'indian_stations'
        verbose_name = "Indain Stations"
        verbose_name_plural = "Indian Sations"
    
    def __str__(self):
        return self.station_name

    # def __str__(self):
    #     return '%s - %s' % (self.station_name, self.basin_name)


class IndianWaterLevelObservations(models.Model):
    id = models.BigAutoField(primary_key=True)
    station_id = models.IntegerField()
    station_code = models.CharField(max_length=200)
    data_time = models.DateTimeField()
    waterlevel = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'indian_water_level_observations'
        
# User Profile Data Table
class Profile(models.Model):  
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    userProfileStations = models.ManyToManyField(FfwcStations2023,db_constraint=False)
    userProfileIndianStations = models.ManyToManyField(IndianStations,db_constraint=False)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)
    
    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()



class DataLoadProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'data_load_profile'

class DataLoadProfileUserprofilestations(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile_id = models.BigIntegerField()
    ffwcstations2023_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'data_load_profile_userProfileStations'
        unique_together = (('profile_id', 'ffwcstations2023_id'),)

        
class DataLoadProfileUserprofileindianstations(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile_id = models.BigIntegerField()
    indianstations_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'data_load_profile_userProfileIndianStations'
        unique_together = (('profile_id', 'indianstations_id'),)




def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<current_datetime>/<filename>
    return f'user_{0}/{1}/{2}'.format(instance.user.id, filename)

# Working on File Upload
class UploadModel(models.Model):
    #file field is added in the model
    file = models.FileField(upload_to='uploads/')

    class Meta:
        verbose_name = "Upload File"
        verbose_name_plural = "Upload Files"


# class UploadModelTwo(models.Model):
#     #file field is added in the model
#     file = models.FileField(upload_to='uploads/')

#     class Meta:
#         verbose_name = "Upload File"
#         verbose_name_plural = "Upload Files"


class DataHeader(models.Model):
    web_id = models.IntegerField()
    station = models.CharField(max_length=100)
    data_header = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Data Header"
        verbose_name_plural = "Data Headers"

class FfwcStationInfo(models.Model):
    # id = models.CharField(primary_key=True, max_length=3)
    st_id = models.CharField(db_column='St ID', max_length=8, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    station = models.CharField(db_column='Station', max_length=26, blank=True, null=True)  # Field name made lowercase.
    river = models.CharField(db_column='River', max_length=22, blank=True, null=True)  # Field name made lowercase.
    dl_mmsl_field = models.CharField(db_column='DL (mMSL)', max_length=9, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    pmdl_mmsl_field = models.CharField(db_column='PMDL (mMSL)', max_length=13, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rhwl_mmsl_mpwd_0_46_field = models.CharField(db_column='RHWL mMSL(mPWD -0.46)', max_length=21, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rhwl_mpwd_confirmed = models.CharField(db_column='RHWL (mPWD) Confirmed', max_length=21, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    date_of_rhwl = models.CharField(db_column='Date of RHWL', max_length=12, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    gauge_shift_pwd_msl_field = models.CharField(db_column='Gauge Shift (PWD-MSL)', max_length=21, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    effective_date = models.CharField(db_column='Effective Date', max_length=14, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    latitude = models.CharField(db_column='Latitude', max_length=8, blank=True, null=True)  # Field name made lowercase.
    longitude = models.CharField(db_column='Longitude', max_length=9, blank=True, null=True)  # Field name made lowercase.
    basin = models.CharField(db_column='Basin', max_length=11, blank=True, null=True)  # Field name made lowercase.
    h_division = models.CharField(db_column='H.Division', max_length=10, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    division = models.CharField(db_column='Division', max_length=10, blank=True, null=True)  # Field name made lowercase.
    district = models.CharField(db_column='District', max_length=16, blank=True, null=True)  # Field name made lowercase.
    upazilla = models.CharField(db_column='Upazilla', max_length=18, blank=True, null=True)  # Field name made lowercase.
    union = models.CharField(db_column='Union', max_length=28, blank=True, null=True)  # Field name made lowercase.
    forecast_status = models.CharField(db_column='Forecast Status', max_length=15, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rimes_medium_range = models.CharField(db_column='RIMES Medium Range', max_length=18, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    model_boundary = models.CharField(db_column='Model Boundary', max_length=14, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pre_monsoon = models.CharField(db_column='Pre-Monsoon', max_length=11, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dry = models.CharField(db_column='Dry', max_length=3, blank=True, null=True)  # Field name made lowercase.
    sms_solution_id = models.CharField(db_column='SMS Solution ID', max_length=15, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    fw_data_location = models.CharField(db_column='FW Data Location', max_length=16, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    web_id = models.CharField(db_column='Web-ID', max_length=6, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    ffdata_header = models.CharField(db_column='ffData Header', max_length=23, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'ffwc_station_info'



# Threshold based Flood Forecasting Models

# class ProbabilisticFlashFloodForecast(models.Model):
#     station_id = models.IntegerField()
#     hours = models.IntegerField()
#     thresholds = models.FloatField()
#     date = models.DateField()
#     value = models.FloatField()
#     # def __str__(self):
#     #     return self.name
#     class Meta:
#         managed = False
#         db_table = 'data_load_probabilisticflashfloodforecast'


class Probabilistic_Flash_Flood_Forecast(models.Model):
    prediction_date = models.DateField()
    basin_id = models.IntegerField()
    date = models.DateField()
    hours = models.IntegerField()
    thresholds = models.FloatField()
    value = models.FloatField()

    def __str__(self):
        return self.name

    # class Meta:
    #     managed = False
    #     db_table = 'data_load_probabilistic_flash_flood_forecast'


class Basin_Wise_Flash_Flood_Forecast(models.Model):

    prediction_date = models.DateField()
    basin_id = models.IntegerField()
    date = models.DateField()
    hours = models.IntegerField()
    thresholds = models.FloatField()
    value = models.FloatField()

    def __str__(self):
        return self.name

    # class Meta:
    #     managed = False
    #     db_table = 'data_load_basin_wise_flash_flood_forecast'