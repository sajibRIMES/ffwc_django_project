from django.urls import path,include
from rest_framework import routers
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from userauth import views
from django.urls import path
# from .views import UserDetailAPI

urlpatterns = [
    
    path('', views.hello_auth, name='user'),
    path('user-by-id/<slug:user_id>/',views.user_by_id),
    path('user-status/<str:username>/',views.user_status),
    # path('get-details/<slug:user_id>',views.UserViewset.as_view()),
    path('register',views.RegisterUserAPIView.as_view()),

    path('user-profile/<str:user_id>/',views.user_profile),
    path('profile-id/<str:user_id>/',views.profile_id),   
]

