from django import forms

from catalogue.models import Type


class TypeForm(forms.ModelForm):
    class Meta:
        model = Type
        fields = ['type']
        labels = {'type': 'Nom du type artistique'}
