# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AudioVideoGetItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class TouTiaoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    video_url = scrapy.Field()
    name = scrapy.Field()
    intro = scrapy.Field()
    album = scrapy.Field()
    author = scrapy.Field()
    author_id = scrapy.Field()
    file_urls = scrapy.Field()
    files = scrapy.Field()
    file_name = scrapy.Field()
    file_paths = scrapy.Field()
    unique_url = scrapy.Field()

