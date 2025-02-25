from django.urls import path,include
from . import views

urlpatterns = [
   
    # path('',  include('fileuploads.urls')),
    path('', views.upload_and_display_files, name='upload_and_display'),
    path('upload',views.FileFieldFormView.as_view())
]


# from django.conf import settings
# from django.conf.urls.static import static
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)