ROLE_MEMBER = 'MEMBER'
ROLE_PRODUCER = 'PRODUCER'
ROLE_CRITIC = 'CRITIC'
ROLE_AFFILIATE_FREE = 'AFFILIATE_FREE'
ROLE_AFFILIATE_STARTER = 'AFFILIATE_STARTER'
ROLE_AFFILIATE_PREMIUM = 'AFFILIATE_PREMIUM'

BUSINESS_ROLES = (
    ROLE_MEMBER,
    ROLE_PRODUCER,
    ROLE_CRITIC,
    ROLE_AFFILIATE_FREE,
    ROLE_AFFILIATE_STARTER,
    ROLE_AFFILIATE_PREMIUM,
)

AFFILIATE_ROLES = (
    ROLE_AFFILIATE_FREE,
    ROLE_AFFILIATE_STARTER,
    ROLE_AFFILIATE_PREMIUM,
)


def has_role(user, role):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=role).exists()


def is_producer_for(user, show):
    return (
        has_role(user, ROLE_PRODUCER)
        and show.producers.filter(pk=user.pk).exists()
    )
