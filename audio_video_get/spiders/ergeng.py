# -*- coding: utf-8 -*-
import re
import os
import time

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from audio_video_get.items import ErGengItem
from audio_video_get.players.letv_player import LetvPlayer
from audio_video_get.players.qq_player import QQPlayer
from audio_video_get.players.ergeng_player import ErgengPlayer
from audio_video_get.players.youku_player import YouKuPlayer


class ErGengSpider(CrawlSpider):
    name = "ergeng"
    download_delay = 5
    # allowed_domains = ["www.ergengtv.com"]
    # start_urls = ['http://www.ergengtv.com/video/list/', 'http://www.ergengtv.com/project/issue/']
    start_urls = ['http://www.ergengtv.com/project/issue/']

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
            # 'scrapy.pipelines.files.FilesPipeline': 200,
            'audio_video_get.pipelines.ErGengPipeline': 100,
            # 'audio_video_get.pipelines.YoukuFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.ErGengUserAgentMiddleware': 400,
            'audio_video_get.middlewares.ErGengDupFilterMiddleware': 1,
        },
    }

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
        item = ErGengItem()
        item['host'] = 'ergeng'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
        item['url'] = response.url
        try:
            item['info'] = {
                'title': re.findall(r'"user_nickname": "(.*?)"', response.body)[0],
                'link': item['url'],
                'date': time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(float(re.findall(r'"create_at": (\d+),', response.body)[0]))),
                'author': re.findall(r'"title": "(.*?)"', response.body)[0],
            }
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            # return

        player = self.__get_player(item['url'], response)
        if player is None:
            self.logger.error('url: {}, error: does not match any player'.format(item['url']))
            return
        yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                 formdata=player.params, callback=player.parse_video)

    def __get_player(self, page_url, response):
        is_thirdparty = re.findall(r'"is_thirdparty"\s*:\s*(\d+)', response.body)[0]
        if re.findall(r'letv.com', response.body):
            player = self.__get_letv_player(page_url, response)
        elif re.findall(r'v.qq.com', response.body) and (is_thirdparty == '1'):
            player = self.__get_qq_player(page_url, response)
        elif re.findall(r'player.youku.com', response.body) and (is_thirdparty == '1'):
            player = self.__get_youku_player(page_url, response)
        # elif is_thirdparty == '0':
        #     player = self.__get_qq_player(page_url, response)
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

    def __get_youku_player(self, page_url, response):
        player_url = re.findall(r'"(//player.youku.com/embed/.*?)"', response.body)[0]
        if 'http' not in player_url:
            page_url = 'http:' + player_url
        return YouKuPlayer(self.logger, page_url, player_url=player_url)

    def __get_ergeng_player(self, page_url, response):
        # TODO: FIX
        app_key = 'NJoeGIN8-'
        video_id = ''
        p = '@VERSION'
        member_host = re.findall(r'member_host\s*=\s*"(.*?)"', response.body)[0]
        media_id = re.findall(r'"media_id"\s*:\s*(\d+)', response.body)[0]
        return ErgengPlayer(self.logger, page_url, app_key=app_key, video_id=video_id,
                            member_host=member_host, media_id=media_id)
