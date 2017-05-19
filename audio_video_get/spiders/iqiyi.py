# -*- coding: utf-8 -*-
import re
import os
import time
import random
import json
from ctypes import c_int, c_uint
# from urlparse import urljoin

import scrapy
from scrapy.conf import settings

from audio_video_get.items import AudioVideoGetItem
from ..common import get_md5


class IQiYiSpider(scrapy.Spider):
    name = "iqiyi"
    download_delay = 10
    users = ['1190686219', '1233288265']
    # allowed_domains = ["youku.com"]
    base_url = 'http://m.iqiyi.com/u/{user}/v/list'

    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.MobileUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for user in self.users:
            url = self.base_url.format(user=user)
            params = {
                'page': 1,
                'size': 10,
                'field': 1,
            }
            yield scrapy.FormRequest(url, method='GET', formdata=params)

    def parse(self, response):
        for video in response.body['videos']:
            item = AudioVideoGetItem()
            item['stack'] = []
            item['download'] = 0
            item['host'] = 'iqiyi'
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
            item['url'] = video['url'].replace('www', 'm')
            item['info'] = {
                'title': video['shortTitle'],
                'intro': '',
                'album': '',
                'date': video['publishDate'],
                'author': re.findall(r'u/(\d+)/v', response.url)[0],
            }
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_video_url)

        total, size, page = response.body['total'], response.body['size'], response.body['page']
        if total > size * page:
            params = {
                'page': page,
                'size': size,
                'field': 1,
            }
            yield scrapy.FormRequest(response.url, method='GET', formdata=params)

    def parse_video_url(self, response):
        item = response.meta['item']
        try:
            vid = re.findall(r'id_(.*?).html', response.url)[0]
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(response.url, str(err)))
            return
        params = {
            'vid': vid,
            'ccode': '0401',
            'client_ip': '192.168.1.1',
            'utid': 'tB2PEWHIKgECAbaWLjUeiFyE',
            'client_ts': str(round(time.time())),
        }
        url = 'https://ups.youku.com/ups/get.json'
        yield scrapy.FormRequest(url, method='GET', meta={'item': item}, formdata=params,
                                 callback=self.parse_download_url)

    def parse_download_url(self, response):
        item = response.meta['item']
        json_data = json.loads(response.body)
        try:
            # r = re.findall(r'"cdn_url":"(.*?hd=0.*?)"', json_data)
            segs = json_data['data']['stream'][0]['segs']
            item['media_urls'] = [seg['cdn_url'] for seg in segs]
            item['file_name'] += '.' + re.findall(r'st/(.*?)/fileid', item['media_urls'][0])[0]
            return item
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return None

    def __get_qyid(self, ua):
        d = 8
        t = ua + str(random.random()) + str(time.time()*1000)
        e = self.l(t, d)
        self.n(e, len(t) * d)

    @staticmethod
    def l(t, d):
        n = (1 << d) - 1
        e = [0] * ((len(t) * d >> 5) + 1)
        for r in range(0, len(t) * d, d):
            try:
                v = ord(t[r / d])
            except:
                v = 0
            e[r >> 5] |= (v & n) << r % 32
        return e

    def n(self, t, e):
        t[e >> 5] |= 128 << e % 32,
        t[14 + (e + 64 >> 9 << 4)] = e
        n, r, c, l = 1732584193, -271733879, -1732584194, 271733878
        for f in range(0, len(t), 16):
            p, h, d, g = n, r, c, l
            n = self.i(n, r, c, l, t[f + 0], 7, -680876936)
            l = self.i(l, n, r, c, t[f + 1], 12, -389564586)
            c = self.i(c, l, n, r, t[f + 2], 17, 606105819)
            r = self.i(r, c, l, n, t[f + 3], 22, -1044525330)
            n = self.i(n, r, c, l, t[f + 4], 7, -176418897)
            l = self.i(l, n, r, c, t[f + 5], 12, 1200080426)
            c = self.i(c, l, n, r, t[f + 6], 17, -1473231341)
            r = self.i(r, c, l, n, t[f + 7], 22, -45705983)
            n = self.i(n, r, c, l, t[f + 8], 7, 1770035416)
            l = self.i(l, n, r, c, t[f + 9], 12, -1958414417)
            c = self.i(c, l, n, r, t[f + 10], 17, -42063)
            r = self.i(r, c, l, n, t[f + 11], 22, -1990404162)
            n = self.i(n, r, c, l, t[f + 12], 7, 1804603682)
            l = self.i(l, n, r, c, t[f + 13], 12, -40341101)
            c = self.i(c, l, n, r, t[f + 14], 17, -1502002290)
            r = self.i(r, c, l, n, t[f + 15], 22, 1236535329)
            n = self.o(n, r, c, l, t[f + 1], 5, -165796510)
            l = self.o(l, n, r, c, t[f + 6], 9, -1069501632)
            c = self.o(c, l, n, r, t[f + 11], 14, 643717713)
            r = self.o(r, c, l, n, t[f + 0], 20, -373897302)
            n = self.o(n, r, c, l, t[f + 5], 5, -701558691)
            l = self.o(l, n, r, c, t[f + 10], 9, 38016083)
            c = self.o(c, l, n, r, t[f + 15], 14, -660478335)
            r = self.o(r, c, l, n, t[f + 4], 20, -405537848)
            n = self.o(n, r, c, l, t[f + 9], 5, 568446438)
            l = self.o(l, n, r, c, t[f + 14], 9, -1019803690)
            c = self.o(c, l, n, r, t[f + 3], 14, -187363961)
            r = self.o(r, c, l, n, t[f + 8], 20, 1163531501)
            n = self.o(n, r, c, l, t[f + 13], 5, -1444681467)
            l = self.o(l, n, r, c, t[f + 2], 9, -51403784)
            c = self.o(c, l, n, r, t[f + 7], 14, 1735328473)
            r = self.o(r, c, l, n, t[f + 12], 20, -1926607734)
            n = self.u(n, r, c, l, t[f + 5], 4, -378558)
            l = self.u(l, n, r, c, t[f + 8], 11, -2022574463)
            c = self.u(c, l, n, r, t[f + 11], 16, 1839030562)
            r = self.u(r, c, l, n, t[f + 14], 23, -35309556)
            n = self.u(n, r, c, l, t[f + 1], 4, -1530992060)
            l = self.u(l, n, r, c, t[f + 4], 11, 1272893353)
            c = self.u(c, l, n, r, t[f + 7], 16, -155497632)
            r = self.u(r, c, l, n, t[f + 10], 23, -1094730640)
            n = self.u(n, r, c, l, t[f + 13], 4, 681279174)
            l = self.u(l, n, r, c, t[f + 0], 11, -358537222)
            c = self.u(c, l, n, r, t[f + 3], 16, -722521979)
            r = self.u(r, c, l, n, t[f + 6], 23, 76029189)
            n = self.u(n, r, c, l, t[f + 9], 4, -640364487)
            l = self.u(l, n, r, c, t[f + 12], 11, -421815835)
            c = self.u(c, l, n, r, t[f + 15], 16, 530742520)
            r = self.u(r, c, l, n, t[f + 2], 23, -995338651)
            n = self.a(n, r, c, l, t[f + 0], 6, -198630844)
            l = self.a(l, n, r, c, t[f + 7], 10, 1126891415)
            c = self.a(c, l, n, r, t[f + 14], 15, -1416354905)
            r = self.a(r, c, l, n, t[f + 5], 21, -57434055)
            n = self.a(n, r, c, l, t[f + 12], 6, 1700485571)
            l = self.a(l, n, r, c, t[f + 3], 10, -1894986606)
            c = self.a(c, l, n, r, t[f + 10], 15, -1051523)
            r = self.a(r, c, l, n, t[f + 1], 21, -2054922799)
            n = self.a(n, r, c, l, t[f + 8], 6, 1873313359)
            l = self.a(l, n, r, c, t[f + 15], 10, -30611744)
            c = self.a(c, l, n, r, t[f + 6], 15, -1560198380)
            r = self.a(r, c, l, n, t[f + 13], 21, 1309151649)
            n = self.a(n, r, c, l, t[f + 4], 6, -145523070)
            l = self.a(l, n, r, c, t[f + 11], 10, -1120210379)
            c = self.a(c, l, n, r, t[f + 2], 15, 718787259)
            r = self.a(r, c, l, n, t[f + 9], 21, -343485551)
            n = self.s(n, p)
            r = self.s(r, h)
            c = self.s(c, d)
            l = self.s(l, g)
        return n, r, c, l

    def i(self, t, e, n, i, o, u, a):
        return self.r(e & n | ~e & i, t, e, o, u, a)

    def r(self, t, e, n, r, i, o):
        return self.s(self.c(self.s(self.s(e, t), self.s(r, o)), i), n)

    @staticmethod
    def s(t, e):
        n = (65535 & t) + (65535 & e)
        return (t >> 16) + (e >> 16) + (n >> 16) << 16 | 65535 & n

    @staticmethod
    def c(t, e):
        return t << e | t >> 32 - e

    def o(self, t, e, n, i, o, u, a):
        return self.r(e & i | n & ~i, t, e, o, u, a)

    def u(self, t, e, n, i, o, u, a):
        return self.r(e ^ n ^ i, t, e, o, u, a)

    def a(self, t, e, n, i, o, u, a):
        return self.r(n ^ (e | ~i), t, e, o, u, a)
