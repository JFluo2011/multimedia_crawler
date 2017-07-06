# -*- coding: utf-8 -*-
import re
import os

from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5


class FeiDieShuoSpider(CrawlSpider):
    name = "feidieshuo"
    download_delay = 5
    allowed_domains = ["www.feidieshuo.com"]
    start_urls = ['http://www.feidieshuo.com/']

    rules = (
        Rule(
            LinkExtractor(allow=('/channel/\d+', '/media/load_more_channle_video?page=\d+&channelid=\d+')),
        ),
        Rule(
            LinkExtractor(allow=('/media/play/\d+', )),
            callback='parse_video',
            follow=True,
        ),
    )

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def parse_video(self, response):
        item = MultimediaCrawlerItem()
        item['host'] = 'feidieshuo'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
        item['url'] = response.url
        item['file_name'] = get_md5(item['url'])

        item['info'] = {
            'title': response.xpath('//div[@class="t-word-text"]/h3/text()')
                .extract_first(default='').strip(),
            'link': item['url'],
            'date': response.xpath('//div[@class="time"]/strong/text()').extract_first(default=''),
            'author': 'feidieshuo',
            'play_count': response.xpath('//div[@class="user"]/div[1]/span[1]/text()').extract_first(default=''),
            'comments_count': response.xpath('//div[@class="user"]/div[1]/span[2]/text()').extract_first(default=''),
            'intro': response.xpath('//div[@class="word-content"]/p/text()').extract_first(default='').strip(),
        }
        item['media_urls'] = [''.join(re.findall(r'videourl:\s*(.*?),', response.body)[0]
                                      .split('+')).replace('"', '')]
        item['file_name'] += '.' + item['media_urls'][0].split('.')[-1]
        return item

