# -*- coding: utf-8 -*-
import re
import os
import time
import random
import json
import datetime

import scrapy
from scrapy.conf import settings

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5, base_n


class IQiYiSpider(scrapy.Spider):
    name = "iqiyi"
    download_delay = 5
    users = ['1190686219', '1233288265']
    # users = ['1233288265']
    # allowed_domains = ["youku.com"]
    base_url = 'http://www.iqiyi.com/u/{}/v'

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
            # 'multimedia_crawler.pipelines.IQiYiPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
        # 'SPIDER_MIDDLEWARES': {
        #     # 'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
        #     'multimedia_crawler.middlewares.IQiYiSpiderMiddleware': 500,
        # }
    }

    def start_requests(self):
        for user in self.users:
            params = {
                'page': '1',
                'video_type': '1',
            }
            yield scrapy.FormRequest(self.base_url.format(user), method='GET', formdata=params)

    def parse(self, response):
        selectors = response.xpath(r'//li[@j-delegate="colitem"]')
        for sel in selectors:
            item = MultimediaCrawlerItem()
            item['stack'] = []
            item['download'] = 0
            item['host'] = 'iqiyi'
            item['media_type'] = 'video'
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name)
            item['url'] = sel.xpath('./div[1]/a/@href').extract()[0]
            item['file_name'] = get_md5(item['url'])
            date = sel.xpath('./div[2]/p[2]/span[2]/text()').extract_first(default='').strip()
            if date == '':
                pass
            elif u'昨日上传' in date:
                date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date = date[:-2]
            item['info'] = {'intro': '', 'date': date, 'link': item['url']}
            item['info']['author'] = re.search(r'u/(\d+)/v|$', response.url).group(1) or ''
            item['info']['title'] = sel.xpath('./div[1]/a/img/@title').extract_first(default='')
            yield scrapy.Request(url=item['url'], meta={'item': item}, callback=self.parse_params)
        sel_next_page = response.xpath(u'//a[text()="下一页"]')
        if sel_next_page:
            params = {
                'page': sel_next_page.xpath(r'./@data-pagecheckouter-p').extract()[0],
                'video_type': '1',
            }
            yield scrapy.FormRequest(url=response.url.split('?')[0], method='GET', formdata=params)

    def parse_params(self, response):
        item = response.meta['item']
        tvid = re.search(r'param\[\'tvid\'\]\s+=\s+"(\d+)"|$', response.body).group(1)
        vid = re.search(r'param\[\'vid\'\]\s+=\s+"(.*?)"|$', response.body).group(1)
        if not all([tvid, vid]):
            return

        tm = int(time.time()*1000)
        host = 'http://cache.video.qiyi.com'
        src = ('/vps?tvid=' + tvid + '&vid=' + vid + '&v=0&qypid=' + tvid + '_12&src=01012001010000000000&t=' +
               str(tm) + '&k_tag=1&k_uid=' + self.__get_macid() + '&rs=1')
        vf = self.__get_vf(src)
        url = host + src + '&vf=' + vf
        yield scrapy.Request(url, method='GET', meta={'item': item, 'tvid': tvid}, callback=self.parse_video_urls)

    def parse_video_urls(self, response):
        item = response.meta['item']
        tvid = response.meta['tvid']
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
            lst = json_data['data']['vp']['tkl'][0]['vs'][0]['fs']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return

        meta = {
            'item': item,
            'url_prefix': url_prefix,
            'lst': sorted(lst, key=lambda d: str(re.findall(r'[?|&]qd_index=(\d+)', d['l'])[0])),
        }
        item['file_name'] += '.' + lst[0]['l'].split('?')[0].split('.')[-1]
        base_url = 'http://mixer.video.iqiyi.com/jp/mixin/videos/{}?callback=window.Q.__callbacks__.{}&status=1'
        temp = base_n(int(2147483648 * random.random()), 36)
        url = base_url.format(tvid, temp)
        yield scrapy.Request(url, method='GET', meta=meta, callback=self.parse_play_count)

    def parse_play_count(self, response):
        item = response.meta['item']
        lst = response.meta['lst']
        url_prefix = response.meta['url_prefix']
        try:
            json_data = json.loads(response.body[response.body.find('{'): response.body.rfind('}') + 1])
            item['info']['play_count'] = json_data['data']['playCount']
            item['info']['comments_count'] = json_data['data']['commentCount']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        # for index, l in enumerate(lst):
        #     item['info']['index'] = [index]
        #     item['info']['count'] = len(lst)
        #     url = url_prefix + l['l']
        #     # TODO: add index
        #     yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_download_url)
        # TODO: fix me: 分段视频暂不支持
        if len(lst) == 1:
            url = url_prefix + lst[0]['l']
            yield scrapy.Request(url, method='GET', meta={'item': item}, callback=self.parse_download_url)

    def parse_download_url(self, response):
        item = response.meta['item']
        try:
            json_data = json.loads(response.body)
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(item['url'], str(err)))
            return
        item['media_urls'] = [json_data['l']]
        # return json_data['l']
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
