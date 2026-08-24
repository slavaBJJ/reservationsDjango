from django import forms

from catalogue.models import Location


class LocationForm(forms.ModelForm):
    website = forms.URLField(label='Site internet', required=False)
    phone = forms.CharField(label='Téléphone', max_length=30, required=False)

    class Meta:
        model = Location
        fields = [
            'slug',
            'designation',
            'address',
            'locality',
            'website',
            'phone',
        ]
        labels = {
            'slug': 'Identifiant URL',
            'designation': 'Nom du lieu',
            'address': 'Adresse',
            'locality': 'Localité',
        }
        help_texts = {
            'slug': 'Valeur unique sans espaces, par exemple theatre-royal.',
        }
