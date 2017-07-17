# -*- coding: utf-8 -*-
import re
import os
import time
import json
import math

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5, WebUser


class YouKuSpider(scrapy.Spider):
    name = "youku"
    download_delay = 20
    # allowed_domains = ["youku.com"]
    users = [
        WebUser(id='UMTQ5OTEzNjU1Ng==', name='Imba_TV', ks3_name='imba_tv'),
        # WebUser(id='UMzE4MTU1MDEwMA==', name='即刻video', ks3_name='jike_video'),
    ]
    base_url = 'http://i.youku.com/u/{}/videos'

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.YouKuDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for user in self.users:
            url = self.base_url.format(user.id)
            yield scrapy.Request(url, method='GET', meta={'user': user})

    def parse(self, response):
        user = response.meta['user']
        count = int(response.xpath('//h3[@node-type="hdTitle"]/following-sibling::span/text()'
                                   ).extract()[0][1:-1].replace(',', ''))

        params = {
            'spm': 'a2hzp.8253869.0.0',
            'order': '1',
            'last_item': '',
            # 'last_vid': re.search(r'last_vid=(\d+)', response.body),
        }
        page, current, num = 1, 0, 50
        while current < count:
            params['page'] = str(page)
            # params['last_pn'] = i
            yield scrapy.FormRequest(url=response.url.split('?')[0], method='GET', meta={'user': user},
                                     formdata=params, callback=self.parse_items)
            current = num * page
            page += 1

    def parse_items(self, response):
        user = response.meta['user']
        sel_video_list = response.xpath('//div[@class="v va"]')
        for sel in sel_video_list:
            item = MultimediaCrawlerItem()
            item['host'] = 'youku'
            item['media_type'] = 'video'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name, user.ks3_name)
            item['url'] = 'http:' + sel.xpath('div[@class="v-link"]/a/@href').extract()[0]
            item['file_name'] = get_md5(item['url'])

            item['info'] = {
                'title': sel.xpath('.//div[@class="v-meta-title"]/a/@title').extract_first(default='').strip(),
                'link': item['url'],
                'date': sel.xpath('.//span[@class="v-publishtime"]/text()').extract_first(default=''),
                'author': user.name,
                'play_count': sel.xpath('.//span[@class="v-num"]/text()').extract_first(default=''),
            }
            params = {
                'spm': (re.search(r'meta name="data-spm" content="(.*?)"', response.body).group(1) + '.' +
                        re.search(r'body class="yk-w970" data-spm="(\d+)"', response.body).group(1) + '.0.0')
            }
            yield scrapy.FormRequest(url=item['url'], method='GET', meta={'item': item}, formdata=params,
                                     callback=self.parse_video_url)

    def parse_video_url(self, response):
        item = response.meta['item']
        vid = re.search(r'id_(.*?).html|$', response.url).group(1)
        if vid is None:
            self.logger.error('url: {}, error: failed to find vid'.format(response.url))
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
            item['media_urls'] = [seg['cdn_url'] for seg in segs]
            item['file_name'] += '.' + re.findall(r'st/(.*?)/fileid', item['media_urls'][0])[0]
            return item
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return None

