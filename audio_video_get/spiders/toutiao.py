# -*- coding: utf-8 -*-
import re
import math
import time
import json
import random
import binascii
import base64
import logging
import requests

import scrapy
from scrapy.conf import settings
from pymongo import MongoClient

from ..common import get_md5
from ..items import TouTiaoItem


class ToutiaoSpider(scrapy.Spider):
    name = "toutiao"
    download_delay = 2
    # FILES_STORE = os.path.join(settings['BASE_PATH'], name)

    def __init__(self):
        super(ToutiaoSpider, self).__init__()
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])

    def parse(self, response):
        json_data = json.loads(response.body)
        if json_data['has_more'] != 0:
            max_behot_time = json_data['next']['max_behot_time']
            user_id = re.findall(r'user_id=(\d+)', response.url)[0]
            param_as, param_cp = self._get_params()
            for data in json_data['data']:
                item = TouTiaoItem()
                item['unique_url'] = item['video_url'] = data['display_url']
                item['name'] = data['title']
                item['intro'] = data['abstract']
                item['album'] = ''
                item['author_id'] = user_id
                item['author'] = data['source']
                if 'toutiao' in item['video_url']:
                    yield scrapy.Request(url=data['display_url'], meta={'item': item}, callback=self.parse_download_url)
                else:
                    item['file_urls'] = [item['video_url']]
                    yield item

            params = {
                'page_type': '0',
                'user_id': user_id,
                'max_behot_time': str(max_behot_time),
                'count': '20',
                'as': param_as,
                'cp': param_cp,
            }
            url = 'http://www.toutiao.com/c/user/article/'
            yield scrapy.FormRequest(url, method='GET', formdata=params)

    def parse_download_url(self, response):
        headers = {
            'User-Agent': random.choice(settings['USER_AGENTS'])
        }
        item = response.meta['item']
        if 'toutiao' not in item['unique_url']:
            item['file_urls'] = [item['unique_url']]
            return item
        video_id = self._get_video_id(item['unique_url'], headers)
        if video_id:
            url = 'http://ib.365yg.com/video/urls/v/1/toutiao/mp4/' + video_id
            video_url = self._get_video_url(url, video_id, headers)
            if video_url:
                item['video_url'], item['file_urls'] = video_url, [video_url]
                return item

    @staticmethod
    def _get_video_id(url, headers):
        video_id = None
        r = requests.get(url=url, headers=headers)
        try:
            video_id = re.findall(r"videoid:[ ]*?'(.*?)'", r.text)[0]
        except Exception as err:
            logging.error(err)
        return video_id

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
                   format(url=url, err=repr(err)))
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
        for result in self.col.find({'download': -1}):
            logging.error('redownload url {}'.format(result['unique_url']))
            item = TouTiaoItem()
            item['unique_url'] = result['unique_url']
            item['name'] = result['name']
            item['intro'] = result['intro']
            item['album'] = result['album']
            item['author_id'] = result['author_id']
            item['author'] = result['author']
            item['video_url'] = result['video_url']
            yield scrapy.FormRequest(url=result['unique_url'], meta={'item': item}, callback=self.parse_download_url)

        user_ids = ['6975800262', '50590890693', '5857206714']
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

