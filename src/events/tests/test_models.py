import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import User
from events.models import Event

pytestmark = pytest.mark.django_db


def make_user(email="organizer@example.com"):
    return User.objects.create_user(
        email=email, password="a-long-unique-passphrase", name="Organizer"
    )


def test_event_requires_a_trimmed_title():
    event = Event(organizer=make_user(), title="   ", details="")
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert "title" in exc.value.message_dict


def test_event_title_is_limited_to_200_characters_after_trimming():
    event = Event(organizer=make_user(), title="  " + ("a" * 201))
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert "title" in exc.value.message_dict


def test_event_accepts_a_trimmed_title_and_starts_active_without_a_final_suggestion():
    event = Event.objects.create(organizer=make_user(), title="  Picnic  ", details="")
    event.refresh_from_db()
    assert event.title == "Picnic"
    assert event.status == Event.Status.ACTIVE
    assert event.invite_token
    assert event.created_at is not None


def test_event_details_are_optional_and_limited_to_5000_characters():
    organizer = make_user()
    event = Event.objects.create(organizer=organizer, title="Picnic")
    assert event.details in {"", None}

    too_long = Event(organizer=organizer, title="Long", details="x" * 5001)
    with pytest.raises(ValidationError) as exc:
        too_long.full_clean()
    assert "details" in exc.value.message_dict


def test_invite_token_is_required_unique_and_unguessable():
    organizer = make_user()
    first = Event.objects.create(organizer=organizer, title="First")
    second = Event.objects.create(organizer=organizer, title="Second")
    assert first.invite_token != second.invite_token
    assert len(first.invite_token) >= 32
    assert not first.invite_token.isdigit()

    with pytest.raises(ValidationError):
        Event(organizer=organizer, title="Missing", invite_token="").full_clean()

    second.invite_token = first.invite_token
    with pytest.raises(IntegrityError), transaction.atomic():
        second.save()


def test_organizer_is_required_and_immutable_after_creation():
    with pytest.raises(ValidationError) as exc:
        Event(title="No organizer").full_clean()
    assert "organizer" in exc.value.message_dict

    organizer = make_user()
    other = make_user("other@example.com")
    event = Event.objects.create(organizer=organizer, title="Picnic")
    event.organizer = other
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert "organizer" in exc.value.message_dict
