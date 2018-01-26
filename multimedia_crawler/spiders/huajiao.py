import re
import os
import time
import random
import json

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5


# class HuaJiaoSpider(scrapy.Spider):
class HuaJiaoSpider(CrawlSpider):
    name = "huajiao"
    download_delay = 2
    start_urls = ['http://www.huajiao.com/vl/']

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    rules = (
        Rule(LinkExtractor(allow=(r'v/\d+', )), callback='parse_video', follow=True, ),
        Rule(LinkExtractor(allow=(r'user/\d+', )), ),
    )

    def parse_video(self, response):
        item = MultimediaCrawlerItem()
        item['host'] = 'huajiao'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['extract'] = 0
        item['url'] = response.url
        item['file_name'] = get_md5(item['url']) + '.mp4'

        json_data = json.loads(re.findall(r'_DATA.feed\s*=\s*(.*?);', response.body)[0])
        uid = json_data['uinfo']['uid']
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name, uid)
        item['info'] = {
            'link': item['url'],
            'author': json_data['uinfo']['nickname'],
            'author_id': uid,
            'title': json_data['feed']['video_title'],
            'play_count': json_data['feed']['watches'],
            'date': json_data['feed']['addtime'],
        }
        item['media_urls'] = [json_data['feed']['video_url']]
        yield item
