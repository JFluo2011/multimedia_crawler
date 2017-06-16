# -*- coding: utf-8 -*-
import abc


class BasePlayer(object):
    __metaclass__ = abc.ABCMeta
    name = 'base_player'

    def __init__(self, logger, page_url, *args, **kwargs):
        self.json_data = None
        self.media_urls = None
        self.file_name = ''
        self.logger = logger
        self.page_url = page_url
        self.args = args
        self.kwargs = kwargs

    # @abc.abstractmethod
    # def get_params(self):
    #     pass
    #
    # @abc.abstractmethod
    # def get_video_info(self, response):
    #     pass

    @abc.abstractmethod
    def parse_video(self, response):
        pass
