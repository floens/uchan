import config
import requests
from uchan import g
from uchan.lib import ArgumentError
from uchan.lib.service.verification_service import VerificationMethod

"""
This plugin adds google reCaptcha v2 as a verification method.
Add the site key and secret like this in config.py:
PLUGIN_CONFIG = {
    'captcha2': {
        'sitekey': '',
        'secret': ''
    }
}

And add it to the enabled plugins list:
PLUGINS = ['captcha2']
"""


def describe_plugin():
    return {
        'name': 'captcha2',
        'description': 'This plugin adds google reCaptcha v2 as a verification method.',
        'version': 'unstable'
    }


class Recaptcha2Method(VerificationMethod):
    def __init__(self, sitekey, secret):
        super().__init__()

        self.sitekey = sitekey
        self.secret = secret

        self.html = """
        <script>

        (function() {
            if (!window.recaptchaOnloadCallback) {
                window.recaptchaContainers = [];
                window.recaptchaOnloadCallback = function() {
                    for (var i = 0; i < recaptchaContainers.length; i++) {
                        var container = recaptchaContainers[i];
                        grecaptcha.render(container, {
                            'sitekey': '__sitekey__',
                            'callback': window['globalCaptchaEntered']
                        });
                    }
                };
                var recaptchaScript = document.createElement('script');
                recaptchaScript.type = 'text/javascript';
                recaptchaScript.async = true;
                recaptchaScript.defer = true;
                recaptchaScript.src = 'https://www.google.com/recaptcha/api.js?onload=recaptchaOnloadCallback&render=explicit';
                var s = document.getElementsByTagName('script')[0];
                s.parentNode.insertBefore(recaptchaScript, s);
            }

            var containerName = 'g-recaptcha-' + recaptchaContainers.length;
            recaptchaContainers.push(containerName);
            document.write('<div id="' + containerName + '"></div>');
        })();
        </script>
        """.replace('__sitekey__', self.sitekey)

    def get_html(self):
        return self.html

    def verify_request(self, request):
        form = request.form

        response = form.get('g-recaptcha-response', None)
        if not response:
            raise ArgumentError('Please fill in the captcha')

        try:
            valid = self.verify(response)
        except Exception:
            g.logger.exception('Verify exception')
            raise ArgumentError('Error contacting recaptcha service')

        if not valid:
            raise ArgumentError('Captcha invalid')

        return True

    def verify(self, response):
        res = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': self.secret,
            'response': response
        })
        res_json = res.json()
        return 'success' in res_json and res_json['success'] is True


def on_enable():
    if 'captcha2' not in config.PLUGIN_CONFIG:
        raise RuntimeError('sitekey or secret not set in PLUGIN_CONFIG')

    plugin_captcha = config.PLUGIN_CONFIG['captcha2']
    sitekey = plugin_captcha['sitekey']
    secret = plugin_captcha['secret']
    if not sitekey or not secret:
        raise RuntimeError('sitekey or secret empty in PLUGIN_CONFIG')

    method = Recaptcha2Method(sitekey, secret)
    g.verification_service.add_method(method)
