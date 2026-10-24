from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string


def generate_invite_token():
    return get_random_string(43)


class Event(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FINALIZED = "finalized", "Finalized"

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organized_events",
    )
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True, default="")
    invite_token = models.CharField(max_length=64, unique=True, default=generate_invite_token)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    final_suggestion = models.ForeignKey(
        "events.Suggestion",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="finalized_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        self.title = (self.title or "").strip()
        self.details = (self.details or "").strip()
        self.invite_token = (self.invite_token or "").strip()
        errors = {}
        if not self.title:
            errors["title"] = "A title is required."
        elif len(self.title) > 200:
            errors["title"] = "The title must be 200 characters or fewer."
        if len(self.details) > 5000:
            errors["details"] = "Details must be 5,000 characters or fewer."
        if not self.invite_token:
            errors["invite_token"] = "An invitation token is required."
        if not self.organizer_id:
            errors["organizer"] = "An organizer is required."
        elif self.pk:
            original = (
                Event.objects.filter(pk=self.pk).values_list("organizer_id", flat=True).first()
            )
            if original and original != self.organizer_id:
                errors["organizer"] = "The organizer cannot be changed."
        if self.status == self.Status.ACTIVE and self.final_suggestion_id:
            errors["final_suggestion"] = "An active event cannot have a final suggestion."
        if self.status == self.Status.FINALIZED and not self.final_suggestion_id:
            errors["final_suggestion"] = "A finalized event requires a final suggestion."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.title = (self.title or "").strip()
        self.details = (self.details or "").strip()
        if not self.invite_token:
            self.invite_token = generate_invite_token()
        if self.pk:
            original = (
                Event.objects.filter(pk=self.pk).values_list("organizer_id", flat=True).first()
            )
            if original and original != self.organizer_id:
                raise ValidationError({"organizer": "The organizer cannot be changed."})
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            Participation.objects.get_or_create(event=self, user_id=self.organizer_id)


class Participation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="events_participation_user_event_unique",
            )
        ]


class Suggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="suggestions")
    author = models.ForeignKey(
        Participation,
        on_delete=models.PROTECT,
        related_name="authored_suggestions",
    )
    proposed_at = models.DateTimeField()
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        self.location = (self.location or "").strip()
        self.description = (self.description or "").strip()
        errors = {}
        if not self.proposed_at:
            errors["proposed_at"] = "A date and time is required."
        if not self.location:
            errors["location"] = "A location is required."
        elif len(self.location) > 200:
            errors["location"] = "The location must be 200 characters or fewer."
        if self.description and len(self.description) > 2000:
            errors["description"] = "The description must be 2,000 characters or fewer."
        if self.author_id and self.event_id and self.author.event_id != self.event_id:
            errors["author"] = "The author must participate in this event."
        if self.pk:
            original = Suggestion.objects.filter(pk=self.pk).values("event_id", "author_id").first()
            if original and original["event_id"] != self.event_id:
                errors["event"] = "The event cannot be changed."
            if original and original["author_id"] != self.author_id:
                errors["author"] = "The author cannot be changed."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.location = (self.location or "").strip()
        self.description = (self.description or "").strip()
        if self.pk:
            original = (
                Suggestion.objects.filter(pk=self.pk).values("proposed_at", "location").first()
            )
            if original and (
                original["proposed_at"] != self.proposed_at or original["location"] != self.location
            ):
                self.updated_at = None
        super().save(*args, **kwargs)


class Agreement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="agreements")
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="agreements")
    participant = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE,
        related_name="agreements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "participant"],
                name="events_agreement_participant_event_unique",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.participant_id and self.event_id and self.participant.event_id != self.event_id:
            errors["participant"] = "The participant must belong to this event."
        if self.suggestion_id and self.event_id and self.suggestion.event_id != self.event_id:
            errors["suggestion"] = "The suggestion must belong to this event."
        if self.pk:
            original = (
                Agreement.objects.filter(pk=self.pk).values("event_id", "participant_id").first()
            )
            if original and original["event_id"] != self.event_id:
                errors["event"] = "The event cannot be changed."
            if original and original["participant_id"] != self.participant_id:
                errors["participant"] = "The participant cannot be changed."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk:
            original_suggestion_id = (
                Agreement.objects.filter(pk=self.pk).values_list("suggestion_id", flat=True).first()
            )
            if original_suggestion_id and original_suggestion_id != self.suggestion_id:
                self.updated_at = None
        super().save(*args, **kwargs)
