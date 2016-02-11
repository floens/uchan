import time

from markupsafe import Markup, escape

from unichan import app


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
def keep_newlines(raw):
    value = str(escape(raw))

    value = value.replace('\n', '<br>\n')

    return Markup(value)
