from django.urls import path

from events import views

urlpatterns = [
    path("new/", views.create_event, name="event-create"),
    path("<str:token>/", views.event_detail, name="event-detail"),
    path("<str:token>/suggestions/", views.create_suggestion, name="suggestion-create"),
    path(
        "<str:token>/suggestions/<int:suggestion_id>/edit/",
        views.edit_suggestion,
        name="suggestion-edit",
    ),
    path(
        "<str:token>/suggestions/<int:suggestion_id>/delete/",
        views.delete_suggestion,
        name="suggestion-delete",
    ),
    path(
        "<str:token>/suggestions/<int:suggestion_id>/agree/",
        views.agree_suggestion,
        name="suggestion-agree",
    ),
    path("<str:token>/finalize/", views.finalize, name="event-finalize"),
]
