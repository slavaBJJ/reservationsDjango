from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseAndSpecialCharacterValidator:
    """Require a password containing an uppercase and a special character."""

    def validate(self, password, user=None):
        errors = []
        if not any(character.isupper() for character in password):
            errors.append(
                ValidationError(
                    _('Le mot de passe doit contenir au moins une majuscule.'),
                    code='password_no_uppercase',
                )
            )
        if not any(
            not character.isalnum() and not character.isspace()
            for character in password
        ):
            errors.append(
                ValidationError(
                    _('Le mot de passe doit contenir au moins un caractère spécial.'),
                    code='password_no_special_character',
                )
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            'Votre mot de passe doit contenir au moins une majuscule '
            'et un caractère spécial.'
        )
