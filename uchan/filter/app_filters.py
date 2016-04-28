import time

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
def formatted_time(t):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(t / 1000))


@app.template_filter()
def time_remaining(t):
    remaining = max(0, t - now())

    ms_in_day = 1000 * 60 * 60 * 24
    days = int(remaining // ms_in_day)
    remaining -= days * ms_in_day

    ms_in_hour = 1000 * 60 * 60
    hours = int(remaining // ms_in_hour)
    remaining -= hours * ms_in_hour

    ms_in_minute = 1000 * 60
    minutes = int(remaining // ms_in_minute)
    remaining -= minutes * ms_in_minute

    ms_in_second = 1000
    seconds = int(remaining // ms_in_second)
    remaining -= seconds * ms_in_second

    text = ''
    if not days and not hours and not minutes:
        text += '{} second{}'.format(seconds, '' if seconds == 1 else 's')
    else:
        if days > 0:
            text += '{} day{}'.format(days, '' if days == 1 else 's')
            if hours > 0:
                text += ', '
            else:
                text += ' and '
        if hours > 0:
            text += '{} hour{} and '.format(hours, '' if hours == 1 else 's')
        text += '{} minute{}'.format(minutes, '' if minutes == 1 else 's')

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
