from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from events.forms import EventCreateForm, SuggestionForm
from events.models import Agreement, Event, Participation, Suggestion
from events.services import finalize_event, highest_suggestions


def home(request):
    events = []
    if request.user.is_authenticated:
        events = (
            Event.objects.filter(participations__user=request.user)
            .distinct()
            .order_by("-created_at")
        )
    return render(request, "home.html", {"events": events})


def _event_or_404(token):
    event = Event.objects.filter(invite_token=token).first()
    if event is None:
        raise Http404
    return event


def _participation(event, user):
    return Participation.objects.filter(event=event, user=user).first()


def _require_active_participant(event, user):
    if event.status != Event.Status.ACTIVE:
        raise PermissionDenied
    participation = _participation(event, user)
    if participation is None:
        raise PermissionDenied
    return participation


def _suggestion_for_event(event, suggestion_id):
    suggestion = Suggestion.objects.filter(pk=suggestion_id, event=event).first()
    if suggestion is None:
        raise Http404
    return suggestion


@login_required
def create_event(request):
    form = EventCreateForm(request.POST or None)
    form.instance.organizer = request.user
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.status = Event.Status.ACTIVE
        event.save()
        return redirect("event-detail", token=event.invite_token)
    return render(request, "events/new.html", {"form": form})


@login_required
def event_detail(request, token):
    event = (
        Event.objects.filter(invite_token=token)
        .select_related("organizer", "final_suggestion")
        .first()
    )
    if event is None:
        return render(request, "events/unavailable.html", status=404)
    participation = _participation(event, request.user)
    if event.status == Event.Status.FINALIZED and participation is None:
        return render(request, "events/unavailable.html", status=404)
    if event.status == Event.Status.ACTIVE and participation is None:
        participation = Participation.objects.create(event=event, user=request.user)
    suggestions = event.suggestions.select_related("author__user").prefetch_related(
        "agreements__participant__user"
    )
    tied = []
    if event.status == Event.Status.ACTIVE and request.user == event.organizer:
        candidates = highest_suggestions(event)
        tied = candidates if len(candidates) > 1 else []
    return render(
        request,
        "events/detail.html",
        {
            "event": event,
            "participation": participation,
            "suggestions": suggestions,
            "suggestion_form": SuggestionForm(),
            "tied_suggestions": tied,
        },
    )


@login_required
@require_POST
def create_suggestion(request, token):
    event = _event_or_404(token)
    participation = _require_active_participant(event, request.user)
    form = SuggestionForm(request.POST)
    if form.is_valid():
        suggestion = form.save(commit=False)
        suggestion.event = event
        suggestion.author = participation
        suggestion.save()
        return redirect("event-detail", token=event.invite_token)
    return render(
        request,
        "events/detail.html",
        {
            "event": event,
            "participation": participation,
            "suggestions": event.suggestions.all(),
            "suggestion_form": form,
            "form": form,
            "tied_suggestions": [],
        },
    )


@login_required
@require_POST
def edit_suggestion(request, token, suggestion_id):
    event = _event_or_404(token)
    participation = _require_active_participant(event, request.user)
    suggestion = _suggestion_for_event(event, suggestion_id)
    if suggestion.author_id != participation.id:
        raise PermissionDenied
    form = SuggestionForm(request.POST, instance=suggestion)
    if not form.is_valid():
        raise PermissionDenied
    form.save()
    return redirect("event-detail", token=event.invite_token)


@login_required
@require_POST
def delete_suggestion(request, token, suggestion_id):
    event = _event_or_404(token)
    participation = _require_active_participant(event, request.user)
    suggestion = _suggestion_for_event(event, suggestion_id)
    is_author = suggestion.author_id == participation.id
    if not (is_author or request.user == event.organizer):
        raise PermissionDenied
    if event.final_suggestion_id == suggestion.id:
        raise PermissionDenied
    suggestion.delete()
    return redirect("event-detail", token=event.invite_token)


@login_required
@require_POST
def agree_suggestion(request, token, suggestion_id):
    event = _event_or_404(token)
    participation = _require_active_participant(event, request.user)
    suggestion = _suggestion_for_event(event, suggestion_id)
    with transaction.atomic():
        agreement, created = Agreement.objects.select_for_update().get_or_create(
            event=event,
            participant=participation,
            defaults={"suggestion": suggestion},
        )
        if not created and agreement.suggestion_id != suggestion.id:
            agreement.suggestion = suggestion
            agreement.save(update_fields=["suggestion", "updated_at"])
    return redirect("event-detail", token=event.invite_token)


@login_required
@require_POST
def finalize(request, token):
    from django.core.exceptions import ValidationError

    event = _event_or_404(token)
    if request.user != event.organizer:
        raise PermissionDenied
    suggestion_id = request.POST.get("suggestion_id") or None
    try:
        finalize_event(event, request.user, suggestion_id)
    except ValidationError as exc:
        candidates = highest_suggestions(event)
        message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
        return render(
            request,
            "events/detail.html",
            {
                "event": event,
                "suggestions": event.suggestions.all(),
                "suggestion_form": SuggestionForm(),
                "tied_suggestions": candidates if len(candidates) > 1 else [],
                "finalize_error": message,
            },
        )
    return redirect("event-detail", token=event.invite_token)
