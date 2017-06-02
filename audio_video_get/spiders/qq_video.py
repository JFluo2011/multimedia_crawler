import os
import json
from urlparse import urljoin

import scrapy
from scrapy.conf import settings

from audio_video_get.items import AudioVideoGetItem
from audio_video_get.common.common import get_md5
from audio_video_get.common.v_qq_com import VQQCom


class QQVideoSpider(scrapy.Spider):
    name = "qq_video"
    download_delay = 10
    # allowed_domains = ['chuansong.me', 'video.qq.com']
    start_urls = ['http://v.qq.com/vplus/jikezhishi/videos']

    custom_settings = {
        'ITEM_PIPELINES': {
            'audio_video_get.pipelines.AudioVideoGetPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'audio_video_get.middlewares.RotateUserAgentMiddleware': 400,
            'audio_video_get.middlewares.AudioVideoGetDupFilterMiddleware': 1,
        },
    }

    def __init__(self, name=None, **kwargs):
        super(QQVideoSpider, self).__init__(name, **kwargs)
        self.v_qq_com = VQQCom()

    def parse(self, response):
        sel_list = response.xpath('//ul[@id="videolst_cont"]')
        for sel in sel_list:
            item = AudioVideoGetItem()
            item['host'] = 'weixin_ergeng'
            item['stack'] = []
            item['download'] = 0
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], self.name)
            url = sel.xpath('.//li/a/@href').extract()[0]
            item['url'] = urljoin('https://v.qq.com/x/page/', url.split('/')[-1])
            item['info'] = {}
            item['info']['title'] = sel.xpath('.//li/a/@title').extract()[0].strip()
            item['info']['link'] = item['url']
            item['info']['date'] = sel.xpath('.//div/span[2]/text()').extract()[0].strip()
            item['info']['author'] = response.url.split('/')[-2]
            item['file_name'] = get_md5(item['url'])
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_info)

    def parse_info(self, response):
        item = response.meta['item']
        url = 'https://vv.video.qq.com/getinfo'
        guid, params = self.v_qq_com.get_info(response.url.split('/')[-1].split('.')[0])
        meta = {
            'guid': guid,
            'item': item,
        }
        yield scrapy.FormRequest(url, method='GET', meta=meta, formdata=params, callback=self.parse_video_url)

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
        item['file_name'] += ext
        return item
