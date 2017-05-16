# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import shutil
import logging

import scrapy
import requests
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from pymongo import MongoClient
from scrapy.conf import settings

from items import TouTiaoItem


class AudioVideoGetPipeline(object):
    def process_item(self, item, spider):
        return item


class ToutiaoPipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
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


class YouKuJiKePipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
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


class WeiXinErGengPipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
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
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
        self.item = TouTiaoItem()

    @staticmethod
    def _handle_redirect(file_url):
        response = requests.head(file_url)
        if response.status_code == 302:
            file_url = response.headers["Location"]
        return file_url

    def get_media_requests(self, item, info):
        self.item = item
        for file_url in item['file_urls']:
            redirect_url = self._handle_redirect(file_url)
            yield scrapy.Request(redirect_url)

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


class ErGengPipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
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
