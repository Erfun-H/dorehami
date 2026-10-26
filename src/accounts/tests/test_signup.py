import pytest
from django.contrib.auth.hashers import check_password

from accounts.forms import SignUpForm
from accounts.models import User


@pytest.mark.django_db
def test_signup_requires_email_password_and_trimmed_name():
    form = SignUpForm(data={"email": "", "password": "", "name": "   "})

    assert not form.is_valid()
    assert "email" in form.errors
    assert "password" in form.errors
    assert "name" in form.errors


@pytest.mark.django_db
def test_signup_rejects_a_duplicate_email_without_creating_a_user():
    User.objects.create_user(
        email="ada@example.com",
        password="a-long-unique-passphrase",
        name="Ada",
    )

    form = SignUpForm(
        data={
            "email": "Ada@Example.com",
            "password": "another-long-passphrase",
            "name": "Another Ada",
        }
    )

    assert not form.is_valid()
    assert "email" in form.errors
    assert "وارد شوید" in form.errors["email"][0]
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_signup_stores_a_password_hash_and_a_trimmed_name():
    form = SignUpForm(
        data={
            "email": "ada@example.com",
            "password": "a-long-unique-passphrase",
            "name": "  Ada Lovelace  ",
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()
    assert user.email == "ada@example.com"
    assert user.name == "Ada Lovelace"
    assert user.is_active
    assert user.password != "a-long-unique-passphrase"
    assert check_password("a-long-unique-passphrase", user.password)
