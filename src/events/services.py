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
        raise PermissionError("فقط میزبان می‌تواند این دورهمی را نهایی کند.")
    with transaction.atomic():
        locked = Event.objects.select_for_update().get(pk=event.pk)
        if locked.status != Event.Status.ACTIVE:
            raise ValidationError("این دورهمی نهایی شده است.")
        non_organizer = Agreement.objects.filter(event=locked).exclude(
            participant__user=locked.organizer
        )
        if not non_organizer.exists():
            raise ValidationError("برای نهایی‌کردن، دست‌کم یک موافقت از غیر میزبان لازم است.")
        candidates = highest_suggestions(locked)
        if suggestion_id is None:
            raise ValidationError("یکی از پیشنهادهای برابر را انتخاب کنید.")
        try:
            selected_id = int(suggestion_id)
        except (TypeError, ValueError):
            raise ValidationError("باید پیشنهادی را انتخاب کنید که بیشترین موافقت را دارد.")
        selected = Suggestion.objects.filter(pk=selected_id, event=locked).first()
        if selected is None or selected.pk not in {candidate.pk for candidate in candidates}:
            raise ValidationError("باید پیشنهادی را انتخاب کنید که بیشترین موافقت را دارد.")
        locked.final_suggestion = selected
        locked.status = Event.Status.FINALIZED
        locked.save(update_fields=["final_suggestion", "status"])
    event.refresh_from_db()
    return event
