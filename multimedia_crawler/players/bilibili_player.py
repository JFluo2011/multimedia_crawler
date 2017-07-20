# -*- coding: utf-8 -*-

import json

import scrapy
import xmltodict

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.common.bilibili_common import BiLiBiLiCommon


class BiLiBiLiPlayer(BasePlayer):
    name = 'bilibili_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(BiLiBiLiPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.bilibili_common = BiLiBiLiCommon()
        self.method = 'GET'
        self.url = 'http://api.bilibili.com/view'
        self.params = self.__get_params()

    def parse_video(self, response):
        item = response.meta['item']
        url = 'https://interface.bilibili.com/playurl'
        if not self.__get_json(response):
            return
        try:
            item['info']['play_count'] = self.json_data['play']
            item['info']['intro'] = self.json_data['description']
            item['info']['date'] = self.json_data['created_at']
            item['info']['author'] = self.json_data['author']
        except:
            pass

        try:
            cid = self.json_data['list'][0]['cid']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return

        params = self.bilibili_common.get_params(cid)
        yield scrapy.FormRequest(url=url, method='GET', meta={'item': item},
                                 formdata=params, callback=self.parse_video_urls)

    def parse_video_urls(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(json.dumps(xmltodict.parse(response.body)))
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return
        try:
            item['media_urls'] = [json_data['video']['durl']['url']]
            item['file_name'] = get_md5(self.page_url) + '.mp4'
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return
        else:
            if not item['media_urls']:
                self.logger.error('url: {}, error: did not get any URL in the json data'.format(self.page_url))
                return

        return item

    def __get_json(self, response):
        try:
            self.json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            return True

    def __get_params(self):
        aid = self.kwargs['aid']
        app_key = self.kwargs['app_key']
        params = {
            'type': 'json',
            'appkey': app_key,
            'id': aid,
            'page': '1',
        }
        return params
