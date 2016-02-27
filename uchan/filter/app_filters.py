import time
from datetime import timedelta

from markupsafe import Markup, escape

from uchan import app
from uchan.filter.text_parser import parse_text
from uchan.lib.utils import now


@app.template_filter()
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    else:
        return plural


@app.template_filter()
def post_time(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t / 1000))


@app.template_filter()
def ban_time(t):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(t / 1000))


@app.template_filter()
def ban_remaining(t):
    remaining = t - now()
    day_ms = timedelta(days=1).total_seconds() * 1000
    days = remaining // day_ms
    hours = (remaining - (days * day_ms)) // (timedelta(hours=1).total_seconds() * 1000)

    text = ''
    if days > 0:
        text += '{} day{} and '.format(int(days), '' if days == 1 else 's')
    hours_rounded = int(hours + 1)
    text += '{} hour{}'.format(hours_rounded, '' if hours_rounded == 1 else 's')
    return text


@app.template_filter()
def keep_newlines(raw):
    value = str(escape(raw))

    value = value.replace('\n', '<br>\n')

    return Markup(value)


@app.template_filter()
def page_formatting(text):
    return parse_text(text, linkify=True, bigheaders=True)


@app.template_filter()
def post_text(text):
    return parse_text(text)


@app.template_filter()
def post_name(name):
    value = str(escape(name))

    if '!' in value:
        one, two = value.split('!', maxsplit=1)
        value = one + '<span class="trip">!' + two + '</span>'

    return Markup(value)
