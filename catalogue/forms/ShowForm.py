from django import forms

from catalogue.models import Show


class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = [
            'slug', 'title', 'description', 'poster_url', 'duration',
            'created_in', 'location', 'bookable', 'prices',
        ]
        labels = {
            'slug': 'Identifiant URL',
            'title': 'Titre',
            'description': 'Description',
            'poster_url': "Nom du fichier de l’affiche",
            'duration': 'Durée (minutes)',
            'created_in': 'Année de création',
            'location': 'Lieu de création',
            'bookable': 'Réservations ouvertes',
            'prices': 'Tarifs disponibles',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'prices': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'slug': 'Valeur unique sans espaces, par exemple mon-spectacle.',
            'poster_url': 'Fichier placé dans catalogue/static/catalogue/images/.',
        }
