from datetime import UTC, datetime

import pytest
from django.db import IntegrityError, transaction

from events.models import Agreement, Event, Participation, Suggestion


def make_suggestion(event, author, location):
    return Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location=location,
    )


@pytest.mark.django_db
def test_a_participant_has_one_agreement_that_moves(user_factory):
    organizer = user_factory(email="organizer@example.com")
    invitee = user_factory(email="invitee@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    organizer_participation = Participation.objects.get(event=event, user=organizer)
    invitee_participation = Participation.objects.create(event=event, user=invitee)
    first = make_suggestion(event, organizer_participation, "Park")
    second = make_suggestion(event, organizer_participation, "Cafe")

    agreement = Agreement.objects.create(
        event=event,
        suggestion=first,
        participant=invitee_participation,
    )
    created_at = agreement.created_at
    agreement.suggestion = second
    agreement.save()
    agreement.refresh_from_db()

    assert Agreement.objects.filter(event=event, participant=invitee_participation).count() == 1
    assert agreement.suggestion == second
    assert agreement.created_at == created_at
    assert agreement.updated_at >= created_at

    with pytest.raises(IntegrityError), transaction.atomic():
        Agreement.objects.create(event=event, suggestion=first, participant=invitee_participation)


@pytest.mark.django_db
def test_agreement_participant_and_suggestion_must_belong_to_the_event(user_factory):
    organizer = user_factory(email="organizer@example.com")
    other = user_factory(email="other@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    other_event = Event.objects.create(organizer=other, title="Other")
    author = Participation.objects.get(event=event, user=organizer)
    foreign = Participation.objects.get(event=other_event, user=other)
    suggestion = make_suggestion(event, author, "Park")

    agreement = Agreement(event=event, suggestion=suggestion, participant=foreign)
    with pytest.raises(Exception):
        agreement.full_clean()
