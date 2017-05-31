# -*- coding: utf-8 -*-
import re
import os

from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ..items import AudioVideoGetItem
from ..common import get_md5


class FeiDieShuoSpider(CrawlSpider):
    name = "feidieshuo"
    download_delay = 10
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
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def parse_video(self, response):
        item = AudioVideoGetItem()
        item['host'] = 'feidieshuo'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
        item['url'] = response.url
        item['file_name'] = get_md5(item['url'])

        try:
            item['info'] = {
                'title': response.xpath('//div[@class="t-word-text"]/h3/text()').extract()[0].strip(),
                'link': item['url'],
                'date': response.xpath('//div[@class="time"]/strong/text()').extract()[0],
                'author': 'feidieshuo',
                # 'album': response.xpath('//div[@class="word-content"]/p/text()').extract()[0].strip(),
            }
        except Exception as err:
            self.logger.warning('page: {}, url: {}, error: {}'.format(response.url, item['url'], str(err)))
        item['media_urls'] = [''.join(re.findall(r'videourl:\s*(.*?),',
                                                 response.body)[0].split('+')).replace('"', '')]
        item['file_name'] += '.' + item['media_urls'][0].split('.')[-1]
        return item
