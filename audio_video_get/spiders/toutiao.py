# -*- coding: utf-8 -*-
import re
import os
import math
import time
import json
import random
import binascii
import base64

import scrapy
from scrapy.conf import settings

from ..common import get_md5
from ..items import TouTiaoItem


class ToutiaoSpider(scrapy.Spider):
    name = "toutiao"
    download_delay = 5
    # user_ids = ['6975800262', '50590890693', '5857206714', '6264649967', '6373263682',
    #             '6905052877', '6887101617', '6886776520']
    user_ids = ['6264649967', '6373263682', '6905052877', '6887101617', '6886776520']
    base_url = 'http://www.toutiao.com/c/user/article/'
    custom_settings = {
        'FILES_STORE': 'Video/toutiao',
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.ToutiaoPipeline': 100,
            # 'audio_video_get.pipelines.ToutiaoFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.TouTiaoDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for user_id in self.user_ids:
            params = self._get_params(user_id)
            yield scrapy.FormRequest(self.base_url, method='GET', formdata=params)

    def parse(self, response):
        json_data = json.loads(response.body)
        if json_data['has_more'] != 0:
            max_behot_time = json_data['next']['max_behot_time']
            user_id = re.findall(r'user_id=(\d+)', response.url)[0]
            for data in json_data['data']:
                item = TouTiaoItem()
                item['stack'] = []
                item['download'] = 0
                item['host'] = 'toutiao'
                item['media_type'] = 'video'
                # item['file_dir'] = '/data/worker/spider/toutiao'
                item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
                if 'item_id' in data:
                    item['url'] = 'http://www.toutiao.com/i' + data['item_id'] + '/'
                else:
                    item['url'] = data['display_url'].replace('group/', 'a')
                item['file_name'] = get_md5(item['url'])
                item['media_urls'] = [item['url']]
                item['info'] = {
                    'title': data['title'],
                    'intro': data['abstract'],
                    'album': '',
                    'author_id': user_id,
                    'author': data['source'],
                }
                if 'toutiao' in item['url']:
                    yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_video_id)
                else:
                    yield item

            params = self._get_params(user_id, max_behot_time)
            yield scrapy.FormRequest(self.base_url, method='GET', formdata=params)

    def parse_video_id(self, response):
        item = response.meta['item']
        try:
            video_id = re.findall(r"videoid:[ ]*?'(.*?)'", response.body)[0]
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(response.url, str(err)))
            return

        url = 'http://ib.365yg.com/video/urls/v/1/toutiao/mp4/' + video_id
        r = str(random.random())[2:]
        path = '/video/urls/v/1/toutiao/mp4/{video_id}?r={r}'.format(video_id=video_id, r=r)
        s = binascii.crc32(bytes(path))
        n = 0
        s = s >> n if s >= 0 else (s + 0x100000000) >> n
        params = {
            'r': r,
            's': str(s),
        }
        yield scrapy.FormRequest(url, method='GET', meta={'item': item},
                                 formdata=params, callback=self.parse_video_url)

    def parse_video_url(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body_as_unicode())
            video_url = base64.b64decode(json_data['data']['video_list']['video_1']['main_url']).decode('utf-8')
            ext = json_data['data']['video_list']['video_1']['vtype']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return

        item['file_name'] += '.' + ext
        item['media_urls'] = [video_url]
        self.logger.info('url: {}'.format(item['url']))
        return item

    @staticmethod
    def _get_params(user_id, max_behot_time=0, t=None):
        params_as, params_cp = '479BB4B7254C150', '7E0AC8874BB0985'
        if not t:
            t = math.floor(time.time() * 1000 / 1e3)
            t = int(t)
        i = hex(int(t))[2:].upper()  # "58DC72B1"
        e = get_md5(str(t)).upper()
        if 8 == len(i):
            s = e[0:5]
            o = e[-5:]
            a = l = ''
            for n in range(0, 5):
                a += s[n] + i[n]
                l += i[n + 3] + o[n]
            params_as, params_cp = 'A1' + a + i[-3:], i[0:3] + l + 'E1'

        params = {
            'page_type': '0',
            'user_id': user_id,
            'max_behot_time': str(max_behot_time),
            'count': '20',
            'as': params_as,
            'cp': params_cp,
        }
        return params

