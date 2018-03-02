# -*- coding: utf-8 -*-
import re
import os
import json
import time

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.players.youku_player import YouKuPlayer
from multimedia_crawler.players.qq_player import QQPlayer
from multimedia_crawler.players.iqiyi_player import IQiYiPlayer


class ResourceXinPianChangSpider(scrapy.Spider):
    name = "resource_xinpianchang"
    download_delay = 5

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.XinPianChangDupFilterMiddleware': 1,
        },
        'SPIDER_MIDDLEWARES': {
            # 'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
            # 'multimedia_crawler.middlewares.MultimediaCrawlerMiddleware': 500,
        }
    }

    def start_requests(self):
        t = int(time.time()*1000)
        yield scrapy.Request('https://resource.xinpianchang.com/audio/list', meta={'t': t})

    def parse(self, response):
        t = response.meta['t']
        base_url = 'https://resource.xinpianchang.com{}'
        for sel in response.xpath(r'//ul[@class="music-list"]/li'):
            item = MultimediaCrawlerItem()
            item['host'] = 'resource_xinpianchang'
            item['media_type'] = 'audio'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 1
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['url'] = base_url.format(sel.xpath(r'.//a[@class="goto-music"]/@href').extract()[0])
            item['file_name'] = get_md5(item['url']) + '.mp3'
            item['info'] = {}
            item['info']['link'] = item['url']
            item['info']['title'] = sel.xpath(r'.//span[@class="music-title"]/text()').extract()[0]
            item['info']['author'] = sel.xpath(r'.//span[contains(@class, "music-producer")]/text()').extract()[0]
            item['media_urls'] = sel.xpath(r'.//dl[@class="music-single"]/@data-music').extract()
            yield item

        for page in range(2, 370):
            t += 1
            url = 'https://resource.xinpianchang.com/api/audio/moreList/{}?categories=&_={}'
            yield scrapy.FormRequest(url=url.format(page, t), method='GET', callback=self.parse_other_page)

    def parse_other_page(self, response):
        base_url = 'https://resource.xinpianchang.com/audio/detail/{}'
        json_data = json.loads(response.body)
        for data in json_data['results']:
            item = MultimediaCrawlerItem()
            item['host'] = 'resource_xinpianchang'
            item['media_type'] = 'audio'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 1
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['url'] = base_url.format(data['uuid'])
            item['file_name'] = get_md5(item['url']) + '.mp3'
            item['info'] = {}
            item['info']['link'] = item['url']
            item['info']['title'] = data['name']
            item['info']['author'] = data['producer']['name']
            item['media_urls'] = [data['preview']]
            yield item
