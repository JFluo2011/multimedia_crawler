# coding: utf-8

import re
import os
import json

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.players.youku_player import YouKuPlayer
from multimedia_crawler.players.qq_player import QQPlayer
from multimedia_crawler.players.bilibili_player import BiLiBiLiPlayer
from multimedia_crawler.players.letv_player import LetvPlayer


class BaoZouManHua(scrapy.Spider):
    name = 'baozoumanhua'
    download_delay = 5
    start_urls = ['http://baozoumanhua.com/api/v2/series/video_channels?page=' + str(i) for i in range(1, 7)]
    count = 0

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def parse(self, response):
        json_data = json.loads(response.body)
        base_url = 'http://baozoumanhua.com/video_channels/{}'
        for video_channel in json_data['video_channels']:
            url = base_url.format(video_channel['id'])
            yield scrapy.Request(url=url, meta={'video_channel_id': video_channel['id']}, callback=self.parse_channels)

    def parse_channels(self, response):
        video_channel_id = response.meta['video_channel_id']
        total = re.findall(r'第(\d+)集', response.body)[0]
        counts = (int(total) // 20) - 1 if (int(total) % 20 == 0) else (int(total) // 20)
        base_url = 'http://baozoumanhua.com/api/v2/video_channels/{}/videos?page={}'
        for page in range(counts+1):
            url = base_url.format(video_channel_id, page+1)
            yield scrapy.Request(url=url, callback=self.parse_video)

    def parse_video(self, response):
        base_url = 'http://baozoumanhua.com/videos/{}'
        json_data = json.loads(response.body)
        for data in json_data:
            url = base_url.format(data['id'])
            yield scrapy.Request(url=url, callback=self.parse_item)

    def parse_item(self, response):
        item = MultimediaCrawlerItem()
        item['host'] = 'baozoumanhua'
        item['media_type'] = 'video'
        item['stack'] = []
        item['download'] = 0
        item['extract'] = 0
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
        item['url'] = response.url
        item['info'] = {
            'link': item['url'],
            'title': (response.xpath(r'//h1[@class="v-title"]/text()').extract_first(default='').strip()),
            'intro': '',
            'author': 'baozoumanhua',
        }

        player = self.__get_player(item['url'], response)
        if player is None:
            self.logger.error('url: {}, error: does not match any player'.format(item['url']))
            return
        yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                 formdata=player.params, callback=player.parse_video)

    def __get_player(self, page_url, response):
        # if re.findall(r'bao.tv', response.body):
        #     player = self.__get_baotv_player(page_url, response)
        if re.findall(r'v.qq.com', response.body):
            player = self.__get_qq_player(page_url, response)
        elif re.findall(r'player.youku.com', response.body):
            player = self.__get_youku_player(page_url, response)
        # elif re.findall(r'letv.com', response.body):
        #     self.count += 1
        #     print self.count
        #     player = None
        #     player = self.__get_letv_player(page_url, response)
        elif re.findall(r'aid=', response.body):
            player = self.__get_bilibili_player(page_url, response)
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

    def __get_baotv_player(self, page_url, response):
        uu = re.search(r'"uu":"(.*?)"|$', response.body).group(1)
        lang = re.search(r'"lang":"(.*?)"|$', response.body).group(1)
        vu = re.search(r'"vu":"(.*?)"|$', response.body).group(1)
        pu = re.search(r'"pu":(.*?)}|$', response.body).group(1)
        # if all([uu, lang, vu, pu]):
        #     return LetvPlayer(self.logger, page_url, uu=uu, vu=vu, pu=pu, lang=lang)

    def __get_qq_player(self, page_url, response):
        vid = re.search(r'vid=(.*?)[&|"]|$', response.body).group(1)
        if vid is not None:
            return QQPlayer(self.logger, page_url, vid=vid)

    def __get_youku_player(self, page_url, response):
        video_id = re.search(r'sid/(.*?)/v.swf|$', response.body).group(1)

        if video_id is not None:
            player_url = 'http://player.youku.com/embed/' + video_id
            return YouKuPlayer(self.logger, page_url, player_url=player_url)
        else:
            player_url = re.search(r'"(.*?player.youku.com/embed/.*?)"|$', response.body).group(1)
            if player_url is not None:
                if 'http' not in player_url:
                    player_url = 'http:' + player_url
                return YouKuPlayer(self.logger, page_url, player_url=player_url)

    def __get_bilibili_player(self, page_url, response):
        app_key = '8e9fc618fbd41e28'
        aid = re.search(r'aid=(\d+)', response.text).group(1)
        if aid is not None:
            return BiLiBiLiPlayer(self.logger, page_url, app_key=app_key, aid=aid)
