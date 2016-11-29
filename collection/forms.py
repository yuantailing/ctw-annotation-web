from django import forms
from .models import UserPackage

class UploadPackageFileForm(forms.Form):
    annotations = forms.FileField()
