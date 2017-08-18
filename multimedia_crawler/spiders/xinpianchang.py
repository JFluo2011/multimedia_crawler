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


class XinPianChangSpider(CrawlSpider):
# class XinPianChangSpider(scrapy.Spider):
    name = "xinpianchang"
    download_delay = 5
    start_urls = ['http://www.xinpianchang.com/']
    # start_urls = ['http://www.xinpianchang.com/channel/index/id-122/sort-like/page-38']
    # start_urls = ['http://www.xinpianchang.com/a18909']

    rules = (
        Rule(
            LinkExtractor(allow=('http://www.xinpianchang.com/a\d+.*?', )),
            callback='parse_video',
            # follow=True,
        ),
        Rule(
            LinkExtractor(allow=('http://www.xinpianchang.com/.*?', )),
        ),
    )

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
            'multimedia_crawler.middlewares.MultimediaCrawlerMiddleware': 500,
        }
    }

    def parse_video(self, response):
    # def parse(self, response):
        item = MultimediaCrawlerItem()
        item['host'] = 'xinpianchang'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['extract'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
        item['url'] = response.url.split('?')[0]
        item['file_name'] = get_md5(item['url'])
        item['info'] = {}
        item['info']['link'] = item['url']
        item['info']['title'] = response.xpath(r'/html/head/title/text()').extract_first(default='')
        item['info']['intro'] = response.xpath(r'//meta[@name="description"]/@content').extract_first(default='')
        item['info']['author'] = response.xpath(r'//meta[@property="article:author"]/@content').extract_first(default='')

        if response.xpath(r'//video[@id="xpc_video"]'):
            player = 'self'
            json_data = sorted(json.loads(re.findall(r'origins\s*=\s*(.*?),isTranscoding', response.body)[0]),
                               key=lambda element: int(element['filesize']))[0]
            item['info']['date'] = (time.strftime('%Y-%m-%d', time.localtime(int(json_data.get('addtime', 0))))
                                    if json_data.get('addtime', 0) != 0 else '')
            item['media_urls'] = [json_data.get('qiniu_url', None)]
            if item['media_urls'][0] is None:
                return
            item['file_name'] += '.' + item['media_urls'][0].split('.')[-1]
        else:
            player = self.__get_player(item['url'], response)
            if player is None:
                self.logger.error('url: {}, error: does not match any player'.format(response.url))
                return

        meta = {'item': item, 'player': player}
        video_id = re.findall(r'a(\d+)&', response.url.split('?')[0]+'&')
        yield scrapy.FormRequest(url='http://www.xinpianchang.com/index.php?app=article&ac=filmplay&ts=plat_views',
                                 method='POST', meta=meta, formdata={'id': video_id},
                                 callback=self.parse_info)

    def parse_info(self, response):
        item = response.meta['item']
        player = response.meta['player']
        json_data = json.loads(response.body)
        item['info']['play_count'] = json_data.get('views', 0)
        if player == 'self':
            yield item
        else:
            yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                     formdata=player.params, callback=player.parse_video)

    def __get_video_info(self, item, response):
        json_data = sorted(json.loads(re.findall(r'origins\s*=\s*(.*?),isTranscoding', response.body)[0]),
                           key=lambda element: int(element['filesize']))[0]
        item['info']['date'] = (time.strftime('%Y-%m-%d', time.localtime(int(json_data.get('addtime', 0))))
                                if json_data.get('addtime', 0) != 0 else '')
        item['media_urls'] = [json_data.get('qiniu_url', None)]
        if item['media_urls'][0] is None:
            return
        item['file_name'] = get_md5(item['url']) + '.' + item['media_urls'][0].split('.')[-1]

    def __get_player(self, page_url, response):
        if re.findall('youkuplayer', response.body):
            player = self.__get_youku_player(page_url, response)
        elif re.findall(r'v.qq.com', response.body):
            player = self.__get_qq_player(page_url, response)
        elif re.findall(r'iqiyi.com/v', response.body):
            player = self.__get_iqiyi_player(page_url, response)
        # elif re.findall(r'le.com/ptv/vplay', response.body):
        #     player = self.__get_letv_player(page_url, response)
        else:
            return None

        return player

    def __get_youku_player(self, page_url, response):
        video_id = re.search(r'vid\s*:\s*[\'\"](.*?)[\'\"]|$', response.body).group(1)
        if video_id:
            player_url = 'http://player.youku.com/embed/' + video_id
            return YouKuPlayer(self.logger, page_url, player_url=player_url)

    def __get_qq_player(self, page_url, response):
        vid = re.search(r'vid=(.*?)[&|"]|$', response.body).group(1)
        if vid is not None:
            return QQPlayer(self.logger, page_url, vid=vid)

    def __get_iqiyi_player(self, page_url, response):
        tvid, vid = response.xpath(r'//div[@id="link-report"]/@vid').extract_first(default='/').split('/')
        if all([tvid, vid]):
            return IQiYiPlayer(self.logger, page_url, tvid=tvid, vid=vid)
