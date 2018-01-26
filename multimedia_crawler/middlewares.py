# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import re
import copy
import random
import logging
import urllib
import json

import scrapy
import requests
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.conf import settings
from fake_useragent import UserAgent

from common.common import setup_mongodb


class RotateUserAgentMiddleware(UserAgentMiddleware):
    ua_obj = UserAgent()
    regex = re.compile(r"android|iphone|ipad|mobile")

    def __init__(self, user_agent=''):
        super(RotateUserAgentMiddleware, self).__init__()

    def process_request(self, request, spider):
        # ua = random.choice(settings['USER_AGENTS'])
        user_agent = self.ua_obj.random
        if (not user_agent) or (self.regex.search(user_agent.lower())):
            user_agent = random.choice(settings['USER_AGENTS'])
        request.headers.setdefault('User-Agent', user_agent)


class MultimediaCrawlerDupFilterMiddleware(object):
    def __init__(self):
        self.col = setup_mongodb()

    def process_request(self, request, spider):
        if self.col.find_one({'$and': [
            {'host': spider.name},
            {'url': request.url},
            # {'download': {'$in': [0, 1, 2]}}
            {'download': {'$ne': -1}},
        ]}):
            logging.warning('the page is crawled, url is {0}'.format(request.url))
            raise IgnoreRequest()


class WeiTaoDupFilterMiddleware(object):
    def process_request(self, request, spider):
        if 'storage_name' in request.url:
            json_data = json.loads(urllib.unquote(request.url))
            user = json_data['user']
            page = json_data['page']
            # cookies, token = spider.get_cookies()
            url, params = spider.get_args(user, int(page), spider.token)
            meta = {
                'user': user,
                'page': page,
                'task': urllib.unquote(request.url),
                'cookies': spider.cookies,
            }
            if 'Referer' in request.headers:
                request.headers.pop('Referer')
            # referer = 'https://daren.taobao.com/account_page/daren_home.htm?user_id={}'.format(user['user_id'])
            return scrapy.FormRequest(url, method='GET', formdata=params,
                                      meta=meta, cookies=spider.cookies, callback=spider.parse)


class XinPianChangDupFilterMiddleware(MultimediaCrawlerDupFilterMiddleware):
    def process_request(self, request, spider):
        url = request.url.split('?')[0]
        if self.col.find_one({'$and': [
            {'host': spider.name},
            {'url': url},
            # {'download': {'$in': [0, 1, 2]}}
            {'download': {'$ne': -1}},
        ]}):
            logging.warning('the page is crawled, url is {0}'.format(request.url))
            raise IgnoreRequest()

        return None


class YouKuJiKeDupFilterMiddleware(MultimediaCrawlerDupFilterMiddleware):
    def process_request(self, request, spider):
        if 'http://v.youku.com/v_show/' in request.url:
            url = request.url.split('?')[0]
        else:
            url = request.url
        if self.col.find_one({'$and': [
            {'host': spider.name},
            {'url': url},
            # {'download': {'$in': [0, 1, 2]}}
            {'download': {'$ne': -1}},
        ]}):
            logging.warning('the page is crawled, url is {0}'.format(url))
            raise IgnoreRequest()

        return None


class YouKuDupFilterMiddleware(MultimediaCrawlerDupFilterMiddleware):
    def process_request(self, request, spider):
        if 'http://v.youku.com/v_show/' in request.url:
            url = request.url.split('?')[0]
        else:
            url = request.url
        if self.col.find_one({'$and': [
            {'host': spider.name},
            {'url': url},
            # {'download': {'$in': [0, 1, 2]}}
            {'download': {'$ne': -1}},
        ]}):
            logging.warning('the page is crawled, url is {0}'.format(url))
            raise IgnoreRequest()

        return None


class MultimediaCrawlerMiddleware(object):
    items = {}

    def process_spider_output(self, response, result, spider):
        for i in result:
            if isinstance(i, scrapy.Item) and (i['info'].get('player', '') == 'iqiyi'):
                key = i['url']
                if key not in self.items.keys():
                    self.items[key] = copy.deepcopy(i)
                else:
                    self.items[key]['media_urls'].append(i['media_urls'][0])
                if i['info']['count'] == len(self.items[key]['media_urls']):
                    yield self.__sort_item(key)
            else:
                yield i

    def __sort_item(self, key):
        item = self.items.pop(key)
        item['media_urls'].sort(key=lambda url: int(re.findall(r'qd_index=(\d+)&', url)[0]))
        item['info'].pop('index', None)
        item['info'].pop('count', None)
        item['info'].pop('player', None)
        return item


# class MultimediaCrawlerMiddleware(object):
#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#
#     def process_spider_input(self, response, spider):
#         # Called for each response that goes through the spider
#         # middleware and into the spider.
#
#         # Should return None or raise an exception.
#         return None
#
#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.
#         # Must return an iterable of Request, dict or Item objects.
#         for i in result:
#             yield i
#
#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.
#
#         # Should return either None or an iterable of Response, dict
#         # or Item objects.
#         pass
#
#     def process_start_requests(self, start_requests, spider):
#         # Called with the start requests of the spider, and works
#         # similarly to the process_spider_output() method, except
#         # that it doesn’t have a response associated.
#
#         # Must return only requests (not items).
#         for r in start_requests:
#             yield r
#
#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)


class QingTingFMAppUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent=''):
        super(QingTingFMAppUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) QingTingFM-Android'
        request.headers.setdefault('User-Agent', ua)


class MobileUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent=''):
        super(MobileUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = ('Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Mobile Safari/537.36')
        request.headers.setdefault('User-Agent', ua)


class WeiXinErGengUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent=''):
        super(WeiXinErGengUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent

    def process_request(self, request, spider):
        if request.url.startswith('http://chuansong.me') or request.url.startswith('https://v.qq.com/x/page/'):
            ua = random.choice(settings['USER_AGENTS'])
        else:
            ua = ('Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Mobile Safari/537.36')
        request.headers.setdefault('User-Agent', ua)


class SinaWeiBoRotateUserAgentMiddleware(UserAgentMiddleware):
    def __init__(self, user_agent=''):
        super(SinaWeiBoRotateUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent

    def process_request(self, request, spider):
        ua = random.choice(settings['SPIDER_USER_AGENTS'])
        if ua:
            # print ua
            request.headers.setdefault('User-Agent', ua)

    # the default user_agent_list composes chrome,I E,firefox,Mozilla,opera,netscape
    # for more user agent strings,you can find it in http://www.useragentstring.com/pages/useragentstring.php
