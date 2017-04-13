# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from pymongo import MongoClient
from scrapy.conf import settings

from common import get_md5


class AudioVideoGetPipeline(object):
    def process_item(self, item, spider):
        return item


class ToutiaoPipeline(object):
    def __init__(self):
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
        self.file_name = ''
        self.file_store = ''

    def process_item(self, item, spider):
        try:
            data = {
                'url': item['link'],
                'host': spider.name,
                'info': str(item),
                'downloaded': 0,
                'file': item['file_name'],
                'local_dir': spider.FILES_STORE
            }
        except Exception, err:
            raise DropItem(str(err))
        self.file_name = item['file_name']
        self.file_store = spider.FILES_STORE
        self.col.insert(data)
        return item

    def file_path(self, request, response=None, info=None):

        return '{path}/{file_name}'.format(path=self.file_store, file_name=self.file_name)


class ToutiaoFilePipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for file_url in item['file_urls']:
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = file_paths
        return item
