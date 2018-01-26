# -*- coding: utf-8 -*-
import os

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5


class DayDayCookSpider(scrapy.Spider):
    name = "daydaycook"
    download_delay = 5
    start_urls = ['http://www.daydaycook.com/daydaycook/hk/website/recipe/list.do']

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        total_page = response.xpath('//a[@class="lastPage"]/@href').re(r'javascript:pageSkip\((\d+)\);')[0]
        params = {
            'categoryId': '',
            'categorySonId': '',
            'screenTechId': '',
            'screenTasteId': '',
            'screenTimeId': '',
            'sortKey': 'releaseDate',
            'clearSearch': '',
            'pageSize': '15',
            'sortField': '',
            'totalPage': total_page,
            'sortType': '',
        }
        for page in range(1, int(total_page)+1):
            params['currentPage'] = str(page)
            yield scrapy.FormRequest(url=response.url, method='POST', formdata=params, callback=self.parse_info)

    def parse_info(self, response):
        sels = response.xpath('//div[@class="resultList justify three"]/div[@class="box"]')
        for sel in sels:
            url = sel.xpath('a/@href').extract()[0].replace(':80', '')
            item = MultimediaCrawlerItem()
            item['host'] = 'daydaycook'
            item['media_type'] = 'video'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['url'] = response.url
            item['file_name'] = get_md5(item['url'])
            item['info'] = {}
            play_count_sel = sel.xpath('.//span[@class="number"]')
            item['info']['play_count'] = play_count_sel[len(play_count_sel) - 1].xpath('text()').extract_first('')
            item['info']['author'] = sel.xpath('span[@class="subtitle"]/text()').extract_first('by DayDayCook')
            yield scrapy.Request(url=url, meta={'item': item}, callback=self.parse_video)

    def parse_video(self, response):
        item = response.meta['item']
        sel = response.xpath('//div[@class="detailWood"]')
        item['info']['link'] = item['url']
        item['info']['title'] = sel.xpath('div[@class="title"]/text()').extract_first('').strip()
        item['info']['intro'] = sel.xpath('div[@class="des"]/text()').extract_first('').strip()
        if 'By DayDayCook' not in sel.xpath('div[@class="time"]/text()').extract_first(''):
            item['info']['data'] = sel.xpath('div[@class="time"]/text()').extract_first('')

        item['media_urls'] = response.xpath('//video[@id="videoPlay"]/source/@src').extract()
        item['file_name'] += response.xpath('//video[@id="videoPlay"]/source/@type').extract().split('/')[-1]

        return item
