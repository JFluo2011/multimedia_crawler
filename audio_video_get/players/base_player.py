# -*- coding: utf-8 -*-
import abc


class BasePlayer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, logger, page_url, *args, **kwargs):
        self.logger = logger
        self.page_url = page_url
        self.args = args
        self.kwargs = kwargs

    @abc.abstractmethod
    def get_params(self):
        pass

    @abc.abstractmethod
    def get_video_info(self, response):
        pass
