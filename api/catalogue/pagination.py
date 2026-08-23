from rest_framework.pagination import PageNumberPagination

from catalogue.roles import (
    ROLE_AFFILIATE_FREE,
    ROLE_AFFILIATE_PREMIUM,
    ROLE_AFFILIATE_STARTER,
)


class AffiliatePagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        user = request.user
        group_names = set(user.groups.values_list('name', flat=True))

        if user.is_staff or user.is_superuser or ROLE_AFFILIATE_PREMIUM in group_names:
            maximum = 100
        elif ROLE_AFFILIATE_STARTER in group_names:
            maximum = 25
        elif ROLE_AFFILIATE_FREE in group_names:
            maximum = 10
        else:
            maximum = 10

        requested = request.query_params.get(self.page_size_query_param)
        if requested:
            try:
                return min(max(int(requested), 1), maximum)
            except ValueError:
                pass
        return maximum
