import pytest
from django.db import IntegrityError, transaction

from accounts.models import User
from events.models import Event, Participation

pytestmark = pytest.mark.django_db


def test_creating_an_event_creates_one_organizer_participation():
    organizer = User.objects.create_user(
        email="organizer@example.com",
        password="a-long-unique-passphrase",
        name="Organizer",
    )
    event = Event.objects.create(organizer=organizer, title="Picnic")

    participation = Participation.objects.get(event=event, user=organizer)
    assert participation.joined_at is not None
    assert Participation.objects.filter(event=event).count() == 1

    with pytest.raises(IntegrityError), transaction.atomic():
        Participation.objects.create(event=event, user=organizer)
