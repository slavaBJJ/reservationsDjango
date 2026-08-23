from rest_framework.permissions import BasePermission, SAFE_METHODS

from catalogue.roles import AFFILIATE_ROLES


class AffiliateCataloguePermission(BasePermission):
    message = 'Un abonnement affilié est nécessaire pour accéder au catalogue API.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if request.method not in SAFE_METHODS:
            return False
        return user.groups.filter(name__in=AFFILIATE_ROLES).exists()
