from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.urls import re_path as url

from django.apps import apps
from rest_framework import routers

from ffwc_django_project.views import home
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from .views import MyTokenObtainPairView

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

admin.sites.AdminSite.site_header = '@dmin'
admin.sites.AdminSite.site_title = 'Administrator Panel (FFWC)'
admin.sites.AdminSite.index_title = ''

# from ffwc_django_project.views import cors_serve

urlpatterns = [
    
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('data_load/',include('data_load.urls')),
    path('earthEngine/',include('earthEngine.urls')),

    path('user-auth/',include('userauth.urls')),
    path('file_uploads/', include('fileuploads.urls')),
    
    # added by SHAIF
    path('api/app_email/', include('app_emails.urls')),
    path('api/app_subscriptions/', include('app_subscriptions.urls')),
    path('api/app_dissemination/', include('app_dissemination.urls')),
    
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
