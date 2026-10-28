
from django import forms
from django_jalali.forms import jDateTimeField
from django_jalali.forms.widgets import jDateTimeInput

from events.models import Event, Suggestion

FIELD_CLASSES = (
    "min-h-11 w-full rounded-[11px] border border-line bg-white px-3 py-2.5 "
    "text-sm text-ink transition-colors focus:border-[#c49ab0] "
    "focus:outline-[3px] focus:outline-[#f5eaf0]"
)


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "details"]

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise forms.ValidationError("عنوان الزامی است.")
        if len(title) > 200:
            raise forms.ValidationError("عنوان باید حداکثر ۲۰۰ نویسه باشد.")
        return title

    def clean_details(self):
        details = (self.cleaned_data.get("details") or "").strip()
        if len(details) > 5000:
            raise forms.ValidationError("توضیحات باید حداکثر ۵۰۰۰ نویسه باشد.")
        return details


class SuggestionForm(forms.ModelForm):
    proposed_at = jDateTimeField(
        widget=jDateTimeInput(
            attrs={
                "data-jdp": "",
                "autocomplete": "off",
                "required": True,
                "class": FIELD_CLASSES,
            }
        )
    )

    class Meta:
        model = Suggestion
        fields = ["proposed_at", "location", "description"]

        widgets = {
            "location": forms.TextInput(attrs={"class": FIELD_CLASSES}),
            "description": forms.Textarea(
                attrs={"rows": 5, "class": FIELD_CLASSES + " min-h-0"}
            ),
        }

    def clean_location(self):
        location = (self.cleaned_data.get("location") or "").strip()
        if not location:
            raise forms.ValidationError("مکان الزامی است.")
        if len(location) > 200:
            raise forms.ValidationError("مکان باید حداکثر ۲۰۰ نویسه باشد.")
        return location

    def clean_description(self):
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) > 2000:
            raise forms.ValidationError("توضیحات باید حداکثر ۲۰۰۰ نویسه باشد.")
        return description
