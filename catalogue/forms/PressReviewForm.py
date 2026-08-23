from django import forms

from catalogue.models import PressReview


class PressReviewForm(forms.ModelForm):
    class Meta:
        model = PressReview
        fields = ['show', 'title', 'content', 'url']
        labels = {
            'show': 'Spectacle',
            'title': 'Titre',
            'content': 'Article',
            'url': 'Lien externe',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('content') and not cleaned_data.get('url'):
            raise forms.ValidationError(
                'Ajoutez le texte de l’article ou un lien externe.',
            )
        return cleaned_data
