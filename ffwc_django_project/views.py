from django.shortcuts import render
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.contrib.staticfiles.views import serve

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView



@api_view(['GET'])
def home(request):

    remoteIP= 'http://ffwc-api.bdservers.site'

    context={
        "user-auth": remoteIP+'/user-auth/',
        'ffwc':remoteIP+'/data_load/',
        'ee':remoteIP+'/earthEngine/',
        'file_uploads':remoteIP+'/file_uploads/'
        }  

    return Response(context)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['firstName']=user.first_name
        token['lastName']=user.last_name
        token['dateJoined']=str(user.date_joined)
        token['lastLogin']=str(user.last_login)

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer


# def cors_serve(request, path, insecure=False, **kwargs):
#     kwargs.pop('document_root')
#     response = serve(request, path, insecure=insecure, **kwargs)
#     response['Access-Control-Allow-Origin'] = '*'
#     return response