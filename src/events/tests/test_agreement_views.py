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
def test_agreeing_with_json_returns_rendered_sections(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    invitee = user_factory(email="invitee@example.com", name="Invitee")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    Participation.objects.create(event=event, user=invitee)
    make_suggestion(event, "Park", 18)
    second = make_suggestion(event, "Cafe", 19)
    client.force_login(invitee)

    response = client.post(
        reverse("suggestion-agree", args=[event.invite_token, second.pk]),
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agreed"] is True
    assert "Cafe" in data["suggestions_html"]
    assert "Invitee" in data["suggestions_html"]
    assert Agreement.objects.get(event=event, participant__user=invitee).suggestion == second


@pytest.mark.django_db
def test_agreeing_again_with_the_same_suggestion_withdraws_it(client, user_factory):
    organizer = user_factory(email="organizer@example.com", name="Organizer")
    invitee = user_factory(email="invitee@example.com", name="Invitee")
    event = Event.objects.create(organizer=organizer, title="Dinner")
    Participation.objects.create(event=event, user=invitee)
    suggestion = make_suggestion(event, "Cafe", 19)
    client.force_login(invitee)

    first = client.post(
        reverse("suggestion-agree", args=[event.invite_token, suggestion.pk]),
        HTTP_ACCEPT="application/json",
    )
    second = client.post(
        reverse("suggestion-agree", args=[event.invite_token, suggestion.pk]),
        HTTP_ACCEPT="application/json",
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["agreed"] is True
    assert second.json()["agreed"] is False
    assert "0 موافق" in second.json()["suggestions_html"]
    assert "Invitee" not in second.json()["suggestions_html"]
    assert not Agreement.objects.filter(event=event, participant__user=invitee).exists()


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
