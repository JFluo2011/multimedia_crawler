import hashlib
from collections import namedtuple

from pymongo import MongoClient
from scrapy.conf import settings


WebUser = namedtuple('WebUser', ['id', 'name', 'storage_name'])


def get_md5(txt):
    m = hashlib.md5()
    m.update(txt.encode('utf-8'))
    return m.hexdigest()


def base_n(num, b, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return (((num == 0) and numerals[0])
            or (base_n(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]))


def setup_mongodb():
    client = MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
    db = client.get_database(settings['MONGODB_DB'])
    if 'MONGODB_USER' in settings.keys():
        db.authenticate(settings['MONGODB_USER'], settings['MONGODB_PASSWORD'])
    return db.get_collection(settings['MONGODB_COLLECTION'])


class MyRFPDupeFilter(object):
    def __init__(self, server, key, debug=False):
        pass

    @classmethod
    def from_settings(cls, settings):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        pass

    def request_seen(self, request):
        pass

    def request_fingerprint(self, request):
        pass

    def close(self, reason=''):
        pass

    def clear(self):
        pass

    def log(self, request, spider):
        pass
