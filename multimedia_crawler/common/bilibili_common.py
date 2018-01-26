import hashlib


class BiLiBiLiCommon(object):
    app_key = '8e9fc618fbd41e28'
    secret_key = '1c15888dc316e05a15fdd0a02ed6584f'

    def get_params(self, cid):
        params = {
            'player': '1',
            'from': 'miniplay',
            'cid': str(cid),
            # 'quality': '1',
            'quality': '3',
        }
        sign = hashlib.md5(bytes('cid={}&from=miniplay&player=1&quality=3{}'.format(cid, self.secret_key))).hexdigest()
        # sign = hashlib.md5(bytes('cid={}&from=miniplay&player=1&quality=1{}'.format(cid, self.secret_key))).hexdigest()
        params.update({'sign': sign})
        return params
