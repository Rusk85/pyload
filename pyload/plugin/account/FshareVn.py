# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class FshareVn(Account):
    __name    = "FshareVn"
    __type    = "account"
    __version = "0.09"

    __description = """Fshare.vn account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    VALID_UNTIL_PATTERN = ur'<dt>Thời hạn dùng:</dt>\s*<dd>([^<]+)</dd>'
    LIFETIME_PATTERN = ur'<dt>Lần đăng nhập trước:</dt>\s*<dd>.+?</dd>'
    TRAFFIC_LEFT_PATTERN = ur'<dt>Tổng Dung Lượng Tài Khoản</dt>\s*<dd.*?>([\d.]+) ([kKMG])B</dd>'
    DIRECT_DOWNLOAD_PATTERN = ur'<input type="checkbox"\s*([^=>]*)[^>]*/>Kích hoạt download trực tiếp</dt>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.fshare.vn/account_info.php", decode=True)

        if re.search(self.LIFETIME_PATTERN, html):
            self.logDebug("Lifetime membership detected")
            trafficleft = self.getTrafficLeft()
            return {"validuntil": -1, "trafficleft": trafficleft, "premium": True}

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), '%I:%M:%S %p %d-%m-%Y'))
            trafficleft = self.getTrafficLeft()
        else:
            premium = False
            validuntil = None
            trafficleft = None

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        html = req.load("https://www.fshare.vn/login.php",
                        post={'LoginForm[email]'     : user,
                              'LoginForm[password]'  : data['password'],
                              'LoginForm[rememberMe]': 1,
                              'yt0'                  : "Login"},
                        referer=True,
                        decode=True)

        if not re.search(r'<img\s+alt="VIP"', html):
            self.wrongPassword()


    def getTrafficLeft(self):
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        return self.parseTraffic(m.group(1) + m.group(2)) if m else 0
