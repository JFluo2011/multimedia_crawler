# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import shutil
import logging

import scrapy
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

    def open_spider(self, spider):
        self.col.remove({'download': -1})
        self.col.remove({'download': 'downloading'})

    def process_item(self, item, spider):
        try:
            data = {
                'video_url': item['video_url'],
                'spider': spider.name,
                'download': 0,
                'file_name': '',
                'unique_url': item['unique_url'],
                'file_paths': '',
            }
        except Exception, err:
            logging.error(str(err))
            raise DropItem(str(err))
        self.col.insert(data)
        return item

    def close_spider(self, spider):
        # for r in self.col.find({'download': 'downloading'}):
        #     if os.path.exists(r['file_paths']):
        #         os.remove(r['file_paths'])
        self.col.remove({'download': 'downloading'})


class ToutiaoFilePipeline(FilesPipeline):
    # path_list = []
    count = 0

    def __init__(self, *args, **kwargs):
        super(ToutiaoFilePipeline, self).__init__(*args, **kwargs)
        self.client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = self.client.get_database(settings['MONGODB_DB'])
        self.col = self.db.get_collection(settings['MONGODB_COLLECTION'])
        self.item = TouTiaoItem()

    def get_media_requests(self, item, info):
        self.item = item
        for file_url in item['file_urls']:
            # self.col.update_one({'video_url': file_url}, {'$set': {'download': 'downloading'}})
            self.col.update({'unique_url': item['unique_url']}, {'$set': {'download': 'downloading'}})
            yield scrapy.Request(file_url)

    def __move_file(self, file_path):
        base_path = os.path.join('Video', 'toutiao')
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        # os.sep
        src_path = os.path.join(os.path.abspath(settings['FILES_STORE']), file_path)
        dre_path = os.path.join(os.path.abspath(settings['FILES_STORE']),
                                base_path, self.item['author_id'], file_path.split(os.sep, 1)[1])
        if not os.path.exists(os.path.split(dre_path)[0]):
            os.makedirs(os.path.split(dre_path)[0])
        print src_path, dre_path
        shutil.move(src_path, dre_path)
        return dre_path

    def item_completed(self, results, item, info):
        self.count += 1
        file_paths = [x['path'].replace('/', os.sep) for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = self.__move_file(file_paths[0])
        item['file_name'] = os.path.split(file_paths[0])[0]
        self.col.update({'unique_url': item['unique_url']},
                        {'$set': {
                            'download': 1,
                            'file_name': item['file_name'],
                            'file_paths': item['file_paths']
                        }})
        logging.error(self.count)
        return item

    # def file_path(self, request, response=None, info=None):
    #     # file_name = request.url.split('/')[-1]
    #     file_name = os.path.join(self.item['author_id'], self.item['file_name'])
    #     path = info.spider.name
    #     # self.path_list.append(os.path.join(path, file_name))
    #     logging.error(os.path.join(path, file_name))
    #     return os.path.join(path, file_name)
    #     # return '{path}/{file_name}'.format(path=path, file_name=file_name)

    # def media_failed(self, failure, request, info):
    #     super(ToutiaoFilePipeline, self).media_failed(failure, request, info)
    #     self.col.update({'file_name': self.item['file_name']}, {'$set': {'download': -1}})

    # def media_to_download(self, request, info):
    #     super(ToutiaoFilePipeline, self).media_to_download(request, info)
    #     self.col.update_one({'url': request.url}, {'$set': {'download': 'downloading'}})
