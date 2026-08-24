from django import forms
from django.contrib.auth.models import Group

from catalogue.roles import BUSINESS_ROLES


class RoleAssignmentForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(
        label='Rôles métier',
        queryset=Group.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['roles'].queryset = Group.objects.filter(
            name__in=BUSINESS_ROLES,
        ).order_by('name')
        if not self.is_bound:
            self.initial['roles'] = user.groups.filter(name__in=BUSINESS_ROLES)

    def save(self):
        business_groups = Group.objects.filter(name__in=BUSINESS_ROLES)
        self.user.groups.remove(*business_groups)
        self.user.groups.add(*self.cleaned_data['roles'])
        return self.user
