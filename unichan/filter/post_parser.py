import re

from markupsafe import escape, Markup

from unichan.lib import ArgumentError

POST_REFNO_PATTERN = re.compile('&gt;&gt;(\\d{1,16})')


def validate_post(raw):
    if not raw:
        raise ArgumentError('No text')

    if len(raw) > 2000:
        raise ArgumentError('Text too long')

    if len(raw.splitlines()) > 25:
        raise ArgumentError('Too many lines')


def parse_post(raw):
    # Any html chars are now replaced with their escaped version
    # e.g. > became &gt;
    # keep this in mind when parsing
    value = str(escape(raw))

    lines = []
    was_empty_line = False
    for line in value.splitlines():
        if line:
            was_empty_line = False

            # If the line started with a > wrap the line around a quote span
            if line.startswith('&gt;'):
                line = '<span class="quote">' + line + '</span>'

            # Replace any >>123 with <a href="#p123">&gt;&gt;123</a>
            line = POST_REFNO_PATTERN.sub('<a href="#p\\1">&gt;&gt;\\1</a>', line)

            lines.append(line)
        else:
            # Allow one empty line at max
            if not was_empty_line:
                lines.append('')
                was_empty_line = True

    value = '<br>'.join(lines)

    return Markup(value)
