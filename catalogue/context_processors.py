from catalogue.roles import ROLE_PRODUCER, has_role


def business_roles(request):
    user = request.user
    return {
        'can_moderate_reviews': (
            user.is_authenticated
            and (user.is_staff or has_role(user, ROLE_PRODUCER))
        ),
    }
