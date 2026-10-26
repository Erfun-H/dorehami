from django.contrib import admin

from events.models import Agreement, Event, Participation, Suggestion


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 0


class SuggestionInline(admin.TabularInline):
    model = Suggestion
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "organizer", "status", "final_suggestion", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "organizer__email"]
    inlines = [ParticipationInline, SuggestionInline]


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ["user", "event", "joined_at"]
    search_fields = ["user__email", "user__name", "event__title"]


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ["location", "event", "author", "proposed_at", "created_at"]
    search_fields = ["location", "event__title", "author__user__name"]


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ["event", "participant", "suggestion", "created_at", "updated_at"]
    list_filter = ["event"]
    search_fields = ["participant__user__name", "suggestion__location"]
