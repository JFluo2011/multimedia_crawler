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
        # 'DOWNLOADER_MIDDLEWARES': {
        #     # 'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
        #     # 'audio_video_get.middlewares.TouTiaoDupFilterMiddleware': 1,
        # },
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
        yield scrapy.FormRequest(url, method='GET', formdata=params, callback=self.parse_page_list)

    def parse_page_list(self, response):
        self.parse_video_list(response)
        pages = response.xpath('//ul[@class="yk-pages"]/li').xpath('.//a/@href').extract()
        for page in pages[:-1]:
            # m, s = page.split('?', 2)
            url = 'http://i.youku.com' + page
            # s = '{"' + s + '"}'
            # s = s.replace('=', '":"')
            # s = s.replace('&', '","')
            # params = eval(s)
            # params['spm'] = response.url.split('=')[-1]
            # yield scrapy.FormRequest(url, method='GET', formdata=params, callback=self.parse_video_list)
            yield scrapy.Request(url=url,  callback=self.parse_video_list)

    def parse_video_list(self, response):
        sel_video_list = response.xpath('//div[@class="v va"]')
        for sel in sel_video_list:
            item = YouKuItem()
            item['host'] = 'youku'
            item['isVideo'] = 'true'
            item['info'] = ''
            item['stack'] = []
            item['downloaded'] = 0
            item['localDir'] = ''
            url = sel.xpath('div[@class="v-link"]/a/@href').extract()[0]
            item['url'] = url
            item['file'] = get_md5(url)
            yield scrapy.Request(url=url, meta={'item': item}, callback=self.parse_video_url)

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
            return item
        except Exception, err:
            print str(err)
            pass

