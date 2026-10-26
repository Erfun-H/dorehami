from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import Http404, JsonResponse
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


def _detail_context(
    event,
    participation,
    suggestion_form=None,
    finalize_error=None,
    failed_edit=None,
    **kwargs,
):
    suggestions = list(
        event.suggestions.annotate(agreements_count=Count("agreements"))
        .select_related("author__user")
        .prefetch_related("agreements__participant__user")
        .order_by("-agreements_count", "-created_at")
    )
    items = []
    for suggestion in suggestions:
        edit_form = SuggestionForm(instance=suggestion)
        if failed_edit is not None and failed_edit.instance.pk == suggestion.pk:
            edit_form = failed_edit
        items.append(
            {
                "suggestion": suggestion,
                "edit_form": edit_form,
                "voters": [
                    agreement.participant.user.name
                    for agreement in suggestion.agreements.all()
                ],
                "voters_element_id": f"voters-data-{suggestion.pk}",
            }
        )
    candidates = []
    if event.status == Event.Status.ACTIVE:
        candidates = highest_suggestions(event)
    is_organizer = event.organizer_id == participation.user_id
    leading_ids = (
        {candidate.pk for candidate in candidates}
        if candidates and candidates[0].agreement_count > 0
        else set()
    )
    return {
        "event": event,
        "participation": participation,
        "suggestion_items": items,
        "suggestion_form": suggestion_form or SuggestionForm(),
        "participants": event.participations.select_related("user").order_by(
            "joined_at"
        ),
        "leading_ids": leading_ids,
        "tied_suggestions": candidates if is_organizer and len(candidates) > 1 else [],
        "winning_suggestion": (
            candidates[0] if is_organizer and len(candidates) == 1 else None
        ),
        "finalize_error": finalize_error,
        **kwargs,
    }


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
    return render(
        request,
        "events/detail.html",
        _detail_context(
            event,
            participation,
            user_agreement=participation.agreements.filter(event=event).first(),
        ),
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
        if "application/json" in request.headers.get("Accept", ""):
            return JsonResponse({"success": True, "suggestion_id": suggestion.pk})
        return redirect("event-detail", token=event.invite_token)
    if "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(
            {"success": False, "errors": {f: list(e) for f, e in form.errors.items()}},
            status=400,
        )
    return render(
        request, "events/detail.html", _detail_context(event, participation, form)
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
    if form.is_valid():
        form.save()
        return redirect("event-detail", token=event.invite_token)
    return render(
        request,
        "events/detail.html",
        _detail_context(event, participation, failed_edit=form),
    )


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
            agreement.save()
    if "application/json" in request.headers.get("Accept", ""):
        agreements = Agreement.objects.filter(event=event).values(
            "suggestion_id", "participant__user__name"
        )
        grouped = {str(item.pk): [] for item in event.suggestions.all()}
        for agreement_item in agreements:
            grouped[str(agreement_item["suggestion_id"])].append(
                agreement_item["participant__user__name"]
            )
        return JsonResponse(
            {
                "agreement": {"suggestion_id": suggestion.pk},
                "agreements": grouped,
            }
        )
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
        message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
        participation = _participation(event, request.user)
        return render(
            request,
            "events/detail.html",
            _detail_context(event, participation, finalize_error=message),
        )
    return redirect("event-detail", token=event.invite_token)
