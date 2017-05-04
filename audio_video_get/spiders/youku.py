# -*- coding: utf-8 -*-
import os
import re
import time
import json

import scrapy

from ..items import YouKuItem
from ..common import get_md5


class YoukuSpider(scrapy.Spider):
    name = "youku"
    download_delay = 2
    # allowed_domains = ["youku.com"]
    start_urls = ['http://i.youku.com/u/UMzE4MTU1MDEwMA==']

    custom_settings = {
        # 'FILES_STORE': 'Video/youku',
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.YoukuPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            # 'audio_video_get.middlewares.TouTiaoDupFilterMiddleware': 1,
        },
    }
    # files_store = os.path.join(os.path.basename('.'), custom_settings['FILES_STORE'])
    # if not os.path.exists(files_store):
    #     os.makedirs(files_store)

    def parse(self, response):
        params = {
            'spm': (re.findall(r'meta name="data-spm" content="(.*?)"', response.body)[0] + '.' +
                    re.findall(r'body class="yk-w970" data-spm="(\d+)"', response.body)[0] + '.0.0')
        }
        url = 'http://i.youku.com/u/UMzE4MTU1MDEwMA==/videos'
        yield scrapy.FormRequest(url, method='GET', formdata=params, meta={'first_page': True},
                                 callback=self.parse_video_list)

    def parse_video_list(self, response):
        sel_video_list = response.xpath('//div[@class="v va"]')
        for sel in sel_video_list:
            item = YouKuItem()
            item['host'] = 'youku'
            item['isVideo'] = 'true'
            item['info'] = ''
            item['stack'] = []
            item['downloaded'] = 0
            # item['localDir'] = ''
            item['localDir'] = '/data/worker/spider/youku'
            url = sel.xpath('div[@class="v-link"]/a/@href').extract()[0]
            item['url'] = url
            item['file'] = get_md5(url)
            yield scrapy.Request(url=url, meta={'item': item}, callback=self.parse_video_url)
        if response.meta['first_page']:
            pages = response.xpath('//ul[@class="yk-pages"]/li').xpath('.//a/@href').extract()
            for page in pages[:-1]:
                url = 'http://i.youku.com' + page
                # yield scrapy.FormRequest(url, method='GET', formdata=params, callback=self.parse_video_list)
                yield scrapy.Request(url=url, meta={'first_page': False}, callback=self.parse_video_list)

    def parse_video_url(self, response):
        item = response.meta['item']
        try:
            # vid = re.findall(r'vid=(.*?)"', response.body)[0]
            vid = re.findall(r'id_(.*?).html', response.url)[0]
        except Exception as err:
            print response.url, str(err)
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
            item['blocks'] = [seg['cdn_url'] for seg in segs]
            item['file'] += '.' + re.findall(r'st/(.*?)/fileid', item['blocks'][0])[0]
            return item
        except Exception, err:
            print str(err)
            pass

