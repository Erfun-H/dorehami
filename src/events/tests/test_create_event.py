import pytest
from django.urls import reverse

from accounts.models import User
from events.models import Event, Participation

pytestmark = pytest.mark.django_db


def sign_in(client):
    user = User.objects.create_user(
        email="organizer@example.com",
        password="a-long-unique-passphrase",
        name="Ada Organizer",
    )
    client.force_login(user)
    return user


def test_signed_in_user_creates_an_event_and_receives_its_invitation_url(client):
    organizer = sign_in(client)

    response = client.post(
        reverse("event-create"),
        {"title": "Saturday picnic", "details": "Bring a blanket."},
    )

    event = Event.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("event-detail", args=[event.invite_token])
    assert event.organizer == organizer
    assert event.status == Event.Status.ACTIVE
    assert Participation.objects.filter(event=event, user=organizer).exists()

    page = client.get(response.url)
    assert page.status_code == 200
    invitation = f"http://testserver/events/{event.invite_token}/"
    content = page.content.decode()
    assert invitation in content
    assert event.invite_token not in {str(event.pk), str(event.id)}
    assert "Ada Organizer" in content
    assert "Saturday picnic" in content


def test_blank_title_shows_a_field_error_and_creates_no_event(client):
    sign_in(client)

    response = client.post(reverse("event-create"), {"title": "   ", "details": ""})

    assert response.status_code == 200
    assert Event.objects.count() == 0
    assert "title" in response.context["form"].errors
