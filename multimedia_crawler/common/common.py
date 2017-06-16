import hashlib


def get_md5(txt):
    m = hashlib.md5()
    m.update(txt.encode('utf-8'))
    return m.hexdigest()


def base_n(num, b, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return (((num == 0) and numerals[0])
            or (base_n(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]))
