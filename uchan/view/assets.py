from flask_assets import Environment
from webassets import Bundle

from uchan import configuration


def setup_assets(app):
    assets = Environment(app)
    assets.directory = './assets/'
    assets.url = '/assets'
    assets.manifest = 'json'

    scripts = [('js_site', 'site', 'js/site'),
               ('js_thread', 'thread', 'js/thread'),
               ('js_extra', 'extra', 'js/extra')
               ]

    styles = [('css', 'style', 'style/style'),
              ('css_mod', 'mod_style', 'mod/style/mod_style'),
              ('css_extra', 'extra', 'style/extra')
              ]

    themes = [('µchan', 'uchan'),
              ('Yotsuba', 'yotsuba')
              ]

    registered_bundles = []

    theme_bundles = []

    if configuration.app.debug:
        # On debug, do not add a version code, and build automatically on changes.
        assets.url_expire = False
        assets.auto_build = True

        for script in scripts:
            bundle = Bundle(script[2] + '.js', output=script[1] + '.js')
            registered_bundles.append((script[0], bundle))

        for style in styles:
            bundle = Bundle(style[2] + '.css', output=style[1] + '.css')
            registered_bundles.append((style[0], bundle))

        for theme in themes:
            bundle = Bundle('style/themes/' + theme[1] + '.css',
                            output=theme[1] + '.css')
            theme_bundles.append(bundle)

    else:
        # On release, do add the version code, and don't rebuild automatically.
        assets.url_expire = True
        assets.auto_build = False

        for script in scripts:
            bundle = Bundle(script[2] + '.js', filters='jsmin', output=script[1] + '.%(version)s.js')
            registered_bundles.append((script[0], bundle))

        for style in styles:
            bundle = Bundle(style[2] + '.css', filters='cleancss', output=style[1] + '.%(version)s.css')
            registered_bundles.append((style[0], bundle))

        for theme in themes:
            bundle = Bundle('style/themes/' + theme[1] + '.css',
                            filters='cleancss', output=theme[1] + '.%(version)s.css')
            theme_bundles.append(bundle)

    for registered_bundle in registered_bundles:
        assets.register(registered_bundle[0], registered_bundle[1])

    theme_names = []
    for i, theme_bundle in enumerate(theme_bundles):
        assets.register('css_theme_' + themes[i][1], theme_bundle)
        theme_names.append(themes[i])

    app.jinja_env.globals['theme_names'] = theme_names
