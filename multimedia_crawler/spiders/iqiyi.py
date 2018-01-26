# -*- coding: utf-8 -*-
import re
import os
import datetime

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5, WebUser
from multimedia_crawler.players.iqiyi_player import IQiYiPlayer


class IQiYiSpider(scrapy.Spider):
    name = "iqiyi"
    download_delay = 5
    users = [
        WebUser(id='1190686219', name='造物集', storage_name='zaowuji'),
        # WebUser(id='1233288265', name='微在涨姿势', storage_name='weizaizhangzishi'),
    ]
    # allowed_domains = ["youku.com"]
    base_url = 'http://www.iqiyi.com/u/{}/v'

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
            # 'multimedia_crawler.pipelines.IQiYiPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
        'SPIDER_MIDDLEWARES': {
            # 'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
            'multimedia_crawler.middlewares.MultimediaCrawlerMiddleware': 500,
        }
    }

    def start_requests(self):
        for user in self.users:
            params = {
                'page': '1',
                'video_type': '1',
            }
            yield scrapy.FormRequest(self.base_url.format(user.id), method='GET', formdata=params, meta={'user': user})

    def parse(self, response):
        user = response.meta['user']
        selectors = response.xpath(r'//li[@j-delegate="colitem"]')
        for sel in selectors:
            item = MultimediaCrawlerItem()
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 0
            item['host'] = 'iqiyi'
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name, user.storage_name)
            item['url'] = sel.xpath('./div[1]/a/@href').extract()[0]
            item['file_name'] = get_md5(item['url'])
            date = sel.xpath('./div[2]/p[2]/span[2]/text()').extract_first(default='').strip()
            if date == '':
                pass
            elif u'昨日上传' in date:
                date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date = date[:-2]
            item['info'] = {'intro': '', 'date': date, 'link': item['url']}
            item['info']['author'] = user.name
            item['info']['title'] = sel.xpath('./div[1]/a/img/@title').extract_first(default='')
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_params)
        sel_next_page = response.xpath(u'//a[text()="下一页"]')
        if sel_next_page:
            params = {
                'page': sel_next_page.xpath(r'./@data-pagecheckouter-p').extract()[0],
                'video_type': '1',
            }
            yield scrapy.FormRequest(url=response.url.split('?')[0], method='GET', formdata=params, meta={'user': user})

    def parse_params(self, response):
        item = response.meta['item']
        tvid = re.search(r'param\[\'tvid\'\]\s+=\s+"(\d+)"|$', response.body).group(1)
        vid = re.search(r'param\[\'vid\'\]\s+=\s+"(.*?)"|$', response.body).group(1)
        if not all([tvid, vid]):
            return

        player = IQiYiPlayer(self.logger, item['url'], tvid=tvid, vid=vid)
        yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                 formdata=player.params, callback=player.parse_video)

