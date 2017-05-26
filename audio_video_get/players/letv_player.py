# -*- coding: utf-8 -*-

import time
import json
import random
import base64

from scrapy.exceptions import CloseSpider

from base_player import BasePlayer
from audio_video_get.common import get_md5


class LetvPlayer(BasePlayer):
    name = 'letv_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(LetvPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.url = 'http://api.letvcloud.com/gpc.php'
        self.method = 'GET'
        self.params = self.__get_params()

    def parse_video(self, response):
        item = response.meta['item']
        if not self.get_json(response):
            return
        if not self.get_media_urls():
            return
        item['media_urls'] = self.media_urls
        item['file_name'] = self.file_name
        return item

    def get_media_urls(self):
        try:
            self.media_urls = [base64.b64decode(self.json_data['data']['videoinfo']['medialist'][0]['urllist'][0]['url'])]
            self.file_name = (get_md5(self.page_url) + '.' +
                              self.json_data['data']['videoinfo']['title'].split('.')[-1])
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            if self.media_urls is None:
                self.logger.error('url: {}, error: did not get any URL in the json data'.format(self.page_url))
                return False
        return True

    def get_json(self, response):
        try:
            json_data = json.loads(response.body[response.body.find('(') + 1: -1])
            code = json_data['code']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            if code != 0:
                self.logger.error('url: {}, code: {}'.format(self.page_url, str(code)))
                return False
            elif code == 10071:
                self.logger.error('Anti-Spider: close spider by self, error code: {}'.format(code))
                raise CloseSpider('Anti-Spider')
        return True

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
