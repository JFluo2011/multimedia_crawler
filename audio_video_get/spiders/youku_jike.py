# -*- coding: utf-8 -*-
import re
import time
import json

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ..items import YouKuJiKeItem
from ..common import get_md5


class YouKuJiKeSpider(CrawlSpider):
    name = "youku_jike"
    download_delay = 2
    # allowed_domains = ["youku.com"]
    start_urls = ['http://i.youku.com/u/UMzE4MTU1MDEwMA==/videos']

    rules = (
        Rule(
            LinkExtractor(allow=('/i/UMzE4MTU1MDEwMA==/videos\?order=1&', )),
            callback='parse_pages',
            follow=True,
        ),
    )

    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.YouKuJiKePipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.YouKuJiKeDupFilterMiddleware': 1,
        },
    }

    def parse_pages(self, response):
        sel_video_list = response.xpath('//div[@class="v va"]')
        for sel in sel_video_list:
            item = YouKuJiKeItem()
            item['host'] = 'youku_jike'
            item['media_type'] = 'video'
            item['info'] = {
                'title': sel.xpath('.//div[@class="v-meta-title"]/a/text()').extract()[0].strip(),
                'link': sel.xpath('.//div[@class="v-meta-title"]/a/@href').extract()[0],
                'date': sel.xpath('.//span[@class="v-publishtime"]/text()').extract()[0],
                'author': 'UMzE4MTU1MDEwMA==',
            }
            item['stack'] = []
            item['download'] = 0
            item['file_dir'] = '/data/worker/spider/youku_jike'
            url = sel.xpath('div[@class="v-link"]/a/@href').extract()[0]
            item['url'] = url
            item['file_name'] = get_md5(url)
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

    @staticmethod
    def parse_download_url(response):
        item = response.meta['item']
        json_data = json.loads(response.body)
        try:
            # r = re.findall(r'"cdn_url":"(.*?hd=0.*?)"', json_data)
            segs = json_data['data']['stream'][0]['segs']
            item['media_urls'] = [seg['cdn_url'] for seg in segs]
            item['file_name'] += '.' + re.findall(r'st/(.*?)/fileid', item['media_urls'][0])[0]
            return item
        except Exception, err:
            print str(err)
            pass

