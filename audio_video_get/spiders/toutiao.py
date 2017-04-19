# -*- coding: utf-8 -*-
import re
import os
import math
import time
import json
import random
import binascii
import base64
import logging

import scrapy
import requests
from scrapy.conf import settings

from ..common import get_md5
from ..items import TouTiaoItem


class ToutiaoSpider(scrapy.Spider):
    name = "toutiao"
    download_delay = 3
    # FILES_STORE = os.path.join(settings['BASE_PATH'], name)

    def parse(self, response):
        json_data = json.loads(response.body)
        if json_data['has_more'] != 0:
            # base_url = ('http://www.toutiao.com/c/user/article/?page_type=0&user_id={user_id}&'
            #             'max_behot_time={max_behot_time}&count=20&as={AS}&cp={cp}')
            max_behot_time = json_data['next']['max_behot_time']
            user_id = re.findall(r'user_id=(\d+)', response.url)[0]
            param_as, param_cp = self._get_params()
            for data in json_data['data']:
                item = TouTiaoItem()
                item['unique_url'] = item['link'] = data['display_url']
                item['name'] = data['title']
                item['intro'] = data['abstract']
                item['album'] = ''
                item['author_id'] = user_id
                item['author'] = data['source']
                if 'toutiao' in item['link']:
                    yield scrapy.Request(url=data['display_url'], meta={'item': item}, callback=self.parse_download_url)
                else:
                    item['file_urls'] = [item['link']]
                    item['file_name'] = get_md5(item['link'])
                    yield item

            params = {
                'page_type': '0',
                'user_id': user_id,
                'max_behot_time': max_behot_time,
                'count': '20',
                'as': param_as,
                'cp': param_cp,
            }
            url = 'http://www.toutiao.com/c/user/article/'
            # yield scrapy.FormRequest(url, method='GET', formdata=params)
            yield scrapy.Request(url=url, body=json.dumps(params), callback=self.parse)

    def parse_download_url(self, response):
        headers = {
            'User-Agent': random.choice(settings['USER_AGENTS'])
        }
        item = response.meta['item']
        video_id = self._get_video_id(item['link'], headers)
        if video_id:
            url = 'http://ib.365yg.com/video/urls/v/1/toutiao/mp4/' + video_id
            video_url = self._get_video_url(url, video_id, headers)
            if video_url:
                item['link'], item['file_urls'] = video_url, [video_url]
                item['file_name'] = get_md5(video_url)
            return item

    @staticmethod
    def _get_video_id(url, headers):
        r = requests.get(url=url, headers=headers)
        return re.findall(r"videoid:[ ]*?'(.*?)'", r.text)[0] if r.status_code == 200 else None

    @staticmethod
    def _get_video_url(url, video_id, headers):
        video_url = None
        r = str(random.random())[2:]
        path = '/video/urls/v/1/toutiao/mp4/{video_id}?r={r}'.format(video_id=video_id, r=r)
        s = binascii.crc32(bytes(path))
        n = 0
        s = s >> n if s >= 0 else (s + 0x100000000) >> n
        params = {
            'r': r,
            's': s,
        }
        r = requests.get(url=url, headers=headers, params=params)
        if r.status_code != 200:
            return None
        try:
            video_url = base64.b64decode(r.json()['data']['video_list']['video_1']['main_url'])
        except Exception as err:
            msg = ('get video url failed, url={url}. error: {err}'.
                   format(url=url, err=err))
            logging.error(msg)

        return video_url.decode('utf-8') if video_url else None

    @staticmethod
    def _get_params(t=None):
        if not t:
            t = math.floor(time.time() * 1000 / 1e3)
            t = int(t)
        i = hex(int(t))[2:].upper()  # "58DC72B1"
        e = get_md5(str(t)).upper()
        if 8 != len(i):
            return {'as': "479BB4B7254C150", 'cp': '7E0AC8874BB0985'}

        s = e[0:5]
        o = e[-5:]
        a = l = ''
        for n in range(0, 5):
            a += s[n] + i[n]
            l += i[n + 3] + o[n]
        return 'A1' + a + i[-3:], i[0:3] + l + 'E1'

    def start_requests(self):
        user_ids = ['6975800262', '50590890693', '5857206714']
        # user_ids = self.user_group.values()
        # base_url = ('http://www.toutiao.com/c/user/article/?page_type=0&user_id={user_id}&max_behot_time=0&'
        #             'count=20&as={AS}&cp={cp}')
        base_url = 'http://www.toutiao.com/c/user/article/'
        for user_id in user_ids:
            param_as, param_cp = self._get_params()
            params = {
                'page_type': '0',
                'user_id': user_id,
                'max_behot_time': '0',
                'count': '20',
                'as': param_as,
                'cp': param_cp,
            }
            yield scrapy.FormRequest(base_url, method='GET', formdata=params)

