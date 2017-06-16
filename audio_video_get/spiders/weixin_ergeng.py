# coding: utf-8

import re
import os
import json
from urlparse import urljoin, urlparse

import scrapy
from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from audio_video_get.items import AudioVideoGetItem
from audio_video_get.common.common import get_md5
from audio_video_get.common.v_qq_com import VQQCom


class WeiXinErGengSpider(CrawlSpider):
    name = "weixin_ergeng"
    download_delay = 5
    # allowed_domains = ['chuansong.me', 'video.qq.com']
    start_urls = ['http://chuansong.me/account/zjhtcmgs111']

    rules = (
        Rule(LinkExtractor(
            allow=('/account/zjhtcmgs111\?start=\d+', 'vhot2.qqvideo.tc.qq.com', 'video.qq.com', )),
            callback='parse_pages',
            follow=True,
        ),
    )

    custom_settings = {
        'ITEM_PIPELINES': {
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.WeiXinErGengUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def __init__(self):
        super(WeiXinErGengSpider, self).__init__()
        self.v_qq_com = VQQCom()

    def parse_pages(self, response):
        sel_list = response.xpath('//div[@class="feed_item_question"]')
        for sel in sel_list:
            item = AudioVideoGetItem()
            item['host'] = 'weixin_ergeng'
            item['stack'] = []
            item['download'] = 0
            url = sel.xpath('.//a[@class="question_link"]/@href').extract_first(default='')
            if url == '':
                continue
            item['url'] = urljoin('http://chuansong.me', url)
            item['info'] = {
                'title': sel.xpath('.//a[@class="question_link"]/text()').extract_first(default='').strip(),
                'link': item['url'],
                'date': sel.xpath('.//span[@class="timestamp"]/text()').extract_first(default='').strip(),
                'author': 'zjhtcmgs111',
            }

            item['file_name'] = get_md5(item['url'])
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_video_or_audio)

    def parse_video_or_audio(self, response):
        item = response.meta['item']
        item['media_type'], result = self.__video_or_audio(response.body)
        item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
        self.logger.info('type: {}, result: {} url: {}'.format(item['media_type'], result, response.url))
        if item['media_type'] == 'video':
            url = 'https://v.qq.com/x/page/{}.html'.format(result)
            meta = {
                'item': item,
                'vid': result,
            }
            yield scrapy.FormRequest(url, method='GET', meta=meta, callback=self.parse_info)
        elif item['media_type'] == 'audio':
            item['media_urls'] = [result]
            t = urlparse(result).path.split('.')
            item['file_name'] += ('.' + t[1]) if ((len(t) >= 2) and t[1]) else '.mp3'
            yield item

    def parse_info(self, response):
        item = response.meta['item']
        vid = response.meta['vid']
        xpath = '//span[@data-id="{}"]/text()'.format(vid)
        item['info']['play_count'] = response.xpath(xpath).extract_first(default='')
        if (item['info']['play_count'] == '') and (not re.findall(r'专辑播放', response.body)):
            item['info']['play_count'] = (response.xpath('//em[@id="mod_cover_playnum"]/text()')
                                          .extract_first(default=''))

        url = 'http://h5vv.video.qq.com/getinfo'
        guid, params = self.v_qq_com.get_info(vid)
        meta = {
            'guid': guid,
            'item': item,
        }
        yield scrapy.FormRequest(url, method='GET', meta=meta, formdata=params, callback=self.parse_video_url)

    @staticmethod
    def __video_or_audio(text):
        result = re.search(r'vid=(.*?)[&|"]|$', text).group(1)
        if result is not None:
            return 'video', result

        result = re.search(r'audiourl="(.*?)"|$', text).group(1)
        if result is not None:
            return 'audio', result

        return '', None

    def parse_video_url(self, response):
        item = response.meta['item']
        guid = response.meta['guid']
        try:
            json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        else:
            if json_data['exem'] != 0:
                self.logger.warning('url: {}, exem: {}'.format(item['url'], json_data['exem']))
                if 'msg' in json_data:
                    self.logger.warning('url: {}, msg: {}'.format(item['url'], json_data['msg']))
                return

        url, ext = self.v_qq_com.get_video_info(guid, json_data)
        if url is None:
            self.logger.error('url: {}, error: {}'.format(item['url'], ext))
            return
        item['media_urls'] = [url]
        # item['file_urls'] = [url]
        item['file_name'] += ext
        return item
