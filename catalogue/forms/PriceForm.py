from django import forms

from catalogue.models import Price


class PriceForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ['type', 'price', 'description', 'end_date']
        labels = {
            'type': 'Nom du tarif',
            'price': 'Prix en euros',
            'description': 'Description',
            'end_date': 'Valable jusqu’au',
        }
        widgets = {'end_date': forms.DateInput(attrs={'type': 'date'})}
