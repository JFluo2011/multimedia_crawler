# -*- coding: utf-8 -*-
import re
import os
import time
import json
import random
import base64

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ..items import ErGengItem
from ..common import get_md5


class ErGengSpider(CrawlSpider):
    name = "ergeng"
    download_delay = 2
    # allowed_domains = ["ergengtv.com"]
    start_urls = ['http://www.ergengtv.com/video/list/']

    rules = (
        Rule(
            LinkExtractor(allow=('www.ergengtv.com/video/\d+.html', )),
            callback='parse_items',
            follow=True,
        ),
    )

    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.ErGengPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.ErGengUserAgentMiddleware': 400,
            'audio_video_get.middlewares.ErGengDupFilterMiddleware': 1,
        },
    }
    definitionCount = 0
    video_url = 'http://api.letvcloud.com/gpc.php'

    def parse_items(self, response):
        # sel = response.xpath('//div[contains(@class, "new-video-info")')
        item = ErGengItem()
        item['host'] = 'ergeng'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
        item['url'] = response.url
        item['file_name'] = get_md5(item['url'])
        try:
            item['info'] = {
                # 'title': sel.xpath('./h3/text()').extract()[0].strip(),
                'title': re.findall(r'"user_nickname": "(.*?)"', response.body)[0],
                'link': response.url,
                'date': time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(float(re.findall(r'"create_at": (\d+),', response.body)[0]))),
                'author': re.findall(r'"title": "(.*?)"', response.body)[0],
            }
        except Exception as err:
            self.logger.warning('page: {}, url: {}, error: {}'.format(response.url, item['url'], str(err)))
        params = self.__get_params(response)
        yield scrapy.FormRequest(url=self.video_url, method='GET', meta={'item': item}, formdata=params,
                                 callback=self.parse_download_url)

    def parse_download_url(self, response):
        item = response.meta['item']
        json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        try:
            # r = re.findall(r'"cdn_url":"(.*?hd=0.*?)"', json_data)
            segs = json_data['data']['videoinfo']['medialist'][0]['urllist']
            item['media_urls'] = [base64.b64decode(seg['url']) for seg in segs]
            item['file_name'] += '.' + json_data['data']['videoinfo']['title'].split('.')[-1]
            return item
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return None

    def __get_params(self, response):
        uu = re.findall(r'"uu":"(.*?)"', response.body)[0]
        lang = re.findall(r'"lang":"(.*?)"', response.body)[0]
        vu = re.findall(r'"vu":"(.*?)"', response.body)[0]
        pu = re.findall(r'"pu":(.*?)}', response.body)[0]
        cf = 'html5'
        ran = int(time.time())
        sign = get_md5(''.join([str(i) for i in [cf, uu, vu, ran]]) + "fbeh5player12c43eccf2bec3300344")
        uuid = self.__creatUuid() + '_' + str(self.definitionCount)
        params = {
            'ver': '2.4',
            'page_url': response.url,
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

    def __creatUuid(self):
        a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        a = ','.join(a).split(',')
        b = [0] * 32
        d = 16
        for c in range(0,32) :
            b[c] = a[random.randint(0,d)]
        return ''.join(map(str,b))
