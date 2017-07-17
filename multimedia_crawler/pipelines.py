# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import copy
import bisect
import logging

import scrapy
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem

from items import MultimediaCrawlerItem
from common.common import setup_mongodb


class MultimediaCrawlerPipeline(object):
    def __init__(self):
        self.col = setup_mongodb()
        self.col.ensure_index('url', unique=True)

    def process_item(self, item, spider):
        try:
            data = {
                'url': item['url'],
                'file_name': item['file_name'],
                'media_type': item['media_type'],
                'host': item['host'],
                'file_dir': item['file_dir'],
                'download': item['download'],
                'extract': item['extract'],
                'info': item['info'],
                'stack': item['stack'],
                'media_urls': item['media_urls'],
            }
            self.col.update({'url': item['url']}, data, upsert=True)
            # self.col.update({'url': item['url']}, {'$set': {'info': item['info']}})
            # self.col.insert(data)
        except Exception, err:
            logging.error(str(err))
            raise DropItem(str(err))
        return item


class IQiYiPipeline(MultimediaCrawlerPipeline):
    items = MultimediaCrawlerItem()
    items['url'] = None

    def insort(self, elem):
        index = bisect.bisect(self.items['info']['index'], elem)
        bisect.insort(self.items['info']['index'], elem)
        return index

    def process_item(self, item, spider):
        if self.items['url'] is None:
            self.items = copy.deepcopy(item)
        elif item['url'] == self.items['url']:
            index = self.insort(item['info']['index'][0])
            self.items['media_urls'].insert(index, item['media_urls'][0])
        else:
            return self.__insert_item(item=item)

    def close_spider(self, spider):
        return self.__insert_item()

    def __insert_item(self, item=None):
        item, self.items = self.items, item
        item.pop('index', None)
        try:
            data = {
                'url': item['url'],
                'file_name': item['file_name'],
                'media_type': item['media_type'],
                'host': item['host'],
                'file_dir': item['file_dir'],
                'download': item['download'],
                'extract': item['extract'],
                'info': item['info'],
                'stack': item['stack'],
                'media_urls': item['media_urls'],
            }
            self.col.update({'url': item['url']}, data, upsert=True)
            # self.col.insert(data)
        except Exception, err:
            logging.error(str(err))
            raise DropItem(str(err))
        return item


class YouKuJiKeFilePipeline(FilesPipeline):
    def __init__(self, *args, **kwargs):
        super(YouKuJiKeFilePipeline, self).__init__(*args, **kwargs)
        self.col = setup_mongodb()
        self.item = MultimediaCrawlerItem()

    @staticmethod
    def _handle_redirect(file_url):
        pass
        # response = requests.head(file_url)
        # if response.status_code == 302:
        #     file_url = response.headers["Location"]
        # return file_url

    def get_media_requests(self, item, info):
        self.item = item
        for file_url in item['file_urls']:
            # redirect_url = self._handle_redirect(file_url)
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'].replace('/', os.sep) for ok, x in results if ok]
        if not file_paths:
            self.col.update({'unique_url': item['unique_url']}, {'$set': {'download': -1}})
            raise DropItem("Item contains no files")
        item['file_paths'] = ''
        item['file_name'] = os.path.split(file_paths[0])[0]
        self.col.update({'unique_url': item['unique_url']},
                        {'$set': {
                            'download': 1,
                            'file_name': item['file_name'],
                        }})
        return item
