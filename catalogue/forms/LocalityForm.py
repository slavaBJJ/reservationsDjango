from django import forms

from catalogue.models import Locality


class LocalityForm(forms.ModelForm):
    postal_code = forms.CharField(
        label='Code postal',
        max_length=6,
        required=True,
    )

    class Meta:
        model = Locality
        fields = ['postal_code', 'locality']
        labels = {'locality': 'Localité'}
