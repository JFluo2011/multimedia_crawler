import re
import os
import time
import math
import json
import random
from ctypes import c_int, c_uint
from urlparse import urljoin, urlparse

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from audio_video_get.items import WeiXinErGengItem
from audio_video_get.common import get_md5

seed = "#$#@#*ad"


class WeiXinErGeng(CrawlSpider):
    name = "weixin_ergeng"
    download_delay = 10
    # allowed_domains = ['chuansong.me', 'video.qq.com']
    start_urls = ['http://chuansong.me/account/zjhtcmgs111']
    rules = (
        Rule(LinkExtractor(
            allow=('/account/zjhtcmgs111\?start=\d+', 'vhot2.qqvideo.tc.qq.com', 'video.qq.com', )),
            callback='parse_pages',
            follow=True,
        ),
    )

    custom_settings = {
        # 'FILES_STORE': '/data/worker/spider/weixin_ergeng',
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.WeiXinErGengPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.WeiXinErGengUserAgentMiddleware': 400,
            'audio_video_get.middlewares.WeiXinErGengDupFilterMiddleware': 1,
        },
    }

    def parse_pages(self, response):
        sel_list = response.xpath('//div[@class="feed_item_question"]')
        for sel in sel_list:
            item = WeiXinErGengItem()
            item['host'] = 'weixin_ergeng'
            item['stack'] = []
            item['download'] = 0
            item['file_dir'] = r'/data/worker/spider/weixin_ergeng'
            # item['file_dir'] = r'D:\python\scrapy\audio_video_get\Video\weixin_ergeng'
            item['info'] = {
                'title': sel.xpath('.//a[@class="question_link"]/text()').extract()[0].strip(),
                'link': sel.xpath('.//a[@class="question_link"]/@href').extract()[0],
                'date': sel.xpath('.//span[@class="timestamp"]/text()').extract()[0].strip(),
                'author': 'zjhtcmgs111',
            }
            url = urljoin('http://chuansong.me', sel.xpath('.//a[@class="question_link"]/@href').extract()[0])
            item['url'] = url
            item['file_name'] = get_md5(url)
            yield scrapy.Request(url=url, meta={'item': item}, callback=self.parse_info)

    def parse_info(self, response):
        item = response.meta['item']
        url = 'http://h5vv.video.qq.com/getinfo'
        item['media_type'], result = self.__video_or_audio(response.body)
        self.logger.info('type: {}, result: {} url: {}'.format(item['media_type'], result, response.url))
        if item['media_type'] == 'video':
            guid, params = self._get_info(result)
            meta = {
                'guid': guid,
                'item': item,
            }
            yield scrapy.FormRequest(url, method='GET', meta=meta, formdata=params, callback=self.parse_video_url)
        elif item['media_type'] == 'audio':
            item['media_urls'] = [result]
            t = urlparse(result).path.split('.')
            item['file_name'] += ('.' + t[1]) if ((len(t) >= 2) and t[1]) else '.mp3'
            yield item

    @staticmethod
    def __video_or_audio(text):
        result = re.findall(r'vid=(.*?)[&|"]', text)
        if result:
            return 'video', result[0]

        result = re.findall(r'audiourl="(.*?)"', text)
        if result:
            return 'audio', result[0]

        return '', None

    def parse_video_url(self, response):
        item = response.meta['item']
        guid = response.meta['guid']
        try:
            json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        else:
            if json_data['exem'] != 0:
                self.logger.warning('url: {}, exem: {}'.format(item['url'], json_data['exem']))
                if 'msg' in json_data:
                    self.logger.warning('url: {}, msg: {}'.format(item['url'], json_data['msg']))
                return

        url, ext = self._get_video_info(guid, json_data)
        if url is None:
            self.logger.error('url: {}, error: {}'.format(item['url'], ext))
            return
        item['media_urls'] = [url]
        # item['file_urls'] = [url]
        item['file_name'] += ext
        return item

    def _get_info(self, vid):
        g = '11001'  # from platform in d
        h = vid  # from vids in d
        i = 'v5010'
        k = 1
        f = str(int(time.time()))
        qv_rmt, qv_rmt2 = self._func_xx(g, h, i, k, f)
        guid = ''.join([str(hex(int(16 * random.random()))[2:]) for _ in range(32)])
        params = {
            'platform': '11001',
            'charge': '0',
            'otype': 'json',
            'ehost': 'http://v.qq.com',
            'sphls': '1',
            'sb': '1',
            'nocache': '0',
            '_rnd': str(int(time.time())),

            'guid': guid,
            'appVer': 'V2.0Build9370',
            'vids': vid,
            'defaultfmt': 'auto',
            '_qv_rmt': qv_rmt,
            '_qv_rmt2': qv_rmt2,
            'sdtfrom': 'v5010',
            'callback': 'tvp_request_getinfo_callback_' + str(int(1e6 * random.random())),
        }
        return guid, params

    @staticmethod
    def _get_video_info(guid, json_data):
        try:
            url = urljoin(json_data['vl']['vi'][0]['ul']['ui'][0]['url'], json_data['vl']['vi'][0]['fn'])
            params = {
                'vkey': json_data['vl']['vi'][0]['fvkey'],
                'br': json_data['vl']['vi'][0]['br'],
                'platform': '2',
                'level': json_data['vl']['vi'][0]['level'],
                'sdtfrom': 'v5010',
                'guid': guid,
                # 'fmt': json_data['vl']['vi'][0]['pl'][0]['pd'][0]['fmt'],
                'fmt': 'auto',
            }
            file_name = json_data['vl']['vi'][0]['fn']
        except Exception as err:
            return None, str(err)

        url += '?' + '&'.join(['='.join([k, str(v)]) for k, v in params.items()])
        return url, os.path.splitext(file_name)[1]

    @staticmethod
    def _func_b(a, b):
        return c_int(((a >> 1) + (b >> 1) << 1) + (1 & a) + (1 & b)).value

    def _func_ha(self, d):
        c = [0 | c_int(int(4294967296 * abs(math.sin(index + 1)))).value for index in range(64)]
        # j = unescape(encodeURI(d))
        j = d
        k = len(j)
        i = [0 for _ in range(k)]
        for m in range(k):
            i[m >> 2] |= (ord(j[m]) or 128) << 8 * (m % 4)
        i[k >> 2] = c_int(i[k >> 2] | c_int(128 << (8 * (k % 4))).value).value
        e = 1732584193
        f = -271733879
        l = [1732584193, -271733879, ~e, ~f]
        a = 16
        d = (k + 8 >> 6) * a + 14
        i[d] = 8 * k
        m = 0
        while d > m:
            h, k = 0, l
            while h < 64:
                e, f, g, t = k[1], k[2], k[3], k[3]
                x = self._func_b(k[0], c_int([e & f | ~e & g, g & e | ~g & f, e ^ f ^ g, f ^ (e | ~g)][h >> 4]).value)
                k = h >> 4
                y = self._func_b(c[h], i[[h, 5 * h + 1, 3 * h + 5, 7 * h][k] % a + m])
                g = self._func_b(x, y)
                k = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, a, 23, 6, 10, 15, 21][4 * k + h % 4]
                k = [t, self._func_b(e, c_int(g << k | (c_uint(g).value >> 32 - k)).value), e, f]
                h += 1
            for index in range(3, -1, -1):
                l[index] = self._func_b(l[index], k[index])
            m += a

        d = ''
        for h in range(32):
            if a == 16:
                d += str(hex(l[h >> 3] >> 4 * (1 ^ 7 & h) & 15)[2:])
            else:
                raise NotImplementedError
        # d = 'bd81608610f369f8c6423d95ba319041'
        return d

    @staticmethod
    def _func_hex_to_string(a):
        a = a[2:] if '0x' == a[:2] else a
        return ''.join([unichr(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    @staticmethod
    def _func_url_enc(a, b, c):
        m, l = 0, ''
        url_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        while m < len(a):
            d = ord(a[m])
            f = ord(a[m + 1]) if (m + 1 < len(a)) else 0
            g = ord(a[m + 2]) if (m + 2 < len(a)) else 0
            m += 3
            if 15 == m:
                l += 'A' + b + c
            h = d >> 2
            i = (3 & d) << 4 | f >> 4
            j = (15 & f) << 2 | g >> 6
            k = 63 & g
            if f == -1:
                j = k = 64
            elif g == -1:
                k = 64
            l += url_str[h] + url_str[i] + url_str[j] + url_str[k]

        return l

    @staticmethod
    def _func_temp_calc(a, b):
        return ''.join([chr(ord(a[i]) ^ ord(b[i % 4])) for i in range(len(a))])

    @staticmethod
    def _func_u1(a, b):
        return ''.join([a[i] for i in range(b, len(a), 2)])

    def _func_xx(self, a, b, c, d, f):
        g = h = ''
        f = f if f is not None else str(int(time.time()))

        j = self._func_hex_to_string(self._func_ha(''.join([a, b, f, seed, g, h, str(d), c])))
        k = self._func_url_enc(self._func_temp_calc(j, seed), str(d), f)
        l = self._func_url_enc(self._func_temp_calc(j, "86FG@hdf"), str(d), f)
        m = self._func_u1(k, 0)
        n = self._func_u1(k, 1)
        return m, n
