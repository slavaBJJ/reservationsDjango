from django import forms
from django.utils import timezone

from catalogue.models import Representation


class RepresentationForm(forms.ModelForm):
    schedule = forms.DateTimeField(
        label='Date et heure',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
    )

    class Meta:
        model = Representation
        fields = ['schedule', 'location']
        labels = {'location': 'Lieu de la représentation'}

    def clean_schedule(self):
        schedule = self.cleaned_data['schedule']
        if not self.instance.pk and schedule <= timezone.now():
            raise forms.ValidationError('La nouvelle représentation doit être future.')
        return schedule
