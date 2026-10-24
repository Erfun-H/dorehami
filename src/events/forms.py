from django import forms

from events.models import Event, Suggestion


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "details"]

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise forms.ValidationError("A title is required.")
        if len(title) > 200:
            raise forms.ValidationError("The title must be 200 characters or fewer.")
        return title

    def clean_details(self):
        details = (self.cleaned_data.get("details") or "").strip()
        if len(details) > 5000:
            raise forms.ValidationError("Details must be 5,000 characters or fewer.")
        return details


class SuggestionForm(forms.ModelForm):
    proposed_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    )

    class Meta:
        model = Suggestion
        fields = ["proposed_at", "location", "description"]

    def clean_location(self):
        location = (self.cleaned_data.get("location") or "").strip()
        if not location:
            raise forms.ValidationError("A location is required.")
        if len(location) > 200:
            raise forms.ValidationError("The location must be 200 characters or fewer.")
        return location

    def clean_description(self):
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) > 2000:
            raise forms.ValidationError("The description must be 2,000 characters or fewer.")
        return description
