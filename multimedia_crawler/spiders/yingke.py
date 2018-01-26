# coding: utf-8

import re
import os
import time
import copy
import json

import scrapy
import redis
from scrapy.conf import settings
from scrapy_redis.spiders import RedisSpider

from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.common import get_md5


class YingKeSpider(RedisSpider):
    name = 'yingke'
    redis_key = 'yingke'
    download_delay = 5
    redis_con = redis.StrictRedis(**settings['USER_REDIS'])

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'multimedia_crawler.middlewares.MultimediaCrawlerDupFilterMiddleware': 1,
        },
    }

    def parse(self, response):
        base_url = 'https://mlive.inke.cn/share_stv/live.html?feedid={}&uid={}'
        item = MultimediaCrawlerItem()
        json_data = json.loads(response.body)
        if 'owner_info' not in json_data.keys():
            print(response.url)
        else:
            uid = str(json_data['owner_info']['id'])
            item['host'] = 'yingke'
            item['media_type'] = 'video'
            item['stack'] = []
            item['download'] = 0
            item['extract'] = 0
            item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'], self.name, uid)
            item['info'] = {
                'author': json_data['owner_info']['nick'],
                'author_id': uid,
            }
            timestamp = json_data['timestamp']
            if json_data['has_more']:
                url = ('https://service.inke.cn/api/feed/feeds?sid=20lV0Wi7cR0ddr0Gc5omEZ1rJ1o6rC2ZkZ9eWOSi256BVq7QYXX'
                       '&uid=626088547&ast=1&start_time={}&is_all=1&limit=10&owner_uid={}')
                self.redis_con.sadd(self.redis_key, url.format(timestamp, uid))
            for video in json_data['feeds']:
                item['url'] = base_url.format(video['feedId'], video['uid'])
                item['info']['title'] = video['title']
                item['info']['play_count'] = video['viewCount']
                item['info']['like_count'] = video['likeCount']
                item['info']['date'] = time.strftime('%Y-%m-%d', time.localtime(float(video['ctime'][:-3])))
                item['media_urls'] = [json.loads(video['content'])['mp4_url']]
                item['file_name'] = get_md5(item['url']) + '.mp4'
                item['info']['link'] = item['url']
                yield item
