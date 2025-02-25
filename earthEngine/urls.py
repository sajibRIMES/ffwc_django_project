from django.urls import path,include
from rest_framework import routers
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import requests

from earthEngine import views

# router = routers.DefaultRouter()
# router.register(r'users',views.ListUsers.as_view() ,basename='users')


urlpatterns = [
    # path('', include((router.urls,'data_load'))),
    path('', views.ee),
    path('ee_with_params/<slug:before_start>/<slug:before_end>/<slug:after_start>/<slug:after_end>/', views.ee_with_params),
    path('ee_water_area/', views.permanentWater),
]

# permanentWater


from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)