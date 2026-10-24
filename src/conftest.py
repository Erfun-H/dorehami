import pytest

from accounts.models import User


@pytest.fixture
def user_password():
    return "a-long-unique-passphrase"


@pytest.fixture
def user_factory(user_password):
    def create(*, email, name=None, password=None, is_active=True):
        user = User.objects.create_user(
            email=email,
            password=password or user_password,
            name=name or email.split("@")[0],
        )
        if not is_active:
            user.is_active = False
            user.save(update_fields=["is_active"])
        return user

    return create
