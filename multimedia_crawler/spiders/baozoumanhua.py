import re

import scrapy
from scrapy.http import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class BaoZouManHua(CrawlSpider):
    name = 'bao_zou_man_hua'
    allowed_domains = ['http://baozoumanhua.com']
    start_urls = ['http://baozoumanhua.com/videos']

    rules = (
        Rule(LinkExtractor(allow=('/video.*?/',)), callback='parse_item'),
    )

    def parse_url(self, response):
        video_urls = re.findall(r'"(/videos/\d+)"', response.text)
        for video_url in video_urls:
            url = 'http://baozoumanhua.com' + video_url
            yield Request(url, callback=self.parse_video_urls)

    def parse_video_urls(self):
        pass

