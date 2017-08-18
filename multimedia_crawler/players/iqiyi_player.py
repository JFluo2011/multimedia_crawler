# -*- coding: utf-8 -*-
import re
import json
import time
import random

import scrapy

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5, base_n


class IQiYiPlayer(BasePlayer):
    name = 'iqiyi_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(IQiYiPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.url = 'http://cache.video.qiyi.com' + self.__get_params()
        self.method = 'GET'
        self.params = {}

    def parse_video(self, response):
        item = response.meta['item']
        item['info']['player'] = 'iqiyi'
        try:
            json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        else:
            if not json_data or json_data['code'] == 'A00001':
                self.logger.error('url: {}, error: get video link failed'.format(item['url']))
                return

        try:
            url_prefix = json_data['data']['vp']['du']
            # lst = json_data['data']['vp']['tkl'][0]['vs'][0]['fs']
            lst = sorted(json_data['data']['vp']['tkl'][0]['vs'], key=lambda x: x['vsize'])[0]['fs']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return

        item['file_name'] += '.' + lst[0]['l'].split('?')[0].split('.')[-1]
        if item['info'].get('play_count', 0) == 0:
            meta = {
                'item': item,
                'url_prefix': url_prefix,
                'lst': lst,
            }
            tvid = self.kwargs['tvid']
            base_url = 'http://mixer.video.iqiyi.com/jp/mixin/videos/{}?callback=window.Q.__callbacks__.{}&status=1'
            temp = base_n(int(2147483648 * random.random()), 36)
            url = base_url.format(tvid, temp)
            yield scrapy.Request(url, method='GET', meta=meta, callback=self.parse_play_count)
        else:
            for l in lst:
                item['info']['count'] = len(lst)
                url = url_prefix + l['l']
                yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_download_url)

    def parse_play_count(self, response):
        item = response.meta['item']
        lst = response.meta['lst']
        url_prefix = response.meta['url_prefix']
        try:
            json_data = json.loads(response.body[response.body.find('(')+1: response.body.find(')')])
            item['info']['play_count'] = json_data['data']['playCount']
            item['info']['comments_count'] = json_data['data']['commentCount']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        if len(lst) == 1:
            return
        for l in lst:
            item['info']['count'] = len(lst)
            url = url_prefix + l['l']
            yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_download_url)

    def parse_download_url(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        item['media_urls'] = [json_data['l']]
        return item

    @staticmethod
    def __get_macid():
        macid = ''
        chars = 'abcdefghijklnmopqrstuvwxyz0123456789'
        size = len(chars)
        for i in range(32):
            macid += list(chars)[random.randint(0, size - 1)]
        return macid

    @staticmethod
    def __get_vf(url_params):
        lst = [url_params]
        for j in range(8):
            for k in range(4):
                v4 = 13 * (66 * k + 27 * j) % 35
                v8 = (v4 + 88) if (v4 >= 10) else (v4 + 49)
                lst.append(chr(v8))
        return get_md5(''.join(lst))

    def __get_params(self):
        tvid = self.kwargs['tvid']
        vid = self.kwargs['vid']
        tm = int(time.time() * 1000)
        src = ('/vps?tvid=' + tvid + '&vid=' + vid + '&v=0&qypid=' + tvid + '_12&src=01012001010000000000&t=' +
               str(tm) + '&k_tag=1&k_uid=' + self.__get_macid() + '&rs=1')
        vf = self.__get_vf(src)
        return src + '&vf=' + vf
