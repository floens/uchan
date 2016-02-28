import requests

import config
from uchan.lib import ArgumentError

"""
This plugin adds google reCaptcha v2 to the quick reply box.
Add the site key and secret like this in config.py:
PLUGIN_CONFIG = {
    'captcha2': {
        'sitekey': '',
        'secret': ''
    }
}
"""


def describe_plugin():
    return {
        'name': 'captcha2',
        'description': 'Adds google reCaptcha v2 to the quick reply box.',
        'version': 'unstable'
    }


_sitekey = None
_secret = None


def on_enable(*args, **kwargs):
    print('on_enable called!', args, kwargs)
    global _sitekey, _secret

    if 'captcha2' not in config.PLUGIN_CONFIG:
        raise RuntimeError('sitekey or secret not set in PLUGIN_CONFIG')

    plugin_captcha = config.PLUGIN_CONFIG['captcha2']
    _sitekey = plugin_captcha['sitekey']
    _secret = plugin_captcha['secret']
    if not _sitekey or not _secret:
        raise RuntimeError('sitekey or secret empty in PLUGIN_CONFIG')


def on_disable(*args, **kwargs):
    print('on_disable called!', args, kwargs)


def extra_javascript(js):
    global _sitekey
    js.add("""
<script>
(function() {
    if (window.pageDetails && (pageDetails.mode == 'board' || pageDetails.mode == 'thread')) {
        var recaptchaElement = document.createElement('div');
        recaptchaElement.className = 'g-recaptcha input';
        recaptchaElement.setAttribute('style', 'width: 302px;');
        recaptchaElement.innerHTML = 'Type to show the captcha.<br><br>';

        var captchaParams = {
            'sitekey': '__sitekey__'
        };

        var postFormFieldset = document.querySelector('.post-form fieldset');
        var postFormComment = postFormFieldset.querySelector('textarea[name="comment"]').parentNode;
        postFormFieldset.insertBefore(recaptchaElement, postFormComment.nextSibling);
        var rendered = false;
        postFormComment.addEventListener('keydown', function(event) {
            if (!rendered) {
                rendered = true;
                recaptchaElement.innerHTML = '';
                window.grecaptcha.render(recaptchaElement, captchaParams);
            }
        });

        window.recaptchaOnloadCallback = function() {
        };

        if (window.qr) {
            var qrRecaptchaElement = recaptchaElement.cloneNode(false);
            qr.insertFormElement(qrRecaptchaElement);
            var qrCaptchaRendered = false;
            var qrRecaptchaWidgetId = null;
            qr.addStateChangedListener(function(qr, what) {
                if (what == 'show') {
                    if (!qrCaptchaRendered) {
                        qrCaptchaRendered = true;
                        qrRecaptchaWidgetId = window.grecaptcha.render(qrRecaptchaElement, captchaParams);
                    }
                } else if (what == 'submitError' || what == 'submitDone') {
                    window.grecaptcha.reset(qrRecaptchaWidgetId);
                }
            });
        }

        var recaptchaScript = document.createElement('script');
        recaptchaScript.type = 'text/javascript';
        recaptchaScript.async = true;
        recaptchaScript.defer = true;
        recaptchaScript.src = 'https://www.google.com/recaptcha/api.js?onload=recaptchaOnloadCallback&render=explicit';
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(recaptchaScript, s);
    }
})();
</script>
""".replace('__sitekey__', _sitekey))


def on_handle_post_check(post_details):
    """Called from a worker thread to check the post params.
    The perfect moment to check the captcha with the google servers.
    """

    response = post_details.form.get('g-recaptcha-response', None)
    if not response:
        raise ArgumentError('Please fill in the captcha')

    if not _verify(response):
        raise ArgumentError('Captcha invalid')


def _verify(response):
    global _secret
    res = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': _secret,
        'response': response
    })
    res_json = res.json()
    print(res_json)
    return 'success' in res_json and res_json['success'] == True
