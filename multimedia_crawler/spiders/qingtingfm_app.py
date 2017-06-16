# -*- coding: utf-8 -*-
import re
import os
import json

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5


class QingTingFMAppSpider(scrapy.Spider):
    name = "qingtingfm_app"
    download_delay = 10
    # allowed_domains = []
    start_urls = ['http://api2.qingting.fm/v5/media/categories/507']

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.QingTingFMAppUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def parse(self, response):
        category_id = response.url.split('/')[-1]
        json_data = json.loads(response.body)
        if json_data['errorno'] != 0:
            self.logger.error('get qingtingfm app category {} failed, error msg: {}'.
                              format(category_id, json_data['errormsg']))
            return

        base_url = 'http://api2.qingting.fm/v5/media/categories/{}'
        for data in json_data['data']:
            url = base_url.format(data['id'])
            yield scrapy.Request(url=url, callback=self.parse_ids)

    def parse_ids(self, response):
        category_id = response.url.split('/')[-1]
        json_data = json.loads(response.body)
        if json_data['errorno'] != 0:
            self.logger.error('get qingtingfm app category {} failed, error msg: {}'.
                              format(category_id, json_data['errormsg']))
            return

        base_url = 'http://api2.qingting.fm/v5/media/categories/{}/channels/order/recommend/curpage/{}/pagesize/10'
        for page in range(int(json_data['totalpage'])):
            url = base_url.format(category_id, page)
            yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        category_id = re.findall(r'categories/(\d+)/channels', response.url)[0]
        json_data = json.loads(response.body)
        if json_data['errorno'] != 0:
            self.logger.error('get qingtingfm app category {} failed, error msg: {}'.
                              format(category_id, json_data['errormsg']))
            return

        page_size = 30
        base_url = 'http://42.120.60.147/v5/media/channels/{}/programs/curpage/{}/pagesize/{}'
        for data in json_data['data']:
            page, current = 1, 0
            count = data['programsCnt']
            while current < count:
                current += page_size
                url = base_url.format(data['id'], page, page_size)
                page += 1
                yield scrapy.Request(url=url, callback=self.parse_channels)

    def parse_channels(self, response):
        channels_id = re.findall(r'channels/(\d+)/programs', response.url)[0]
        json_data = json.loads(response.body)
        if json_data['errorno'] != 0:
            self.logger.error('get qingtingfm app channel {} failed, error msg: {}'.
                              format(channels_id, json_data['errormsg']))
            return

        for data in json_data['data']:
            item = MultimediaCrawlerItem()
            item['host'] = 'qingtingfm_app'
            item['media_type'] = 'audio'
            item['stack'] = []
            item['download'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
            item['url'] = response.url
            item['file_name'] = get_md5(item['url'])

            item['info'] = {
                'title': data.get('name', ''),
                'link': item['url'],
                'intro': data.get('desc', ''),
                'date': data.get('updatetime', ''),
                'author': data.get('cname', ''),
            }

            item['media_urls'] = ['http://upod.qingting.fm/' + data['mediainfo']['download']]
            item['file_name'] += '.' + item['media_urls'][0].split('.')[-1]
            return item
