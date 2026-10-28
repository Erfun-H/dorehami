from datetime import UTC, datetime

import pytest
from django.urls import reverse

from events.models import Agreement, Event, Participation, Suggestion


def make_suggestion(event, location, hour):
    author = Participation.objects.get(event=event, user=event.organizer)
    return Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=datetime(2026, 10, 24, hour, 0, tzinfo=UTC),
        location=location,
    )


@pytest.mark.django_db
def test_organizer_sees_the_edit_form(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner", details="Old")
    client.force_login(organizer)

    response = client.get(reverse("event-edit", args=[event.invite_token]))

    assert response.status_code == 200
    assert "Dinner" in response.content.decode()


@pytest.mark.django_db
def test_organizer_updates_title_and_details(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner", details="Old")
    client.force_login(organizer)

    response = client.post(
        reverse("event-edit", args=[event.invite_token]),
        {"title": "Game Night", "details": "Bring snacks"},
    )

    assert response.status_code == 302
    event.refresh_from_db()
    assert event.title == "Game Night"
    assert event.details == "Bring snacks"


@pytest.mark.django_db
def test_finalized_events_cannot_be_edited(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    suggestion = make_suggestion(event, "Cafe", 18)
    Participation.objects.create(
        event=event, user=user_factory(email="guest@example.com")
    )
    guest = Participation.objects.get(event=event, user__email="guest@example.com")
    Agreement.objects.create(event=event, suggestion=suggestion, participant=guest)
    from events.services import finalize_event

    finalize_event(event, organizer, suggestion.pk)
    client.force_login(organizer)

    response = client.post(
        reverse("event-edit", args=[event.invite_token]),
        {"title": "Renamed", "details": ""},
    )

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.title == "Dinner"


@pytest.mark.django_db
def test_only_the_organizer_can_edit_or_delete(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    stranger = user_factory(email="stranger@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(stranger)

    assert client.get(reverse("event-edit", args=[event.invite_token])).status_code == 403
    assert (
        client.post(
            reverse("event-delete", args=[event.invite_token]), {}
        ).status_code
        == 403
    )
    assert Event.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
def test_organizer_deletes_an_active_event_with_everything(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    invitee_participation = Participation.objects.create(event=event, user=invitee)
    suggestion = make_suggestion(event, "Cafe", 18)
    Agreement.objects.create(
        event=event, suggestion=suggestion, participant=invitee_participation
    )
    client.force_login(organizer)

    response = client.post(reverse("event-delete", args=[event.invite_token]))

    assert response.status_code == 302
    assert response.url == reverse("home")
    assert not Event.objects.filter(pk=event.pk).exists()
    assert not Suggestion.objects.filter(pk=suggestion.pk).exists()
    assert not Participation.objects.filter(event=event).exists()
    assert not Agreement.objects.filter(event=event).exists()


@pytest.mark.django_db
def test_organizer_can_delete_a_finalized_event(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    suggestion = make_suggestion(event, "Cafe", 18)
    guest_participation = Participation.objects.create(
        event=event, user=user_factory(email="guest@example.com")
    )
    Agreement.objects.create(
        event=event, suggestion=suggestion, participant=guest_participation
    )
    from events.services import finalize_event

    finalize_event(event, organizer, suggestion.pk)
    client.force_login(organizer)

    response = client.post(reverse("event-delete", args=[event.invite_token]))

    assert response.status_code == 302
    assert not Event.objects.filter(pk=event.pk).exists()
    assert not Suggestion.objects.filter(pk=suggestion.pk).exists()


@pytest.mark.django_db
def test_delete_requires_post(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(organizer)

    response = client.get(reverse("event-delete", args=[event.invite_token]))

    assert response.status_code == 405
    assert Event.objects.filter(pk=event.pk).exists()
