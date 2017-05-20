# -*- coding: utf-8 -*-

import time
import json
import random
import base64

from base_player import BasePlayer
from audio_video_get.common import get_md5


class LetvPlayer(BasePlayer):
    def get_params(self):
        method = 'GET'
        url = 'http://api.letvcloud.com/gpc.php'
        params = self.__get_params()
        return url, method, params

    def get_video_info(self, response):
        json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        code = json_data['code']
        if code != 0:
            self.logger.error('url: {}, code: {}'.format(self.page_url, str(code)))
            # self.logger.error('url: {}, error: {}'.format(self.page_url, json_data['message'].decode('utf-8')))
            return code, None, None
        try:
            url = base64.b64decode(json_data['data']['videoinfo']['medialist'][0]['urllist'][0]['url'])
            file_name = (get_md5(self.page_url) +
                         '.' + json_data['data']['videoinfo']['title'].split('.')[-1])
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return code, None, None
        else:
            if url is None:
                return code, None, None
        media_urls = [url]
        return code, media_urls, file_name

    def __get_params(self):
        uu = self.kwargs['uu']
        vu = self.kwargs['vu']
        pu = self.kwargs['pu']
        lang = self.kwargs['lang']
        cf = 'html5'
        ran = int(time.time())
        sign = get_md5(''.join([str(i) for i in [cf, uu, vu, ran]]) + "fbeh5player12c43eccf2bec3300344")
        a, d = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"), 16
        uuid = ''.join([str(a[random.randint(0, d)]) for _ in range(32)]) + '_' + str(0)
        params = {
            'ver': '2.4',
            'page_url': self.page_url,
            'uu': uu,
            'sign': sign,
            'lang': lang,
            'ran': str(ran),
            'vu': vu,
            'pu': pu,
            'format': 'jsonp',
            'cf': 'html5',
            'pver': 'H5_Vod_20170406_4.8.3',
            'bver': 'safari9.0',
            'uuid': uuid,
            'pf': 'html5',
            'spf': '0',
            'pet': '0',
            'callback': 'letvcloud149492509772658',
        }
        return params
