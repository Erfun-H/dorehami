import pytest
from django.urls import reverse

from events.models import Event, Participation


@pytest.mark.django_db
def test_signed_in_invitee_joins_once_and_sees_the_event(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Friday dinner")
    client.force_login(invitee)

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 200
    assert b"Friday dinner" in response.content
    assert Participation.objects.filter(event=event, user=invitee).count() == 1

    client.get(reverse("event-detail", args=[event.invite_token]))

    assert Participation.objects.filter(event=event, user=invitee).count() == 1


@pytest.mark.django_db
def test_anonymous_invite_link_asks_for_sign_in_without_creating_participation(
    client, user_factory
):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Friday dinner")

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 302
    assert reverse("login") in response.url
    assert Participation.objects.filter(event=event).count() == 1


@pytest.mark.django_db
def test_invalid_invite_link_shows_an_unavailable_message(client, user_factory):
    invitee = user_factory(email="invitee@example.com")
    client.force_login(invitee)

    response = client.get(reverse("event-detail", args=["not-a-real-invitation"]))

    assert response.status_code == 404
    assert b"unavailable" in response.content.lower()
    assert Event.objects.count() == 0
