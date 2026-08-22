from django import forms

from catalogue.models import Price


class ReservationForm(forms.Form):
    price = forms.ModelChoiceField(
        label='Tarif',
        queryset=Price.objects.none(),
        empty_label=None,
    )
    quantity = forms.IntegerField(
        label='Nombre de places',
        min_value=1,
        max_value=20,
        initial=1,
    )

    def __init__(self, *args, representation, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].queryset = representation.show.prices.order_by(
            'price',
            'type',
        )
