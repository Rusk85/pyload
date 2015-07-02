# -*- coding: utf-8 -*-

import re
import urllib

from pyload.plugin.captcha.ReCaptcha import ReCaptcha
from pyload.plugin.internal.SimpleHoster import SimpleHoster


class DepositfilesCom(SimpleHoster):
    __name    = "DepositfilesCom"
    __type    = "hoster"
    __version = "0.55"

    __pattern = r'https?://(?:www\.)?(depositfiles\.com|dfiles\.(eu|ru))(/\w{1,3})?/files/(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Depositfiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<script type="text/javascript">eval\( unescape\(\'(?P<N>.*?)\''
    SIZE_PATTERN    = r': <b>(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</b>'
    OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'

    NAME_REPLACEMENTS = [(r'\%u([0-9A-Fa-f]{4})', lambda m: unichr(int(m.group(1), 16))),
                         (r'.*<b title="(?P<N>.+?)".*', "\g<N>")]
    URL_REPLACEMENTS  = [(__pattern + ".*", "https://dfiles.eu/files/\g<ID>")]

    COOKIES = [("dfiles.eu", "lang_current", "en")]

    WAIT_PATTERN = r'(?:download_waiter_remain">|html_download_api-limit_interval">|>Please wait|>Try in).+'
    ERROR_PATTER = r'File is checked, please try again in a minute'

    LINK_FREE_PATTERN    = r'<form id="downloader_file_form" action="(http://.+?\.(dfiles\.eu|depositfiles\.com)/.+?)" method="post"'
    LINK_PREMIUM_PATTERN = r'class="repeat"><a href="(.+?)"'
    LINK_MIRROR_PATTERN  = r'class="repeat_mirror"><a href="(.+?)"'


    def handle_free(self, pyfile):
        self.html = self.load(pyfile.url, post={'gateway_result': "1"})

        self.checkErrors()

        m = re.search(r"var fid = '(\w+)';", self.html)
        if m is None:
            self.retry(wait_time=5)
        params = {'fid': m.group(1)}
        self.logDebug("FID: %s" % params['fid'])

        self.checkErrors()

        recaptcha = ReCaptcha(self)
        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            return

        self.html = self.load("https://dfiles.eu/get_file.php", get=params)

        if '<input type=button value="Continue" onclick="check_recaptcha' in self.html:
            params['response'], params['challenge'] = recaptcha.challenge(captcha_key)
            self.html = self.load("https://dfiles.eu/get_file.php", get=params)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m:
            self.link = urllib.unquote(m.group(1))


    def handle_premium(self, pyfile):
        if '<span class="html_download_api-gold_traffic_limit">' in self.html:
            self.logWarning(_("Download limit reached"))
            self.retry(25, 60 * 60, "Download limit reached")

        elif 'onClick="show_gold_offer' in self.html:
            self.account.relogin(self.user)
            self.retry()

        else:
            link   = re.search(self.LINK_PREMIUM_PATTERN, self.html)
            mirror = re.search(self.LINK_MIRROR_PATTERN, self.html)

            if link:
                self.link = link.group(1)

            elif mirror:
                self.link = mirror.group(1)
