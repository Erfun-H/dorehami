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
def test_agreeing_moves_the_participants_only_agreement(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    invitee = user_factory(email="invitee@example.com", name="Invitee")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    invitee_participation = Participation.objects.create(event=event, user=invitee)
    first = make_suggestion(event, "Park", 18)
    second = make_suggestion(event, "Cafe", 19)
    Agreement.objects.create(event=event, suggestion=first, participant=invitee_participation)
    client.force_login(invitee)

    response = client.post(reverse("suggestion-agree", args=[event.invite_token, second.pk]))

    assert response.status_code == 302
    agreement = Agreement.objects.get(participant=invitee_participation)
    assert agreement.suggestion == second
    page = client.get(response.url)
    content = page.content.decode()
    assert "Invitee" in content
    assert "Cafe" in content


@pytest.mark.django_db
def test_a_suggestion_from_another_event_is_not_found(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    other = Event.objects.create(organizer=organizer, title="Other")
    foreign = make_suggestion(other, "Park", 18)
    client.force_login(organizer)

    response = client.post(reverse("suggestion-agree", args=[event.invite_token, foreign.pk]))

    assert response.status_code == 404
    assert Agreement.objects.count() == 0
