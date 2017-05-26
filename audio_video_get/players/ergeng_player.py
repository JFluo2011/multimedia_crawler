# -*- coding: utf-8 -*-

import re
import time
import json
import random
import base64

from base_player import BasePlayer
from audio_video_get.common import get_md5


class ErgengPlayer(BasePlayer):
    name = 'ergeng_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(ErgengPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.url = 'http://videojj.com/api/videos/v'
        self.method = 'GET'
        self.params = self.__get_params()

    def parse_video(self, response):
        pass

    def get_video_info(self, response):
        # TODO: FIX
        pass

    def __get_params(self):
        # TODO: FIX
        base64.b64encode()
        app_key = self.kwargs['app_key']
        video_id = self.kwargs['video_id']
        member_host = self.kwargs['member_host']
        media_id = self.kwargs['media_id']
        # video_url = member_host + '/api/video/vod/?id=' + media_id + '&site=bve&callback=?'
        callback = 'jQuery' + re.sub(r'\D', '', '@VERSION' + str(random.random()))

        params = {
            'callback': callback,
        }
        return params
