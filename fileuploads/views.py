from django.shortcuts import render

from django.shortcuts import render, redirect
from .models import UploadedFile
from .forms import UploadFileForm

from django.views.generic.edit import FormView
from .forms import FileFieldForm


def upload_and_display_files(request):

    files = UploadedFile.objects.all()

    if request.method == 'POST':
        
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            for uploaded_file in request.FILES.getlist('files'):
                # print('Uploaded Multiple Files')
                UploadedFile.objects.create(file=uploaded_file)
            return redirect('upload_and_display')
    else:
        form = UploadFileForm()

    return render(request, 'upload_and_display.html', {'form': form, 'files': files})

class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "upload_and_display.html"  # Replace with your template.
    success_url = "..."  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        for f in files:
            print('File Uploaded .. ')
            ...  # Do something with each file.
        return super().form_valid()
