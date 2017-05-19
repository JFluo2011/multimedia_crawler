# -*- coding: utf-8 -*-
import re
import os
import time

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

from audio_video_get.items import ErGengItem
from audio_video_get.players.letv_player import LetvPlayer
from audio_video_get.players.qq_player import QQPlayer


class ErGengSpider(CrawlSpider):
    name = "ergeng"
    download_delay = 4
    # allowed_domains = ["ergengtv.com"]
    start_urls = ['http://www.ergengtv.com/video/list/']

    rules = (
        Rule(
            # LinkExtractor(allow=('www.ergengtv.com/video/\d+.html', )),
            # LinkExtractor(allow=('http://www.ergengtv.com/video/list/0_.*?.html', )),
            LinkExtractor(allow=('http://www.ergengtv.com/video/list/0_1.html', )),
            callback='parse_pages',
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

    def __init__(self):
        super(ErGengSpider, self).__init__()

    def parse_pages(self, response):
        sel_list = response.xpath('//li[@class="eg-border new"]')
        for sel in sel_list:
            item = ErGengItem()
            item['host'] = 'ergeng'
            item['media_type'] = 'video'
            item['stack'] = []
            item['download'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
            item['url'] = 'http:' + sel.xpath('.//div[1]/a/@href').extract()[0]
            # item['file_name'] = get_md5(item['url'])
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_video)

    def parse_video(self, response):
        item = response.meta['item']
        try:
            item['info'] = {
                'title': re.findall(r'"user_nickname": "(.*?)"', response.body)[0],
                'link': response.url,
                'date': time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(float(re.findall(r'"create_at": (\d+),', response.body)[0]))),
                'author': re.findall(r'"title": "(.*?)"', response.body)[0],
            }
        except Exception as err:
            self.logger.warning('url: {}, error: {}'.format(item['url'], str(err)))

        player = self.__get_player(item['url'], response)
        if player is None:
            self.logger.error('url: {}, error: does not match any player'.format(item['url']))
            return
        url, method, params = player.get_params()

        meta = {
            'player': player,
            'url': url,
            'method': method,
            'params': params,
            'item': item,
        }
        yield scrapy.FormRequest(url=url, method=method, meta=meta, formdata=params,
                                 callback=self.parse_video_url)

    def parse_video_url(self, response):
        item = response.meta['item']
        player = response.meta['player']
        code, item['media_urls'], item['file_name'] = player.get_video_info(response)
        if code == 10071:
            self.logger.error('Anti-Spider, error code: {}'.format(code))
            raise CloseSpider('Anti-Spider')
        elif code == 0:
            if item['media_urls'] is not None:
                return item

    def __get_player(self, page_url, response):
        if re.findall(r'letv.com', response.body):
            player = self.__get_letv_player(page_url, response)
        elif re.findall(r'v.qq.com', response.body):
            player = self.__get_qq_player(page_url, response)
        else:
            return None

        return player

    def __get_letv_player(self, page_url, response):
        uu = re.findall(r'"uu":"(.*?)"', response.body)[0]
        lang = re.findall(r'"lang":"(.*?)"', response.body)[0]
        vu = re.findall(r'"vu":"(.*?)"', response.body)[0]
        pu = re.findall(r'"pu":(.*?)}', response.body)[0]
        return LetvPlayer(self.logger, page_url, uu=uu, vu=vu, pu=pu, lang=lang)

    def __get_qq_player(self, page_url, response):
        vid = re.findall(r'vid=(.*?)[&|"]', response.body)[0]
        return QQPlayer(self.logger, page_url, vid=vid)
