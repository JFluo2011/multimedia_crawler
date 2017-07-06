# -*- coding: utf-8 -*-
import re
import json

import scrapy

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.common.v_qq_com import VQQCom


class QQPlayer(BasePlayer):
    seed = "#$#@#*ad"
    name = 'qq_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(QQPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.v_qq_com = VQQCom()
        self.url = 'http://h5vv.video.qq.com/getinfo'
        self.method = 'GET'
        self.params = self.__get_params()

    def parse_video(self, response):
        item = response.meta['item']
        # item['info']['play_count'] = response.xpath(xpath).extract_first(default='')
        # if (item['info']['play_count'] == '') and (not re.findall(r'专辑播放', response.body)):
        #     item['info']['play_count'] = (response.xpath('//em[@id="mod_cover_playnum"]/text()')
        #                                   .extract_first(default=''))
        if not self.__get_json(response):
            return

        if not self.__get_media_urls():
            return
        item['media_urls'] = self.media_urls
        item['file_name'] = self.file_name

        url = 'https://v.qq.com/x/page/{}.html'.format(self.kwargs['vid'])
        meta = {
            'item': item,
            'vid': self.kwargs['vid'],
        }
        yield scrapy.FormRequest(url, method='GET', meta=meta, callback=self.parse_play_count)

    def parse_play_count(self, response):
        item = response.meta['item']
        vid = response.meta['vid']
        xpath = '//span[@data-id="{}"]/text()'.format(vid)
        item['info']['play_count'] = response.xpath(xpath).extract_first(default='')
        if (item['info']['play_count'] == '') and (not re.findall(r'专辑播放', response.body)):
            item['info']['play_count'] = (response.xpath('//em[@id="mod_cover_playnum"]/text()')
                                          .extract_first(default=''))
        return item

    def __get_media_urls(self):
        url, result = self.v_qq_com.get_video_info(self.params['guid'], self.json_data)
        if url is None:
            self.logger.error('url: {}, error: {}'.format(self.page_url, result))
            return False
        elif not url:
            self.logger.error('url: {}, error: did not get any URL in the json data'.format(self.page_url))
            return False
        self.file_name = get_md5(self.page_url) + result
        self.media_urls = [url]
        return True

    def __get_json(self, response):
        try:
            self.json_data = json.loads(response.body[response.body.find('{'): response.body.rfind('}') + 1])
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return False
        else:
            code = self.json_data['exem']
            if code != 0:
                self.logger.error('url: {}, code: {}'.format(self.page_url, str(code)))
                return False
        return True

    def __get_params(self):
        return self.v_qq_com.get_info(self.kwargs['vid'])[-1]
