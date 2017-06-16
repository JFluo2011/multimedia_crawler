# -*- coding: utf-8 -*-

import re
import time
import json
import random

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5


class ErgengPlayer(BasePlayer):
    name = 'ergeng_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(ErgengPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.method = 'GET'
        self.url, self.params = self.__get_params()

    def parse_video(self, response):
        item = response.meta['item']
        if not self.__get_json(response):
            return
        if not self.__get_media_urls():
            return
        item['media_urls'] = self.media_urls
        item['file_name'] = self.file_name
        return item

    def __get_media_urls(self):
        try:
            segs = self.json_data['msg']['segs']
            if not self.__get_urls(segs):
                self.logger.error('url: {}, error: no such video types'.format(self.page_url))
                return False
            self.file_name = get_md5(self.page_url) + '.' + self.media_urls[0].split('.')[-1]
        except Exception, err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            if not self.media_urls:
                self.logger.error('url: {}, error: did not get any URL in the json data'.format(self.page_url))
                return False
        return True

    def __get_urls(self, data):
        if 'HD' in data.keys():
            key = 'HD'
        elif '720p' in data.keys():
            key = '720p'
        elif '1080p' in data.keys():
            key = '1080p'
        else:
            return False
        self.media_urls = [data['url'] for data in data[key]]
        return True

    def __get_json(self, response):
        try:
            self.json_data = json.loads(response.body)
            code = self.json_data['status']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            if code != 0:
                self.logger.error('url: {}, code: {}'.format(self.page_url, str(code)))
                return False
        return True

    def __get_params(self):
        # base64.b64encode()
        # app_key = self.kwargs['app_key']
        # video_id = self.kwargs['video_id']
        member_host = ('http://' + self.kwargs['member_host']) if ('http://' not in self.kwargs['member_host']) else self.kwargs['member_host']
        media_id = self.kwargs['media_id']
        video_url = member_host + '/api/video/vod/?id=' + media_id + '&site=bve&callback=?'
        tmp = str(time.time()*1000)
        callback = 'jQuery' + re.sub(r'\D', '', '@VERSION' + str(random.random())) + tmp

        params = {
            'callback': callback,
            'id': media_id,
            'site': 'bve',
            '_': tmp,
        }
        return video_url, params
