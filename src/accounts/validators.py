from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError


class PersianMinimumLengthValidator(MinimumLengthValidator):
    """Same rule as MinimumLengthValidator, but with Persian messages."""

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"رمز عبور باید حداقل {self.min_length} کاراکتر باشد.",
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return f"رمز عبور شما باید حداقل {self.min_length} کاراکتر باشد."
