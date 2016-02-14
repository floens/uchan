import time
from datetime import timedelta

from markupsafe import Markup, escape

from unichan import app
from unichan.filter.post_parser import parse_post
from unichan.lib.utils import now


@app.template_filter()
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    else:
        return plural


@app.template_filter()
def post_time(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t / 1000))


@app.template_filter()
def ban_time(t):
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(t / 1000))


@app.template_filter()
def ban_remaining(t):
    remaining = t - now()
    day_ms = timedelta(days=1).total_seconds() * 1000
    days = remaining // day_ms
    hours = (remaining - (days * day_ms)) // (timedelta(hours=1).total_seconds() * 1000)

    return ('{} day{} and '.format(int(days), '' if days == 1 else '') if days > 0 else '') + '{} hour{}'.format(int(hours + 1), '' if hours == 1 else '')


@app.template_filter()
def keep_newlines(raw):
    value = str(escape(raw))

    value = value.replace('\n', '<br>\n')

    return Markup(value)


@app.template_filter()
def post_text(text):
    return parse_post(text)
