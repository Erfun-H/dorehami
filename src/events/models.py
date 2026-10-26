from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
from django_jalali.db import models as jmodels


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
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        self.title = (self.title or "").strip()
        self.details = (self.details or "").strip()
        self.invite_token = (self.invite_token or "").strip()
        errors = {}
        if not self.title:
            errors["title"] = "عنوان الزامی است."
        elif len(self.title) > 200:
            errors["title"] = "عنوان باید حداکثر ۲۰۰ نویسه باشد."
        if len(self.details) > 5000:
            errors["details"] = "توضیحات باید حداکثر ۵۰۰۰ نویسه باشد."
        if not self.invite_token:
            errors["invite_token"] = "نشانه دعوت الزامی است."
        if not self.organizer_id:
            errors["organizer"] = "میزبان الزامی است."
        elif self.pk:
            original = (
                Event.objects.filter(pk=self.pk).values_list("organizer_id", flat=True).first()
            )
            if original and original != self.organizer_id:
                errors["organizer"] = "میزبان قابل تغییر نیست."
        if self.status == self.Status.ACTIVE and self.final_suggestion_id:
            errors["final_suggestion"] = "دورهمی فعال نمی‌تواند پیشنهاد نهایی داشته باشد."
        if self.status == self.Status.FINALIZED and not self.final_suggestion_id:
            errors["final_suggestion"] = "دورهمی نهایی‌شده به پیشنهاد نهایی نیاز دارد."
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
                raise ValidationError({"organizer": "میزبان قابل تغییر نیست."})
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            Participation.objects.get_or_create(event=self, user_id=self.organizer_id)

    def __str__(self):
        return self.title


class Participation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participations")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    joined_at = jmodels.jDateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="events_participation_user_event_unique",
            )
        ]

    def __str__(self):
        return f"{self.user.name} در «{self.event.title}»"


class Suggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="suggestions")
    author = models.ForeignKey(
        Participation,
        on_delete=models.PROTECT,
        related_name="authored_suggestions",
    )
    proposed_at = jmodels.jDateTimeField()
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def clean(self):
        super().clean()
        self.location = (self.location or "").strip()
        self.description = (self.description or "").strip()
        errors = {}
        if not self.proposed_at:
            errors["proposed_at"] = "تاریخ و ساعت الزامی است."
        if not self.location:
            errors["location"] = "مکان الزامی است."
        elif len(self.location) > 200:
            errors["location"] = "مکان باید حداکثر ۲۰۰ نویسه باشد."
        if self.description and len(self.description) > 2000:
            errors["description"] = "توضیحات باید حداکثر ۲۰۰۰ نویسه باشد."
        if self.author_id and self.event_id and self.author.event_id != self.event_id:
            errors["author"] = "نویسنده باید در این دورهمی شرکت کند."
        if self.pk:
            original = Suggestion.objects.filter(pk=self.pk).values("event_id", "author_id").first()
            if original and original["event_id"] != self.event_id:
                errors["event"] = "دورهمی قابل تغییر نیست."
            if original and original["author_id"] != self.author_id:
                errors["author"] = "نویسنده قابل تغییر نیست."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.location = (self.location or "").strip()
        self.description = (self.description or "").strip()
        if self.pk and "update_fields" not in kwargs:
            original = (
                Suggestion.objects.filter(pk=self.pk).values("proposed_at", "location").first()
            )
            if original and (
                original["proposed_at"] == self.proposed_at
                and original["location"] == self.location
            ):
                # Nothing but the description changed: keep updated_at untouched by
                # excluding it from the UPDATE, since auto_now always fires otherwise.
                kwargs["update_fields"] = ["proposed_at", "location", "description"]
        super().save(*args, **kwargs)

    def __str__(self):
        if self.proposed_at:
            return f"{self.location} — {self.proposed_at.strftime('%Y-%m-%d %H:%M')}"
        return self.location


class Agreement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="agreements")
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="agreements")
    participant = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE,
        related_name="agreements",
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

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
            errors["participant"] = "شرکت‌کننده باید به این دورهمی تعلق داشته باشد."
        if self.suggestion_id and self.event_id and self.suggestion.event_id != self.event_id:
            errors["suggestion"] = "پیشنهاد باید به این دورهمی تعلق داشته باشد."
        if self.pk:
            original = (
                Agreement.objects.filter(pk=self.pk).values("event_id", "participant_id").first()
            )
            if original and original["event_id"] != self.event_id:
                errors["event"] = "دورهمی قابل تغییر نیست."
            if original and original["participant_id"] != self.participant_id:
                errors["participant"] = "شرکت‌کننده قابل تغییر نیست."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk and "update_fields" not in kwargs:
            original_suggestion_id = (
                Agreement.objects.filter(pk=self.pk).values_list("suggestion_id", flat=True).first()
            )
            if original_suggestion_id == self.suggestion_id:
                kwargs["update_fields"] = ["suggestion"]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.participant.user.name} روی «{self.suggestion.location}»"
