# -*- coding: utf-8 -*-

from __future__ import division
import os
import re
import json
import time
import math
import random
from urlparse import urljoin

import scrapy
from scrapy.conf import settings

from audio_video_get.items import AudioVideoGetItem
from audio_video_get.common.common import get_md5
from audio_video_get.common.v_qq_com import VQQCom


class QQVideoSpider(scrapy.Spider):
    name = "qq_video"
    download_delay = 5
    # allowed_domains = ['chuansong.me', 'video.qq.com']
    users = {
        # '0093c8b4c792637609ad9e42a10507e0': '日食记',
        'jikezhishi': '即刻video',
        # 'kehua': '刻画',
        # 'yitiao': '一条',
        # 'vicechina': 'VICE中国 ',
        # '0713f8d7448192de': '一人食',
    }
    base_url = 'http://v.qq.com/vplus/{}/videos'

    custom_settings = {
        'ITEM_PIPELINES': {
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def __init__(self, name=None, **kwargs):
        super(QQVideoSpider, self).__init__(name, **kwargs)
        self.v_qq_com = VQQCom()

    def start_requests(self):
        for user in self.users.iteritems():
            url = self.base_url.format(user[0])
            yield scrapy.Request(url, method='GET', meta={'user': user})

    def parse(self, response):
        user = response.meta['user']
        num = 24
        count = response.xpath('//div[@id="headBgMod"]//ul[@class="user_count"]/li[3]/span[2]/text()').extract()[0]
        for page in range(1, int(math.ceil(int(count) / num)) + 1):
            aa = "1.9.1"
            callback = ''.join(['jQuery', re.sub(r'\D', '', aa + str(random.random())),
                                '_', str(int(time.time() * 1000))])
            params = {
                'otype': 'json',
                'pagenum': str(page),
                'callback': callback,
                'qm': '1',
                'num': str(num),
                'sorttype': '0',
                'orderflag': '0',
                'low_login': '1',
                'uin': re.search(r'data-vuin="(.*?)"', response.body).group(1),
                '_': str(int(time.time() * 1000)),
            }
            url = 'http://c.v.qq.com/vchannelinfo'
            yield scrapy.FormRequest(url, method='GET', meta={'user': user}, formdata=params, callback=self.parse_page)

    def parse_page(self, response):
        user = response.meta['user']
        json_data = json.loads(response.body[response.body.find('{'): response.body.rfind('}')+1])
        for data in json_data['videolst']:
            item = AudioVideoGetItem()
            item['host'] = 'qq_video'
            item['stack'] = []
            item['download'] = 0
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['url'] = urljoin('https://v.qq.com/x/page/', data['vid'] + '.html')
            item['info'] = {
                'title': data['title'],
                'link': item['url'],
                'play_count': data['play_count'],
                'date': data['uploadtime'],
                'author': user[1],
                'author_homepage': self.base_url.format(user[0]),
                'intro': data['desc'],
            }
            item['file_name'] = get_md5(item['url'])
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_info)

    def parse_info(self, response):
        item = response.meta['item']
        url = 'https://vv.video.qq.com/getinfo'
        guid, params = self.v_qq_com.get_info(response.url.split('/')[-1].split('.')[0])
        meta = {
            'guid': guid,
            'item': item,
        }
        yield scrapy.FormRequest(url, method='GET', meta=meta, formdata=params, callback=self.parse_video_url)

    def parse_video_url(self, response):
        item = response.meta['item']
        guid = response.meta['guid']
        try:
            json_data = json.loads(response.body[response.body.find('{'): response.body.rfind('}')+1])
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        else:
            if json_data['exem'] != 0:
                self.logger.warning('url: {}, exem: {}'.format(item['url'], json_data['exem']))
                if 'msg' in json_data:
                    self.logger.warning('url: {}, msg: {}'.format(item['url'], json_data['msg']))
                return

        url, ext = self.v_qq_com.get_video_info(guid, json_data)
        if url is None:
            self.logger.error('url: {}, error: {}'.format(item['url'], ext))
            return
        item['media_urls'] = [url]
        item['file_name'] += ext
        return item
