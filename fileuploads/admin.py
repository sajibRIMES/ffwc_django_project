from django.contrib import admin
from .models import UploadedFile

@admin.register(UploadedFile)
class UploadModelAdmin(admin.ModelAdmin):

    # change_form_template = "data_load/model_file_upload.html"

    list_display = ('file','uploaded_at')

# Register your models here.
