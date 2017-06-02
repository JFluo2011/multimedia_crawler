import hashlib


def get_md5(txt):
    m = hashlib.md5()
    m.update(txt.encode('utf-8'))
    return m.hexdigest()
