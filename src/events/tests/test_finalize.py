from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError

from events.models import Agreement, Event, Participation, Suggestion
from events.services import finalize_event


def suggest(event, location):
    author = Participation.objects.get(event=event, user=event.organizer)
    return Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location=location,
    )


@pytest.mark.django_db
def test_organizer_finalizes_the_unique_highest_suggestion(user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    winner = suggest(event, "Park")
    suggest(event, "Cafe")
    Agreement.objects.create(
        event=event,
        suggestion=winner,
        participant=Participation.objects.create(event=event, user=invitee),
    )

    finalize_event(event, organizer, winner.pk)
    event.refresh_from_db()

    assert event.status == Event.Status.FINALIZED
    assert event.final_suggestion == winner


@pytest.mark.django_db
def test_organizer_agreement_alone_cannot_finalize(user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    suggestion = suggest(event, "Park")
    Agreement.objects.create(
        event=event,
        suggestion=suggestion,
        participant=Participation.objects.get(event=event, user=organizer),
    )

    with pytest.raises(ValidationError):
        finalize_event(event, organizer, suggestion.pk)
    event.refresh_from_db()
    assert event.status == Event.Status.ACTIVE


@pytest.mark.django_db
def test_tie_requires_one_of_the_tied_suggestions(user_factory):
    organizer = user_factory(email="organizer@example.com")
    first_guest = user_factory(email="one@example.com")
    second_guest = user_factory(email="two@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    park = suggest(event, "Park")
    cafe = suggest(event, "Cafe")
    Agreement.objects.create(
        event=event,
        suggestion=park,
        participant=Participation.objects.create(event=event, user=first_guest),
    )
    Agreement.objects.create(
        event=event,
        suggestion=cafe,
        participant=Participation.objects.create(event=event, user=second_guest),
    )

    with pytest.raises(ValidationError):
        finalize_event(event, organizer, None)
    finalize_event(event, organizer, cafe.pk)
    event.refresh_from_db()
    assert event.final_suggestion == cafe


@pytest.mark.django_db
def test_non_organizer_cannot_finalize(user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    suggestion = suggest(event, "Park")
    Agreement.objects.create(
        event=event,
        suggestion=suggestion,
        participant=Participation.objects.create(event=event, user=invitee),
    )

    with pytest.raises(PermissionError):
        finalize_event(event, invitee, suggestion.pk)
