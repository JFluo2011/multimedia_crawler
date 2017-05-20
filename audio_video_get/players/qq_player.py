# -*- coding: utf-8 -*-
import os
import time
import math
import json
import random
from ctypes import c_int, c_uint
from urlparse import urljoin

from base_player import BasePlayer
from audio_video_get.common import get_md5


class QQPlayer(BasePlayer):
    seed = "#$#@#*ad"

    def get_params(self):
        method = 'GET'
        url = 'http://h5vv.video.qq.com/getinfo'
        params = self.__get_params()
        return url, method, params

    def get_video_info(self, response):
        guid = response.meta['guid']
        code = -1
        try:
            json_data = json.loads(response.body[response.body.find('(') + 1: -1])
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return code, None, None
        else:
            code = json_data['exem']
            if code != 0:
                self.logger.warning('url: {}, exem: {}'.format(self.page_url, json_data['exem']))
                if 'msg' in json_data:
                    self.logger.warning('url: {}, msg: {}'.format(self.page_url, json_data['msg']))
                return code, None, None
        return code, self._get_video_info(guid, json_data)

    def __get_params(self):
        vid = self.kwargs['vid']
        g = '11001'  # from platform in d
        h = vid  # from vids in d
        i = 'v5010'
        k = 1
        f = str(int(time.time()))
        qv_rmt, qv_rmt2 = self._func_xx(g, h, i, k, f)
        guid = ''.join([str(hex(int(16 * random.random()))[2:]) for _ in range(32)])
        params = {
            'platform': '11001',
            'charge': '0',
            'otype': 'json',
            'ehost': 'http://v.qq.com',
            'sphls': '1',
            'sb': '1',
            'nocache': '0',
            '_rnd': str(int(time.time())),

            'guid': guid,
            'appVer': 'V2.0Build9370',
            'vids': vid,
            'defaultfmt': 'auto',
            '_qv_rmt': qv_rmt,
            '_qv_rmt2': qv_rmt2,
            'sdtfrom': 'v5010',
            'callback': 'tvp_request_getinfo_callback_' + str(int(1e6 * random.random())),
        }
        return params

    def _get_video_info(self, guid, json_data):
        try:
            url = urljoin(json_data['vl']['vi'][0]['ul']['ui'][0]['url'], json_data['vl']['vi'][0]['fn'])
            params = {
                'vkey': json_data['vl']['vi'][0]['fvkey'],
                'br': json_data['vl']['vi'][0]['br'],
                'platform': '2',
                'level': json_data['vl']['vi'][0]['level'],
                'sdtfrom': 'v5010',
                'guid': guid,
                # 'fmt': json_data['vl']['vi'][0]['pl'][0]['pd'][0]['fmt'],
                'fmt': 'auto',
            }
            file_name = json_data['vl']['vi'][0]['fn']
        except Exception as err:
            self.logger.error('url: {}, error: {}'.format(self.page_url, str(err)))
            return None, None
        else:
            if url is None:
                return None, None

        url += '?' + '&'.join(['='.join([k, str(v)]) for k, v in params.items()])
        media_urls = [url] if (url is not None) else None
        file_name = get_md5(self.page_url) + os.path.splitext(file_name)[1]
        return media_urls, file_name

    @staticmethod
    def _func_b(a, b):
        return c_int(((a >> 1) + (b >> 1) << 1) + (1 & a) + (1 & b)).value

    def _func_ha(self, d):
        c = [0 | c_int(int(4294967296 * abs(math.sin(index + 1)))).value for index in range(64)]
        # j = unescape(encodeURI(d))
        j = d
        k = len(j)
        i = [0 for _ in range(k)]
        for m in range(k):
            i[m >> 2] |= (ord(j[m]) or 128) << 8 * (m % 4)
        i[k >> 2] = c_int(i[k >> 2] | c_int(128 << (8 * (k % 4))).value).value
        e = 1732584193
        f = -271733879
        l = [1732584193, -271733879, ~e, ~f]
        a = 16
        d = (k + 8 >> 6) * a + 14
        i[d] = 8 * k
        m = 0
        while d > m:
            h, k = 0, l
            while h < 64:
                e, f, g, t = k[1], k[2], k[3], k[3]
                x = self._func_b(k[0], c_int([e & f | ~e & g, g & e | ~g & f, e ^ f ^ g, f ^ (e | ~g)][h >> 4]).value)
                k = h >> 4
                y = self._func_b(c[h], i[[h, 5 * h + 1, 3 * h + 5, 7 * h][k] % a + m])
                g = self._func_b(x, y)
                k = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, a, 23, 6, 10, 15, 21][4 * k + h % 4]
                k = [t, self._func_b(e, c_int(g << k | (c_uint(g).value >> 32 - k)).value), e, f]
                h += 1
            for index in range(3, -1, -1):
                l[index] = self._func_b(l[index], k[index])
            m += a

        d = ''
        for h in range(32):
            if a == 16:
                d += str(hex(l[h >> 3] >> 4 * (1 ^ 7 & h) & 15)[2:])
            else:
                raise NotImplementedError
        # d = 'bd81608610f369f8c6423d95ba319041'
        return d

    @staticmethod
    def _func_hex_to_string(a):
        a = a[2:] if '0x' == a[:2] else a
        return ''.join([unichr(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    @staticmethod
    def _func_url_enc(a, b, c):
        m, l = 0, ''
        url_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        while m < len(a):
            d = ord(a[m])
            f = ord(a[m + 1]) if (m + 1 < len(a)) else 0
            g = ord(a[m + 2]) if (m + 2 < len(a)) else 0
            m += 3
            if 15 == m:
                l += 'A' + b + c
            h = d >> 2
            i = (3 & d) << 4 | f >> 4
            j = (15 & f) << 2 | g >> 6
            k = 63 & g
            if f == -1:
                j = k = 64
            elif g == -1:
                k = 64
            l += url_str[h] + url_str[i] + url_str[j] + url_str[k]

        return l

    @staticmethod
    def _func_temp_calc(a, b):
        return ''.join([chr(ord(a[i]) ^ ord(b[i % 4])) for i in range(len(a))])

    @staticmethod
    def _func_u1(a, b):
        return ''.join([a[i] for i in range(b, len(a), 2)])

    def _func_xx(self, a, b, c, d, f):
        g = h = ''
        f = f if f is not None else str(int(time.time()))

        j = self._func_hex_to_string(self._func_ha(''.join([a, b, f, self.seed, g, h, str(d), c])))
        k = self._func_url_enc(self._func_temp_calc(j, self.seed), str(d), f)
        l = self._func_url_enc(self._func_temp_calc(j, "86FG@hdf"), str(d), f)
        m = self._func_u1(k, 0)
        n = self._func_u1(k, 1)
        return m, n
