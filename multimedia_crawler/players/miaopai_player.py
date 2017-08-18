# -*- coding: utf-8 -*-
import re

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.common.v_qq_common import VQQCom


class MiaoPaiPlayer(BasePlayer):
    name = 'miaopai_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(MiaoPaiPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.v_qq_com = VQQCom()
        self.url = self.kwargs['player_url']
        self.method = 'GET'
        self.params = {}

    def parse_video(self, response):
        video_id = self.page_url.split('/')[-1].split('.')[0]
        item = response.meta['item']
        item['info']['author'] = response.xpath('//p[@class="personalDataN"]/a/text()').extract_first(default='')
        item['info']['date'] = response.xpath('//p[@class="personalDataT"]/span/text()').extract_first(default='')
        item['info']['play_count'] = response.xpath('//p[@class="personalDataT"]/span[2]/text()').extract_first(default='')
        item['info']['intro'] = response.xpath('//p[@class="viedoAbout"]/p/text()').extract_first(default='')
        item['media_urls'] = re.findall(r'[\'\"]videoSrc[\'\"]\s*:\s*[\'\"](.*?)[\'\"]', response.body)
        if not item['media_urls']:
            self.logger.error('url: {}, error: did not get any URL'.format(self.page_url))
            return
        item['file_name'] = get_md5(item['url']) + re.findall(r'{}(.*?)\?'.format(video_id), item['media_urls'][0])[0]

        return item
