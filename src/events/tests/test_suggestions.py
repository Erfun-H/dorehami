from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError

from events.models import Event, Participation, Suggestion


@pytest.mark.django_db
def test_suggestion_requires_a_time_and_trimmed_location(user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    author = Participation.objects.get(event=event, user=organizer)

    suggestion = Suggestion(
        event=event,
        author=author,
        proposed_at=None,
        location="   ",
    )
    with pytest.raises(ValidationError) as exc:
        suggestion.full_clean()
    assert "proposed_at" in exc.value.message_dict
    assert "location" in exc.value.message_dict


@pytest.mark.django_db
def test_suggestion_stores_trimmed_location_and_optional_description(user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    author = Participation.objects.get(event=event, user=organizer)
    when = datetime(2026, 10, 24, 18, 30, tzinfo=UTC)

    suggestion = Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=when,
        location="  The park  ",
        description="  Bring dessert  ",
    )

    assert suggestion.location == "The park"
    assert suggestion.description == "Bring dessert"
    assert suggestion.created_at is not None
    assert suggestion.updated_at is not None


@pytest.mark.django_db
def test_suggestion_author_must_belong_to_the_same_event(user_factory):
    organizer = user_factory(email="organizer@example.com")
    other = user_factory(email="other@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    other_event = Event.objects.create(organizer=other, title="Other")
    foreign_author = Participation.objects.get(event=other_event, user=other)

    suggestion = Suggestion(
        event=event,
        author=foreign_author,
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="The park",
    )
    with pytest.raises(ValidationError) as exc:
        suggestion.full_clean()
    assert "author" in exc.value.message_dict
