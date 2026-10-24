from datetime import UTC, datetime

import pytest
from django.urls import reverse

from events.models import Agreement, Event, Participation, Suggestion
from events.services import finalize_event


def finalized_event(user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    invitee = user_factory(email="invitee@example.com", name="Invitee")
    event = Event.objects.create(organizer=organizer, title="Secret dinner", details="Private")
    suggestion = Suggestion.objects.create(
        event=event,
        author=Participation.objects.get(event=event, user=organizer),
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="The park",
    )
    Agreement.objects.create(
        event=event,
        suggestion=suggestion,
        participant=Participation.objects.create(event=event, user=invitee),
    )
    finalize_event(event, organizer, suggestion.pk)
    return event, organizer, invitee, suggestion


@pytest.mark.django_db
def test_participants_can_read_a_finalized_event_but_cannot_change_it(client, user_factory):
    event, organizer, invitee, suggestion = finalized_event(user_factory)
    client.force_login(invitee)

    page = client.get(reverse("event-detail", args=[event.invite_token]))
    content = page.content.decode()
    assert page.status_code == 200
    assert "Secret dinner" in content
    assert "The park" in content
    assert "Invitee" in content

    change = client.post(
        reverse("suggestion-create", args=[event.invite_token]),
        {"proposed_at": "2026-11-01T18:30", "location": "Cafe"},
    )
    assert change.status_code == 403
    assert Suggestion.objects.filter(event=event).count() == 1


@pytest.mark.django_db
def test_non_participants_see_the_generic_unavailable_page(client, user_factory):
    event, organizer, invitee, suggestion = finalized_event(user_factory)
    outsider = user_factory(email="outsider@example.com")
    client.force_login(outsider)
    before = Participation.objects.filter(event=event).count()

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 404
    content = response.content.decode()
    assert "unavailable" in content.lower()
    assert "Secret dinner" not in content
    assert "Private" not in content
    assert "The park" not in content
    assert Participation.objects.filter(event=event).count() == before


@pytest.mark.django_db
def test_non_organizer_cannot_post_finalization(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    suggestion = Suggestion.objects.create(
        event=event,
        author=Participation.objects.get(event=event, user=organizer),
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="Park",
    )
    Agreement.objects.create(
        event=event,
        suggestion=suggestion,
        participant=Participation.objects.create(event=event, user=invitee),
    )
    client.force_login(invitee)

    response = client.post(
        reverse("event-finalize", args=[event.invite_token]),
        {"suggestion_id": suggestion.pk},
    )

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.status == Event.Status.ACTIVE
