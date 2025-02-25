from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions,viewsets, generics

from django.contrib.auth.models import User
from data_load.models import AuthUser, Profile, FfwcStations2023
from data_load import models
from rest_framework.authentication import TokenAuthentication
from .serializers import UserSerializer,RegisterSerializer,AuthUserSerializer

from urllib.parse import unquote


@api_view()
def hello_auth(request):

    return Response({"Hello":'User'})

# Class based view to Get User Details using Token Authentication
class UserViewset(viewsets.ModelViewSet):

    def userById(self,request,**kwargs):

        user_id=int(self.kwargs['user_id'])
        queryset=AuthUser.objects.filter(id=user_id).values()[0]
        return Response( queryset)
    
    def userStatusByUser(self,request,**kwargs):

        username=unquote(self.kwargs['username'])

        try:
            queryset=AuthUser.objects.filter(username=username).values()[0]
            user_status={
                'id':queryset['id'],
                'is_active':queryset['is_active'],
                'is_staff':queryset['is_staff'],
                'is_superuser':queryset['is_superuser']
                }
        
        except IndexError:
            user_status ={}

        return Response(user_status)

        # return Response({"user_status":username})

    def getUserProfileId(self,request,**kwargs):

        user_id=int(self.kwargs['user_id'])
        profile_query= models.DataLoadProfile.objects.filter(user_id=user_id).values()[0]
        profile_id= profile_query['id']

        return Response({'profile_id':profile_id})


    def userProfileByUserId(self,request,**kwargs):

        user_id=int(self.kwargs['user_id'])

        profile_query= models.DataLoadProfile.objects.filter(user_id=user_id).values()[0]
        profile_id= profile_query['id']

        ffwcStationQuery=models.DataLoadProfileUserprofilestations.objects.filter(profile_id=profile_id).values_list('ffwcstations2023_id',flat=True)
        indianStationQuery=models.DataLoadProfileUserprofileindianstations.objects.filter(profile_id=profile_id).values_list('indianstations_id',flat=True)


        list_of_user_station={
            'ffwc_stations':ffwcStationQuery,
            'indian_stations':indianStationQuery,
            }

        return Response(list_of_user_station)

user_by_id=UserViewset.as_view({'get':'userById'})
user_status=UserViewset.as_view({'get':'userStatusByUser'})
user_profile=UserViewset.as_view({'get':'userProfileByUserId'})
profile_id=UserViewset.as_view({'get':'getUserProfileId'})

#Class based view to register user
class RegisterUserAPIView(generics.CreateAPIView):
  permission_classes = (AllowAny,)
  serializer_class = RegisterSerializer