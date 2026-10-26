import pytest
from django.urls import reverse

from events.models import Event, Participation


@pytest.mark.django_db
def test_anonymous_event_link_preserves_the_destination(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Friday dinner", details="Secret")

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 302
    assert reverse("login") in response.url
    assert reverse("event-detail", args=[event.invite_token]) in response.url
    assert b"Secret" not in response.content
    assert Participation.objects.filter(event=event).count() == 1


@pytest.mark.django_db
def test_signup_from_an_invitation_returns_the_visitor_as_a_participant(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Friday dinner")
    destination = reverse("event-detail", args=[event.invite_token])

    response = client.post(
        reverse("signup") + f"?next={destination}",
        {
            "email": "invitee@example.com",
            "password": "a-long-unique-passphrase",
            "name": "Invitee",
        },
    )

    assert response.status_code == 302
    assert response.url == destination
    page = client.get(response.url)
    assert page.status_code == 200
    assert Participation.objects.filter(event=event, user__email="invitee@example.com").count() == 1


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
def test_signed_in_user_joins_a_valid_active_event(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com", name="Invitee")
    event = Event.objects.create(organizer=organizer, title="Friday dinner")
    client.force_login(invitee)

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 200
    assert Participation.objects.filter(event=event, user=invitee).count() == 1
    assert b"Invitee" in response.content


@pytest.mark.django_db
def test_event_page_shows_every_participant_name(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    first_guest = user_factory(email="one@example.com", name="First Guest")
    second_guest = user_factory(email="two@example.com", name="Second Guest")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    Participation.objects.create(event=event, user=first_guest)
    Participation.objects.create(event=event, user=second_guest)
    client.force_login(first_guest)

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Organizer" in content
    assert "First Guest" in content
    assert "Second Guest" in content


@pytest.mark.django_db
def test_invalid_token_shows_a_generic_unavailable_page(client, user_factory):
    client.force_login(user_factory(email="invitee@example.com"))

    response = client.get(reverse("event-detail", args=["not-a-real-token"]))

    assert response.status_code == 404
    content = response.content.decode().lower()
    assert "در دسترس نیست" in content
    assert "not-a-real-token" not in content
    assert Event.objects.count() == 0
