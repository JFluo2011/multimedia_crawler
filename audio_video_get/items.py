# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AudioVideoGetItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    media_type = scrapy.Field()
    url = scrapy.Field()
    media_urls = scrapy.Field()
    host = scrapy.Field()
    file_dir = scrapy.Field()
    download = scrapy.Field()
    info = scrapy.Field()
    stack = scrapy.Field()
    file_name = scrapy.Field()



