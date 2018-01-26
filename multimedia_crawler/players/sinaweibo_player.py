# -*- coding: utf-8 -*-
import re
import urllib

import scrapy

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.common.v_qq_common import VQQCom


class SinaWeiBoPlayer(BasePlayer):
    name = 'sinaweibo_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(SinaWeiBoPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.v_qq_com = VQQCom()
        self.url = self.kwargs['player_url']
        self.method = 'GET'
        self.params = {}

    def parse_video(self, response):
        item = response.meta['item']
        item['info']['author'] = response.xpath('//span[@class="W_f14 L_autocut bot_name W_fl"]/text()').extract_first(default='')
        item['info']['date'] = response.xpath('//div[@class="broad_time W_f12"]/text()').extract_first(default='')
        item['info']['intro'] = response.xpath('//div[@class="info_txt W_f14"]/text()').extract_first(default='')
        item['info']['play_count'] = re.findall(r'play_count=(.*?)[&\"]', response.body)[0]
        urls = re.findall(r'video_src=(.*?)[&\"]', response.body)
        if not urls:
            self.logger.error('url: {}, error: did not get any URL'.format(self.page_url))
            return
        item['media_urls'] = []
        for url in urls:
            url = urllib.unquote(url)
            if ('http' not in url) or ('https' not in url):
                url = 'http:' + url
            item['media_urls'].append(url)
        item['file_name'] = get_md5(item['url']) + '.mp4'

        return item

