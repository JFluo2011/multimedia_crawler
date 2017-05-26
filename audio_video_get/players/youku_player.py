# -*- coding: utf-8 -*-

import re
import time
import json

import scrapy

from base_player import BasePlayer
from audio_video_get.common import get_md5


class YouKuPlayer(BasePlayer):
    name = 'youku_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(YouKuPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.url = self.kwargs['player_url']
        self.method = 'GET'
        self.params = {}

    def parse_video(self, response):
        item = response.meta['item']
        url = 'https://api.youku.com/players/custom.json'
        params = {
            'refer': self.url,
            'client_id': re.findall(r'client_id = "\d+"', response.body)[0],
            'video_id': self.url.split('/')[-1],
            'version': '1.0',
            'type': 'h5',
            'embsig': '',
            'callback': 'json' + str(int(time.time() * 1000)),
        }
        yield scrapy.FormRequest(url=url, method='GET', meta={'item': item},
                                 formdata=params, callback=self.parse_video_custom)

    def parse_video_custom(self, response):
        item = response.meta['item']
        json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        vid = self.url.split('/')[-1]
        url = 'https://ups.youku.com/ups/get.json'
        params = {
            'vid': vid,
            'ccode': '0590',
            'client_ip': '0.0.0.0',
            'client_ts': str(int(time.time())),
            'utid': 'aKCuEcCdq38CAbaWLjWeW3TI',
            'r': json_data['stealsign'],
            'callback': 'json' + str(int(time.time() * 1000)),
        }
        yield scrapy.FormRequest(url=url, method='GET', meta={'item': item},
                                 formdata=params, callback=self.parse_video_urls)

    def parse_video_urls(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.text[response.body.find('(') + 1: -1])
            code = json_data['code']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return
        else:
            if code != 0:
                self.logger.error('url: {}, code: {}'.format(self.page_url, str(code)))
                return

        try:

            item['media_urls'] = [data['cdn_url'] for data in json_data['data']['stream'][0]['segs']]
            item['file_name'] = get_md5(self.page_url) + '.' + re.findall(r'st/(.*?)/fileid', item['media_urls'][0])[0]
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return
        else:
            if not item['media_urls']:
                self.logger.error('url: {}, error: did not get any URL in the json data'.format(self.page_url))
                return

        return item
