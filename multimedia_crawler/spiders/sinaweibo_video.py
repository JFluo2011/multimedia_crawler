# -*- coding: utf-8 -*-

from __future__ import division
import os
import re
import json
import time

import scrapy
from lxml import etree
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5, WebUser
from multimedia_crawler.players.youku_player import YouKuPlayer
from multimedia_crawler.players.miaopai_player import MiaoPaiPlayer
from multimedia_crawler.players.sinaweibo_player import SinaWeiBoPlayer
from multimedia_crawler.players.kuaishou_player import KuaiShouPlayer


class SinaWeiBoVideoSpider(scrapy.Spider):
    name = "sinaweibo_video"
    download_delay = 5
    # allowed_domains = ['chuansong.me', 'video.qq.com']
    users = [
        # WebUser(id='1005053948713134', name='日食记', storage_name='rishiji'),
        # WebUser(id='1005055709892136', name='刘哔电影', storage_name='liuhuadianying'),
        # WebUser(id='1005053171948942', name='一人食', storage_name='yirenshi'),
        # WebUser(id='1005052163553891', name='VICE中国', storage_name='vicechina'),
        WebUser(id='1002061618051664', name='CCTV5', storage_name='cctv5'),
    ]
    base_url = 'http://www.weibo.com/p/{}/photos?type=video#place'

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.SinaWeiBoRotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def start_requests(self):
        for user in self.users:
            url = self.base_url.format(user.id)
            yield scrapy.Request(url, method='GET', meta={'user': user})

    def parse(self, response):
        user = response.meta['user']
        page = response.meta.get('page', 2)
        if page == 2:
            left = response.body.find('<div class="PCD_photo_album_v2" node-type="list">')
            right = response.body.find('<div class="WB_footer S_bg2" id="pl_common_footer">')
            source = response.body[left:right].decode('utf-8')
        else:
            source = json.loads(response.body)['data']
        selector = etree.HTML(source)
        if not selector.xpath('//div[@class="WB_cardwrap S_bg2"]'):
            return
        for sel in selector.xpath('//li[@class="photo_module"]'):
            url = sel.xpath('a/@href')[0].replace('://', '://www.')
            if url == '':
                # self.logger.warning(sel.xpath('a/div/text()')[0])
                continue
            item = MultimediaCrawlerItem()
            item['host'] = 'sinaweibo_video'
            item['media_type'] = 'video'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['info'] = {}
            try:
                item['info']['title'] = sel.xpath(r'a/div/text()')[0]
            except:
                pass

            # if 'gifshow' not in url:
            #     continue
            player = self.__get_player(url)
            if player is None:
                self.logger.warning(sel.xpath('a/div/text()')[0])
                self.logger.error('url: {}, error: does not match any player'.format(url))
                continue
            item['url'] = player.url
            item['info']['link'] = item['url']
            yield scrapy.FormRequest(url=player.url, method=player.method, meta={'item': item},
                                     formdata=player.params, callback=player.parse_video)

        url = 'http://www.weibo.com/p/aj/album/loading'
        action_data = selector.xpath('//div[@class="WB_cardwrap S_bg2"]/@action-data')[0]+'&'
        params = {
            'ajwvr': '6',
            'type': 'video',
            'viewer_uid': '',
            'page': str(page),
            'ajax_call': '1',
            '__rnd': str(int(time.time()*1000)),
            'owner_uid': re.findall(r'owner_uid=(\d+)&', action_data)[0],
            'page_id': user.id,
            'since_id': re.findall(r'since_id=(\d+)&', action_data)[0],
        }
        meta = {
            'user': user,
            'page': page+1,
        }
        yield scrapy.FormRequest(url=url, method='GET', meta=meta, formdata=params, callback=self.parse)

    def __get_player(self, page_url):
        if 'video.weibo.com' in page_url:
            player = self.__get_sinaweibo_player(page_url)
        # elif 'video.sina.com' in page_url:
        #     player = self.__get_sina_player(page_url)
        elif 'miaopai' in page_url:
            player = self.__get_miaopai_player(page_url)
        elif 'youku' in page_url:
            player = self.__get_youku_player(page_url)
        elif 'gifshow' in page_url:
            player = self.__get_kuaishou_player(page_url)
        else:
            return None

        return player

    def __get_youku_player(self, page_url):
        video_id = re.findall(r'id_(.*?)\.', page_url)
        if video_id:
            # player_url = 'http://www.player.youku.com/embed/' + video_id[0]
            player_url = 'http://player.youku.com/embed/' + video_id[0]
            return YouKuPlayer(self.logger, page_url, player_url=player_url)

    def __get_miaopai_player(self, page_url):
        return MiaoPaiPlayer(self.logger, page_url, player_url=page_url)

    def __get_sinaweibo_player(self, page_url):
        video_id = page_url.split('?')[-1]
        player_url = 'http://www.weibo.com/tv/v/FeYaud0RD?' + video_id
        return SinaWeiBoPlayer(self.logger, page_url, player_url=player_url)

    def __get_sina_player(self, page_url):
        video_id = page_url.split('?')[-1]
        player_url = 'http://www.weibo.com/tv/v/FeYaud0RD?' + video_id
        return SinaWeiBoPlayer(self.logger, page_url, player_url=player_url)

    def __get_kuaishou_player(self, page_url):
        usr_id = re.findall(r'userId=(\d+)&', page_url+'&')[0]
        video_id = re.findall(r'photoId=(\d+)&', page_url+'&')[0]
        player_url = 'https://www.kuaishou.com/photo/{}/{}?'.format(usr_id, video_id) + page_url.split('?')[-1]
        return KuaiShouPlayer(self.logger, page_url, player_url=player_url)
