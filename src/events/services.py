from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count

from events.models import Agreement, Event, Suggestion


def highest_suggestions(event):
    suggestions = list(event.suggestions.annotate(agreement_count=Count("agreements")))
    if not suggestions:
        return []
    highest = max(suggestion.agreement_count for suggestion in suggestions)
    return [suggestion for suggestion in suggestions if suggestion.agreement_count == highest]


def finalize_event(event, user, suggestion_id):
    if user != event.organizer:
        raise PermissionError("Only the organizer can finalize this event.")
    with transaction.atomic():
        locked = Event.objects.select_for_update().get(pk=event.pk)
        if locked.status != Event.Status.ACTIVE:
            raise ValidationError("This event is already finalized.")
        non_organizer = Agreement.objects.filter(event=locked).exclude(
            participant__user=locked.organizer
        )
        if not non_organizer.exists():
            raise ValidationError(
                "Finalizing requires an agreement from someone other than the organizer."
            )
        candidates = highest_suggestions(locked)
        if suggestion_id is None:
            raise ValidationError("Choose one of the tied suggestions.")
        selected = Suggestion.objects.filter(pk=suggestion_id, event=locked).first()
        if selected is None or selected.pk not in {candidate.pk for candidate in candidates}:
            raise ValidationError("Choose one suggestion that has the most agreements.")
        locked.final_suggestion = selected
        locked.status = Event.Status.FINALIZED
        locked.save(update_fields=["final_suggestion", "status"])
    event.refresh_from_db()
    return event
