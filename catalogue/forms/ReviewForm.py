from django import forms

from catalogue.models import Review


class ReviewForm(forms.ModelForm):
    stars = forms.TypedChoiceField(
        label='Note',
        choices=[(value, f'{value}/5') for value in range(1, 6)],
        coerce=int,
    )

    class Meta:
        model = Review
        fields = ['stars', 'review']
        labels = {'review': 'Commentaire'}
        widgets = {
            'review': forms.Textarea(attrs={'rows': 5}),
        }
