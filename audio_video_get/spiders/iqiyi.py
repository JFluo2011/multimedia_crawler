# -*- coding: utf-8 -*-
import re
import os
import time
import random
import json
import datetime

import scrapy
from scrapy.conf import settings

from audio_video_get.items import AudioVideoGetItem
from ..common import get_md5


class IQiYiSpider(scrapy.Spider):
    name = "iqiyi"
    download_delay = 10
    # users = ['1190686219', '1233288265']
    users = ['1233288265']
    # allowed_domains = ["youku.com"]
    base_url = 'http://www.iqiyi.com/u/{}/v'

    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            # 'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
            'audio_video_get.pipelines.IQiYiPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 'audio_video_get.middlewares.MobileUserAgentMiddleware': 400,
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for user in self.users:
            params = {
                'page': '1',
                'video_type': '1',
            }
            yield scrapy.FormRequest(self.base_url.format(user), method='GET', formdata=params)

    def parse(self, response):
        selectors = response.xpath(r'//li[@j-delegate="colitem"]')
        for sel in selectors:
            item = AudioVideoGetItem()
            item['stack'] = []
            item['download'] = 0
            item['host'] = 'iqiyi'
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
            item['url'] = sel.xpath('./div[1]/a/@href').extract()[0]
            item['file_name'] = get_md5(item['url'])
            date = sel.xpath('./div[2]/p[2]/span[2]/text()').extract()[0].strip()
            if u'昨日上传' in date:
                date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date = date[:-2]
            item['info'] = {
                'title': sel.xpath('./div[1]/a/img/@title').extract()[0],
                'intro': '',
                'album': '',
                'date': date,
                'author': re.findall(r'u/(\d+)/v', response.url)[0],
            }
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_params)
        sel_next_page = response.xpath(u'//a[text()="下一页"]')
        if sel_next_page:
            params = {
                'page': sel_next_page.xpath(r'./@data-pagecheckouter-p').extract()[0],
                'video_type': '1',
            }
            yield scrapy.FormRequest(url=response.url.split('?')[0], method='GET', formdata=params)

    def parse_params(self, response):
        item = response.meta['item']
        tvid = re.findall(r'param\[\'tvid\'\]\s+=\s+"(\d+)"', response.body)[0]
        vid = re.findall(r'param\[\'vid\'\]\s+=\s+"(.*?)"', response.body)[0]
        tm = time.time()
        tm = int(tm) * 1000
        host = 'http://cache.video.qiyi.com'
        src = ('/vps?tvid=' + tvid + '&vid=' + vid + '&v=0&qypid=' + tvid + '_12&src=01012001010000000000&t=' +
               str(tm) + '&k_tag=1&k_uid=' + self.__get_macid() + '&rs=1')
        vf = self.__get_vf(src)
        url = host + src + '&vf=' + vf
        yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_video_urls)

    def parse_video_urls(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        else:
            if not json_data or json_data['code'] == 'A00001':
                self.logger.error('url: {}, error: get video link failed'.format(item['url']))
                return

        try:
            url_prefix = json_data['data']['vp']['du']
            lst = json_data['data']['vp']['tkl'][0]['vs'][0]['fs']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return

        item['file_name'] += '.' + lst[0]['l'].split('?')[0].split('.')[-1]
        for l in lst:
            url = url_prefix + l['l']
            yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_download_url)

    def parse_download_url(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        item['media_urls'] = [json_data['l']]
        # return json_data['l']
        return item

    @staticmethod
    def __get_macid():
        macid = ''
        chars = 'abcdefghijklnmopqrstuvwxyz0123456789'
        size = len(chars)
        for i in range(32):
            macid += list(chars)[random.randint(0, size - 1)]
        return macid

    @staticmethod
    def __get_vf(url_params):
        lst = [url_params]
        for j in range(8):
            for k in range(4):
                v4 = 13 * (66 * k + 27 * j) % 35
                v8 = (v4 + 88) if (v4 >= 10) else (v4 + 49)
                lst.append(chr(v8))
        return get_md5(''.join(lst))
