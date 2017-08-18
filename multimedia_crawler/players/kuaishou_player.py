# -*- coding: utf-8 -*-
import re

from base_player import BasePlayer
from multimedia_crawler.common.common import get_md5
from multimedia_crawler.common.v_qq_common import VQQCom


class KuaiShouPlayer(BasePlayer):
    name = 'kuaishou_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        super(KuaiShouPlayer, self).__init__(logger, page_url, *args, **kwargs)
        self.v_qq_com = VQQCom()
        self.url = self.kwargs['player_url']
        self.method = 'GET'
        self.params = {}

    def parse_video(self, response):
        item = response.meta['item']
        item['info']['author'] = (response.xpath('//div[@class="desc"]/div[@class="comment-wrap"]/div/h3/strong/text()')
                                  .extract_first(default=''))
        item['info']['date'] = (response.xpath('//div[@class="desc"]/div[@class="comment-wrap"]/div/h3/span/text()')
                                .extract_first(default=''))
        item['info']['intro'] = (response.xpath('//div[@class="desc"]/div[@class="comment-wrap"]/div/div/p/text()')
                                 .extract_first(default=''))
        item['info']['play_count'] = (response.xpath('//div[@class="desc"]/div[@class="comments-num"]/span[3]/text()')
                                      .extract_first(default=''))
        item['media_urls'] = response.xpath('//div[@class="video"]/video/@src').extract()
        if not item['media_urls']:
            self.logger.error('url: {}, error: did not get any URL'.format(self.page_url))
            return
        item['file_name'] = get_md5(item['url']) + '.' + item['media_urls'][0].split('.')[-1]

        return item
