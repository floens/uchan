import os

import dateutil.parser
import requests

from uchan import logger
from uchan.lib.exceptions import ArgumentError
from uchan.lib.service import verification_service
from uchan.lib.utils import now

"""
This plugin adds google reCaptcha v2 as a verification method.
Currently the plugin system is in a semi-usable state. 
We might put this code back into the core logic.
"""


def describe_plugin():
    return {
        'name': 'captcha2',
        'description': 'This plugin adds google reCaptcha v2 as a verification method.',
        'version': 'unstable'
    }


class Recaptcha2Method(verification_service.VerificationMethod):
    def __init__(self, sitekey, secret):
        super().__init__()

        self.sitekey = sitekey
        self.secret = secret

        self.html = """
        <div class="g-recaptcha"></div>
        <noscript>
          <div>
            <div style="width: 302px; height: 422px; position: relative;">
              <div style="width: 302px; height: 422px; position: absolute;">
                <iframe src="https://www.google.com/recaptcha/api/fallback?k=__sitekey__"
                        frameborder="0" scrolling="no"
                        style="width: 302px; height:422px; border-style: none;">
                </iframe>
              </div>
            </div>
            <div style="width: 300px; height: 60px; border-style: none;
                           bottom: 12px; left: 25px; margin: 0px; padding: 0px; right: 25px;
                           background: #f9f9f9; border: 1px solid #c1c1c1; border-radius: 3px;">
              <textarea id="g-recaptcha-response" name="g-recaptcha-response"
                           class="g-recaptcha-response"
                           style="width: 250px; height: 40px; border: 1px solid #c1c1c1;
                                  margin: 10px 25px; padding: 0px; resize: none;" >
              </textarea>
            </div>
          </div>
        </noscript>
        """.replace('__sitekey__', self.sitekey)

        self.javascript = """
        <script src="https://www.google.com/recaptcha/api.js?onload=g_captcha2_callback&render=explicit" async defer></script>
        <script>
        window.g_captcha2_callback = function() {
            var captchas = document.querySelectorAll('.g-recaptcha');
            for (var i = 0; i < captchas.length; i++) {
                grecaptcha.render(captchas[i], {
                    'sitekey': '__sitekey__'
                });
            }
        };
        </script>
        """.replace('__sitekey__', self.sitekey)

    def get_html(self):
        return self.html

    def get_javascript(self):
        return self.javascript

    def verification_in_request(self, request):
        return 'g-recaptcha-response' in request.form

    def verify_request(self, request):
        form = request.form

        response = form.get('g-recaptcha-response', None)
        if not response:
            raise ArgumentError('Please fill in the captcha')

        try:
            valid = self.verify(response)
        except Exception:
            logger.exception('Verify exception')
            raise ArgumentError('Error contacting recaptcha service')

        if not valid:
            raise ArgumentError('Captcha invalid')

    def verify(self, response):
        res = requests.post('https://www.google.com/recaptcha/api/siteverify',
                            data={
                                'secret': self.secret,
                                'response': response
                            })
        res_json = res.json()

        timestamp_iso = 'challenge_ts' in res_json and res_json['challenge_ts']
        if not timestamp_iso:
            return False

        timestamp = dateutil.parser.parse(timestamp_iso)
        time_ago = now() - int(timestamp.timestamp() * 1000)

        if time_ago > 1000 * 60 * 30:
            # Expired
            return False

        if 'success' in res_json and res_json['success'] is True:
            return True

        return False


def on_enable():
    sitekey = os.getenv('GOOGLE_CAPTCHA2_SITEKEY',
                        '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    secret = os.getenv('GOOGLE_CAPTCHA2_SECRET',
                       '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')

    if not sitekey or not secret:
        raise RuntimeError(
            "Required keys not found in the environment. "
            "Please set the GOOGLE_CAPTCHA2_SITEKEY and GOOGLE_CAPTCHA2_SECRET environment variables.")

    method = Recaptcha2Method(sitekey, secret)
    verification_service.add_method(method)
