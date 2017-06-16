# -*- coding: utf-8 -*-
import re
import os
import time

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from audio_video_get.items import AudioVideoGetItem
from audio_video_get.players.letv_player import LetvPlayer
from audio_video_get.players.qq_player import QQPlayer
from audio_video_get.players.ergeng_player import ErgengPlayer
from audio_video_get.players.youku_player import YouKuPlayer


# class ErGengSpider(CrawlSpider):
class ErGengSpider(scrapy.Spider):
    name = "ergeng"
    download_delay = 10
    # allowed_domains = ["www.ergengtv.com"]
    # start_urls = ['http://www.ergengtv.com/video/list/', 'http://www.ergengtv.com/project/issue/']
    start_urls = ['http://www.ergengtv.com/video/1573.html']

    rules = (
        Rule(LinkExtractor(allow=('project/issue/0_\d+.html', 'video/list/0_\d+.html', ), )),
        Rule(
            LinkExtractor(allow=('video/\d+.html', 'project/\d+.html', )),
            callback='parse_video',
            follow=True,
        ),
    )

    custom_settings = {
        'ITEM_PIPELINES': {
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.MobileUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    # def parse_video(self, response):
    def parse(self, response):
        item = AudioVideoGetItem()
        item['host'] = 'ergeng'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
        item['url'] = response.url
        timestamp = re.search(r'"create_at"\s*:\s*(\d+),|$', response.body).group(1)
        item['info'] = {
            'link': item['url'],
            'title': (response.xpath(r'//div[contains(@class, "new-video-info")]/h3/text()').
                      extract_first(default='').strip()),
            'intro': response.xpath(r'//div[contains(@class, "tj")]/text()').extract_first(default='').strip(),
            'date': time.strftime('%Y-%m-%d', time.localtime(int(timestamp))) if timestamp is not None else '',
            'author': re.search(r'"user_nickname"\s*:\s*"(.*?)"|$', response.body).group(1),
        }

        player = self.__get_player(item['url'], response)
        if player is None:
            self.logger.error('url: {}, error: does not match any player'.format(item['url']))
            return
        yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                 formdata=player.params, callback=player.parse_video)

    def __get_player(self, page_url, response):
        is_thirdparty = re.search(r'"is_thirdparty"\s*:\s*(\d+)|$', response.body).group(1) or -1

        if re.findall(r'letv.com', response.body):
            player = self.__get_letv_player(page_url, response)
        elif re.findall(r'v.qq.com', response.body):
            player = self.__get_qq_player(page_url, response)
        elif re.findall(r'player.youku.com', response.body):
            player = self.__get_youku_player(page_url, response)
        elif is_thirdparty == '0':
            player = self.__get_ergeng_player(page_url, response)
        else:
            return None

        return player

    def __get_letv_player(self, page_url, response):
        uu = re.search(r'"uu":"(.*?)"|$', response.body).group(1)
        lang = re.search(r'"lang":"(.*?)"|$', response.body).group(1)
        vu = re.search(r'"vu":"(.*?)"|$', response.body).group(1)
        pu = re.search(r'"pu":(.*?)}|$', response.body).group(1)
        if all([uu, lang, vu, pu]):
            return LetvPlayer(self.logger, page_url, uu=uu, vu=vu, pu=pu, lang=lang)

    def __get_qq_player(self, page_url, response):
        vid = re.search(r'vid=(.*?)[&|"]|$', response.body).group(1)
        if vid is not None:
            return QQPlayer(self.logger, page_url, vid=vid)

    def __get_youku_player(self, page_url, response):
        player_url = re.search(r'"(//player.youku.com/embed/.*?)"|$', response.body).group(1)
        if player_url is not None:
            if 'http' not in player_url:
                player_url = 'http:' + player_url
            return YouKuPlayer(self.logger, page_url, player_url=player_url)

    def __get_ergeng_player(self, page_url, response):
        # TODO: FIX
        app_key = 'NJoeGIN8-'
        video_id = ''
        p = '@VERSION'
        member_host = re.search(r'member_host\s*=\s*"(.*?)"|$', response.body).group(1)
        media_id = re.search(r'"media_id"\s*:\s*(\d+)|$', response.body).group(1)
        if all([member_host, media_id]):
            return ErgengPlayer(self.logger, page_url, app_key=app_key, video_id=video_id,
                                member_host=member_host, media_id=media_id)
