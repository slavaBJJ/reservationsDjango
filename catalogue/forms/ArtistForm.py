from django import forms
from catalogue.models import Artist

class ArtistForm(forms.ModelForm):

    firstname = forms.CharField(min_length=2)
    lastname = forms.CharField(min_length=2)


    class Meta:
       model = Artist

       fields = [
           'firstname',
           'lastname',
       ]
