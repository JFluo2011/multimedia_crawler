# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import logging

import scrapy
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from pymongo import MongoClient
from scrapy.conf import settings

from common import get_md5
from items import TouTiaoItem


class AudioVideoGetPipeline(object):
    def process_item(self, item, spider):
        return item


class ToutiaoPipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])

    def process_item(self, item, spider):
        try:
            data = {
                'url': item['link'],
                'host': spider.name,
                'downloaded': 1,
                'file_name': item['file_name'],
                'unique_url': item['unique_url'],
                'local_dir': os.path.join(os.path.abspath(settings['FILES_STORE']), spider.name, item['file_name']),
            }
        except Exception, err:
            logging.error(str(err))
            raise DropItem(str(err))
        self.col.insert(data)
        return item


class ToutiaoFilePipeline(FilesPipeline):
    count = 0
    file_names = []

    def __init__(self, *args, **kwargs):
        super(ToutiaoFilePipeline, self).__init__(*args, **kwargs)
        # self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        # self.db = self.client.get_database(settings['MONGODB_DB'])
        # self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
        self.item = TouTiaoItem()

    def get_media_requests(self, item, info):
        self.item = item
        for file_url in item['file_urls']:
            self.count += 1
            logging.error(file_url + ' ' + str(self.count))
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = file_paths
        self.file_names.append(item['file_name'])
        logging.error(self.file_names)
        # self.col.update({'file_name': item['file_name']}, {'$set': {'downloaded': 1}})
        return item

    def file_path(self, request, response=None, info=None):
        # file_name = request.url.split('/')[-1]
        file_name = os.path.join(self.item['author_id'], self.item['file_name'])
        path = info.spider.name
        return '{path}/{file_name}'.format(path=path, file_name=file_name)
