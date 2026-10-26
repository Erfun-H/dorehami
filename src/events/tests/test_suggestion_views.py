from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse

from events.models import Agreement, Event, Participation, Suggestion

TEHRAN = ZoneInfo("Asia/Tehran")


def suggestion_url(event):
    return reverse("suggestion-create", args=[event.invite_token])


def edit_url(event, suggestion):
    return reverse("suggestion-edit", args=[event.invite_token, suggestion.pk])


def delete_url(event, suggestion):
    return reverse("suggestion-delete", args=[event.invite_token, suggestion.pk])


@pytest.mark.django_db
def test_participant_creates_a_suggestion_attributed_to_their_participation(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(organizer)

    response = client.post(
        suggestion_url(event),
        {
            "proposed_at": "1405-08-02 18:30",
            "location": "  The park  ",
            "description": "Bring dessert",
        },
    )

    suggestion = Suggestion.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("event-detail", args=[event.invite_token])
    assert suggestion.author.user == organizer
    assert suggestion.location == "The park"
    assert suggestion.proposed_at == datetime(2026, 10, 24, 18, 30, tzinfo=TEHRAN)
    assert Agreement.objects.count() == 0


@pytest.mark.django_db
def test_entered_times_round_trip_through_tehran_time(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(organizer)

    client.post(
        suggestion_url(event),
        {"proposed_at": "1405-08-02 18:30", "location": "Cafe"},
    )

    suggestion = Suggestion.objects.get()
    assert suggestion.proposed_at == datetime(2026, 10, 24, 15, 0, tzinfo=UTC)
    page = client.get(reverse("event-detail", args=[event.invite_token]))
    assert "18:30" in page.content.decode()


@pytest.mark.django_db
def test_edit_form_is_prefilled_with_the_suggestion_values(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    Suggestion.objects.create(
        event=event,
        author=Participation.objects.get(event=event, user=organizer),
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="The park",
        description="Bring dessert",
    )
    client.force_login(organizer)

    response = client.get(reverse("event-detail", args=[event.invite_token]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'name="location" value="The park"' in content
    assert 'value="1405-08-02 22:00:00"' in content
    assert "Bring dessert</textarea>" in content


@pytest.mark.django_db
def test_blank_location_creates_no_suggestion(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(organizer)

    response = client.post(
        suggestion_url(event),
        {"proposed_at": "1405-08-02 18:30", "location": "   "},
    )

    assert response.status_code == 200
    assert Suggestion.objects.count() == 0
    assert "location" in response.context["suggestion_form"].errors


@pytest.mark.django_db
def test_only_the_author_can_edit_and_editing_keeps_agreements(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    author_user = user_factory(email="author@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    author = Participation.objects.create(event=event, user=author_user)
    suggestion = Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="Park",
    )
    Agreement.objects.create(
        event=event,
        suggestion=suggestion,
        participant=Participation.objects.get(event=event, user=organizer),
        )
    client.force_login(organizer)

    forbidden = client.post(
        edit_url(event, suggestion),
        {"proposed_at": "1405-08-03 19:00", "location": "Cafe"},
    )
    assert forbidden.status_code == 403
    suggestion.refresh_from_db()
    assert suggestion.location == "Park"

    client.force_login(author_user)
    allowed = client.post(
        edit_url(event, suggestion),
        {"proposed_at": "1405-08-03 19:00", "location": "Cafe"},
    )
    assert allowed.status_code == 302
    suggestion.refresh_from_db()
    assert suggestion.location == "Cafe"
    assert Agreement.objects.filter(suggestion=suggestion).count() == 1


@pytest.mark.django_db
def test_author_or_organizer_can_delete_and_deletion_removes_agreements(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    author_user = user_factory(email="author@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    author = Participation.objects.create(event=event, user=author_user)
    suggestion = Suggestion.objects.create(
        event=event,
        author=author,
        proposed_at=datetime(2026, 10, 24, 18, 30, tzinfo=UTC),
        location="Park",
    )
    Agreement.objects.create(event=event, suggestion=suggestion, participant=author)
    client.force_login(organizer)

    response = client.post(delete_url(event, suggestion))

    assert response.status_code == 302
    assert Suggestion.objects.count() == 0
    assert Agreement.objects.count() == 0


@pytest.mark.django_db
def test_non_participant_cannot_create_a_suggestion(client, user_factory):
    organizer = user_factory(email="organizer@example.com")
    outsider = user_factory(email="outsider@example.com")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    client.force_login(outsider)

    response = client.post(
        suggestion_url(event),
        {"proposed_at": "2026-10-24T18:30", "location": "Cafe"},
    )

    assert response.status_code == 403
    assert Suggestion.objects.filter(event=event).count() == 0
