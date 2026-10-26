from django.template import Library
from jdatetime import datetime

register = Library()


@register.filter
def event_date_in_persian(date: datetime, with_time: bool = False):
    time = date.strftime("%H:%M")
    text = (
        f"{date.j_weekdays_fa[date.weekday()]} {date.day}"
        f" {date.j_months_fa[date.month - 1]} {date.year}"
    )
    return f"{text}{f"، ساعت {time}" if with_time else ""}"
