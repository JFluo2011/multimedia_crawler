# -*- coding: utf-8 -*-
import os
import time
import json
import copy
import logging
from threading import RLock

import redis
import scrapy
from scrapy.conf import settings
from scrapy_redis.spiders import RedisSpider

from multimedia_crawler.common.common import get_md5, WebUser
from multimedia_crawler.items import MultimediaCrawlerItem
from multimedia_crawler.common.weitao_comm import WeiTao


# class WeiTaoSpider(scrapy.Spider):
class WeiTaoSpider(RedisSpider):
    name = "weitao"
    redis_key = 'weitao'
    lock = RLock()
    download_delay = 5
    weitao = WeiTao()
    redis_con = redis.StrictRedis(**settings['USER_REDIS'])
    app_key = '12574478'
    token = '6607538343cdf287b11911ccfde96792'
    cookies = {
        't': '7f888015a732354899758c7b7f3b3663',
        '_m_h5_tk': '6607538343cdf287b11911ccfde96792_1513823230119',
        '_m_h5_tk_enc': '82287e40d085270426293409ed4f949f',
    }
    handle_httpstatus_list = [403, 404, 408, 564, 503, 501]
    users = [
        # WebUser(id='23302707', name='坤哥玩花卉', storage_name='kungewanhuahui'),
        # WebUser(id='1994256139', name='HaoHuo好活', storage_name='haohuohaohuo'),
        # WebUser(id='99859201', name='大叔爱家居', storage_name='dashuaijiaju'),
        WebUser(id='279628378', name='格调汇', storage_name='gediaohui'),
        # WebUser(id='256345687', name='理想家先生', storage_name='lixiangjiaxiansheng'),
        # WebUser(id='21858018', name='年轮故事', storage_name='nianlungushi'),
        # WebUser(id='713735197', name='爱家FASHION', storage_name='aijiafashion'),
        # WebUser(id='1850683564', name='大懒的简单生活', storage_name='dalaidejiandanshenghuo'),
        # WebUser(id='1667286669', name='极品联盟', storage_name='jipinglianmeng'),
        # WebUser(id='73747545', name='妙汇APP', storage_name='miaohuiapp'),
        # WebUser(id='3314527906', name='拾物玩意', storage_name='shiwuwanyi'),
        # WebUser(id='748202617', name='理想家的家', storage_name='lixiangjiadejia'),
    ]

    custom_settings = {
        'ITEM_PIPELINES': {
            'multimedia_crawler.pipelines.MultimediaCrawlerPipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'multimedia_crawler.middlewares.RotateUserAgentMiddleware': 400,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
            'multimedia_crawler.middlewares.WeiTaoDupFilterMiddleware': 1,
        },
    }

    def parse(self, response):
        task = response.meta['task']
        user = response.meta['user']
        cookies = response.meta['cookies']
        if response.status in self.handle_httpstatus_list:
            logging.error('{}: {}'.format(response.url, response.status))
            self.redis_con.sadd(self.redis_key, task)
            return
        json_data = json.loads(response.text[response.text.find('(') + 1:response.text.rfind(')')])
        if u'服务调用成功' not in json_data['ret'][0]:
            # import pdb
            # pdb.set_trace()
            logging.error('task: {} failed, error: {}'.format(task, json_data['ret'][0].encode('utf-8')))
            # logging.error('task: {} failed, error: {}'.format(task, json_data['data']['result']))
            self.redis_con.sadd(self.redis_key, task)
            with self.lock:
                if self.cookies == cookies:
                    self.update_cookies(response)
            # if ('RGV587_ERROR::SM' in json_data['ret'][0]) or (u'令牌过期' in json_data['ret'][0]):
            #     with self.lock:
            #         if self.cookies == cookies:
            #             self.update_cookies(response)
        else:
            for data in json_data['data']['result']['feeds']:
                if 'videoId' not in data.keys():
                    continue
                item = MultimediaCrawlerItem()
                item['stack'] = []
                item['download'] = 0
                item['extract'] = 0
                item['host'] = 'weitao'
                item['media_type'] = 'video'
                item['file_dir'] = os.path.join(settings['FILES_STORE'], item['media_type'],
                                                self.name, user['storage_name'])
                item['url'] = 'http://market.m.taobao.com/apps/market/content/index.html?contentId={}'.format(
                    data['feedId'])

                item['file_name'] = get_md5(item['url']) + '.' + data['videoUrl'].split('.')[-1]
                item['media_urls'] = ['http://' + data['videoUrl']]
                item['info'] = {
                    'title': data.get('title', ''),
                    'link': item['url'],
                    'intro': data.get('content', ''),
                    'author': user['user_name'],
                    'play_count': data.get('viewCount', 0),
                    'comments_count': data.get('commentCount', 0),
                    'date': time.strftime('%Y-%m-%d', time.localtime(int(data['publishTime'][:-3])))
                }
                yield item

    def get_args(self, user, page, token):
        data = {
            "accountId": str(user['user_id']),
            "force": "2",
            "currentPage": str(page)
        }
        t = str(int(time.time() * 1000))
        sign = self.weitao.get_sign('&'.join([token, t, self.app_key, json.dumps(data)]))
        url = 'https://h5api.m.taobao.com/h5/mtop.taobao.daren.accountpage.feeds/1.0/'
        params = {
            'jsv': '2.4.3',
            'appKey': self.app_key,
            't': t,
            'sign': sign,
            'api': 'mtop.taobao.daren.accountpage.feeds',
            'v': '1.0',
            'type': 'jsonp',
            'AntiCreep': 'true',
            'dataType': 'jsonp',
            'callback': 'mtopjsonp{}'.format(page + 1),
            'data': json.dumps(data),
        }
        return url, params

    def get_cookies(self):
        try:
            cookies = json.loads(self.redis_con.lindex('weitao_cookies', 0))
        except Exception as err:
            logging.error('get cookies failed: '.format(str(err)))
            return None, None
        token = cookies.pop('token')
        return cookies, token

    def update_cookies(self, response):
        cookie_lst = response.headers.getlist('Set-Cookie')
        for cookie in cookie_lst:
            if '_m_h5_tk_enc' in cookie:
                self.cookies.update({'_m_h5_tk_enc': cookie.split(';')[0].split('=')[-1]})
            elif '_m_h5_tk' in cookie:
                self.cookies.update({'_m_h5_tk': cookie.split(';')[0].split('=')[-1]})
                self.token = cookie.split(';')[0].split('=')[-1].split('_')[0]
            elif 't=' in cookie:
                self.cookies.update({'t': cookie.split(';')[0].split('=')[-1]})

        logging.info('update cookies done')
        # return cookies, token
