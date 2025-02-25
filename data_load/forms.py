from django import forms
from data_load import models

class StationChangeListForm(forms.ModelForm):
    # here we only need to define the field we want to be editable
    stations = forms.ModelMultipleChoiceField(queryset=models.FfwcStations2023.objects.all(), required=False)
        