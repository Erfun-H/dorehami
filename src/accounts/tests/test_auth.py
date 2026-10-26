import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_signup_signs_in_and_returns_to_a_safe_next_url(client):
    response = client.post(
        reverse("signup") + "?next=/events/new/",
        {
            "email": "ada@example.com",
            "password": "a-long-unique-passphrase",
            "name": "Ada",
        },
    )

    user = User.objects.get(email="ada@example.com")
    assert user.is_active
    assert response.status_code == 302
    assert response.url == "/events/new/"
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_signup_rejects_an_external_next_url(client):
    response = client.post(
        reverse("signup") + "?next=https://evil.example/steal",
        {
            "email": "ada@example.com",
            "password": "a-long-unique-passphrase",
            "name": "Ada",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_login_starts_a_session_and_honors_a_safe_next_url(client, user_factory):
    user_factory(email="ada@example.com", name="Ada")

    response = client.post(
        reverse("login") + "?next=/events/new/",
        {"email": "Ada@Example.com", "password": "a-long-unique-passphrase"},
    )

    assert response.status_code == 302
    assert response.url == "/events/new/"
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        {"email": "missing@example.com", "password": "a-long-unique-passphrase"},
        {"email": "ada@example.com", "password": "wrong-long-passphrase"},
    ],
)
def test_login_failures_share_a_generic_message(client, user_factory, payload):
    user_factory(email="ada@example.com", name="Ada")

    response = client.post(reverse("login"), payload)

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    message = response.context["form"].non_field_errors()[0]
    assert "email" not in message.lower()
    assert "password" not in message.lower()
    assert "inactive" not in message.lower()


@pytest.mark.django_db
def test_inactive_account_gets_the_same_generic_login_failure(client, user_factory):
    user_factory(email="ada@example.com", name="Ada", is_active=False)

    response = client.post(
        reverse("login"),
        {"email": "ada@example.com", "password": "a-long-unique-passphrase"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    message = response.context["form"].non_field_errors()[0].lower()
    assert "inactive" not in message
    assert "password" not in message


@pytest.mark.django_db
def test_invitation_next_survives_failed_login_then_signup_and_joins_event(client, user_factory):
    from events.models import Event, Participation

    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    invitation_url = reverse("event-detail", args=[event.invite_token])

    invitation = client.get(invitation_url)
    assert invitation.status_code == 302
    login_url = invitation.url
    failed = client.post(login_url, {"email": "missing@example.com", "password": "wrong-pass"})
    assert failed.status_code == 200
    assert failed.context["next"] == invitation_url
    signup_url = reverse("signup") + f"?next={failed.context['next']}"
    response = client.post(
        signup_url,
        {"email": "invitee@example.com", "password": "a-long-unique-passphrase", "name": "Invitee"},
    )
    assert response.url == invitation_url
    client.get(response.url)
    assert Participation.objects.filter(event=event, user__email="invitee@example.com").exists()


@pytest.mark.django_db
def test_logout_ends_the_session(client, user_factory):
    client.force_login(user_factory(email="ada@example.com", name="Ada"))

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
