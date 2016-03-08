import re

from markupsafe import escape, Markup

POST_REFNO_PATTERN = re.compile('&gt;&gt;(\\d{1,16})')


def parse_text(raw, linkify=False, bigheaders=False, maxlines=0, maxlinestext=None):
    lines = []
    was_empty_line = False
    for rawline in raw.splitlines():
        # Any html chars are now replaced with their escaped version
        # e.g. > became &gt;
        # keep this in mind when parsing
        line = str(escape(rawline))

        if line:
            was_empty_line = False

            lines.append(parse_text_line(line, linkify, bigheaders))
        else:
            # Allow one empty line at max
            if not was_empty_line:
                lines.append('<br>')
                was_empty_line = True

        if maxlines > 0 and len(lines) >= maxlines - 1:
            if maxlinestext:
                lines.append(maxlinestext)
            break

    value = ''.join(lines)

    value = parse_text_whole(value)

    # Mark as safe html
    return Markup(value)


# note: these match until the closing tag or the end of the line
# this is to make the maxlines code easier
CODE_RE = re.compile(r'(\[code\](?:<br>)?)(.+?(?=\[/code\]|$))(\[/code\]|$)', re.S | re.I)
SPOILER_RE = re.compile(r'(\[s\])(.+?(?=\[/s\]|$))(\[/s\]|$)', re.S | re.I)

STRIKETHROUGH_RE = re.compile(r'(~~)(.+?(?=~~))(~~)', re.S)

STRONG_RE = re.compile(r'(\*\*)(.+?(?=\*\*))(\*\*)', re.S)
STRONG2_RE = re.compile(r'(__)(.+?(?=__))(__)', re.S)

EMPHASIS_RE = re.compile(r'(\*)([^\*]+)(\*)', re.S)
EMPHASIS2_RE = re.compile(r'(_)([^_]+)(_)', re.S)

LINK_RE = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)', re.S)


def parse_text_whole(text):
    if '[code]' in text:
        text = CODE_RE.sub('<code>\\2</code>', text)

    if '[s]' in text:
        text = SPOILER_RE.sub('<span class="spoiler">\\2</span>', text)

    return text


def parse_text_line(line, linkify, bigheaders):
    with_break = True

    line = STRONG_RE.sub('<b>\\2</b>', line)
    line = STRONG2_RE.sub('<b>\\2</b>', line)

    line = EMPHASIS_RE.sub('<em>\\2</em>', line)
    line = EMPHASIS2_RE.sub('<em>\\2</em>', line)

    line = STRIKETHROUGH_RE.sub('<s>\\2</s>', line)

    if bigheaders:
        if line.startswith('####'):
            with_break = False
            line = '<h1> ' + line[4:].lstrip() + '</h1>'

        if line.startswith('###'):
            with_break = False
            line = '<h2> ' + line[3:].lstrip() + '</h2>'

    if line.startswith('##'):
        with_break = False
        line = '<h3 class="red"> ' + line[2:].lstrip() + '</h3>'

    if line.startswith('#'):
        with_break = False
        line = '<h3> ' + line[1:].lstrip() + '</h3>'

    # If the line started with a > wrap the line around a quote span
    if line.startswith('&gt;'):
        line = '<span class="quote">' + line + '</span>'

    # Replace any >>123 with <a href="#p123">&gt;&gt;123</a>
    line = POST_REFNO_PATTERN.sub('<a href="#p\\1">&gt;&gt;\\1</a>', line)

    if linkify:
        # Replace [text](links)
        line = LINK_RE.sub('<a href="\\2">\\1</a>', line)

    if with_break:
        line += '<br>'

    return line
