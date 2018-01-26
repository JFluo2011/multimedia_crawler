from ctypes import c_int, c_uint


class WeiTao(object):
    # o, p, q, r, s, t, u, v, w,
    x = []
    y = 7
    z = 12
    A = 17
    B = 22
    C = 5
    D = 9
    E = 14
    F = 20
    G = 4
    H = 11
    I = 16
    J = 23
    K = 6
    L = 10
    M = 15
    N = 21

    def get_sign(self, a):
        a = self.func_n(a)
        x = self.func_l(a)
        t = 1732584193
        u = 4023233417
        v = 2562383102
        w = 271733878
        o = 0
        while o < len(x):
            p = t
            q = u
            r = v
            s = w
            t = self.func_h(t, u, v, w, x[o + 0], self.y, 3614090360)
            w = self.func_h(w, t, u, v, x[o + 1], self.z, 3905402710)
            v = self.func_h(v, w, t, u, x[o + 2], self.A, 606105819)
            u = self.func_h(u, v, w, t, x[o + 3], self.B, 3250441966)
            t = self.func_h(t, u, v, w, x[o + 4], self.y, 4118548399)
            w = self.func_h(w, t, u, v, x[o + 5], self.z, 1200080426)
            v = self.func_h(v, w, t, u, x[o + 6], self.A, 2821735955)
            u = self.func_h(u, v, w, t, x[o + 7], self.B, 4249261313)
            t = self.func_h(t, u, v, w, x[o + 8], self.y, 1770035416)
            w = self.func_h(w, t, u, v, x[o + 9], self.z, 2336552879)
            v = self.func_h(v, w, t, u, x[o + 10], self.A, 4294925233)
            u = self.func_h(u, v, w, t, x[o + 11], self.B, 2304563134)
            t = self.func_h(t, u, v, w, x[o + 12], self.y, 1804603682)
            w = self.func_h(w, t, u, v, x[o + 13], self.z, 4254626195)
            v = self.func_h(v, w, t, u, x[o + 14], self.A, 2792965006)
            u = self.func_h(u, v, w, t, x[o + 15], self.B, 1236535329)
            t = self.func_i(t, u, v, w, x[o + 1], self.C, 4129170786)
            w = self.func_i(w, t, u, v, x[o + 6], self.D, 3225465664)
            v = self.func_i(v, w, t, u, x[o + 11], self.E, 643717713)
            u = self.func_i(u, v, w, t, x[o + 0], self.F, 3921069994)
            t = self.func_i(t, u, v, w, x[o + 5], self.C, 3593408605)
            w = self.func_i(w, t, u, v, x[o + 10], self.D, 38016083)
            v = self.func_i(v, w, t, u, x[o + 15], self.E, 3634488961)
            u = self.func_i(u, v, w, t, x[o + 4], self.F, 3889429448)
            t = self.func_i(t, u, v, w, x[o + 9], self.C, 568446438)
            w = self.func_i(w, t, u, v, x[o + 14], self.D, 3275163606)
            v = self.func_i(v, w, t, u, x[o + 3], self.E, 4107603335)
            u = self.func_i(u, v, w, t, x[o + 8], self.F, 1163531501)
            t = self.func_i(t, u, v, w, x[o + 13], self.C, 2850285829)
            w = self.func_i(w, t, u, v, x[o + 2], self.D, 4243563512)
            v = self.func_i(v, w, t, u, x[o + 7], self.E, 1735328473)
            u = self.func_i(u, v, w, t, x[o + 12], self.F, 2368359562)
            t = self.func_j(t, u, v, w, x[o + 5], self.G, 4294588738)
            w = self.func_j(w, t, u, v, x[o + 8], self.H, 2272392833)
            v = self.func_j(v, w, t, u, x[o + 11], self.I, 1839030562)
            u = self.func_j(u, v, w, t, x[o + 14], self.J, 4259657740)
            t = self.func_j(t, u, v, w, x[o + 1], self.G, 2763975236)
            w = self.func_j(w, t, u, v, x[o + 4], self.H, 1272893353)
            v = self.func_j(v, w, t, u, x[o + 7], self.I, 4139469664)
            u = self.func_j(u, v, w, t, x[o + 10], self.J, 3200236656)
            t = self.func_j(t, u, v, w, x[o + 13], self.G, 681279174)
            w = self.func_j(w, t, u, v, x[o + 0], self.H, 3936430074)
            v = self.func_j(v, w, t, u, x[o + 3], self.I, 3572445317)
            u = self.func_j(u, v, w, t, x[o + 6], self.J, 76029189)
            t = self.func_j(t, u, v, w, x[o + 9], self.G, 3654602809)
            w = self.func_j(w, t, u, v, x[o + 12], self.H, 3873151461)
            v = self.func_j(v, w, t, u, x[o + 15], self.I, 530742520)
            u = self.func_j(u, v, w, t, x[o + 2], self.J, 3299628645)
            t = self.func_k(t, u, v, w, x[o + 0], self.K, 4096336452)
            w = self.func_k(w, t, u, v, x[o + 7], self.L, 1126891415)
            v = self.func_k(v, w, t, u, x[o + 14], self.M, 2878612391)
            u = self.func_k(u, v, w, t, x[o + 5], self.N, 4237533241)
            t = self.func_k(t, u, v, w, x[o + 12], self.K, 1700485571)
            w = self.func_k(w, t, u, v, x[o + 3], self.L, 2399980690)
            v = self.func_k(v, w, t, u, x[o + 10], self.M, 4293915773)
            u = self.func_k(u, v, w, t, x[o + 1], self.N, 2240044497)
            t = self.func_k(t, u, v, w, x[o + 8], self.K, 1873313359)
            w = self.func_k(w, t, u, v, x[o + 15], self.L, 4264355552)
            v = self.func_k(v, w, t, u, x[o + 6], self.M, 2734768916)
            u = self.func_k(u, v, w, t, x[o + 13], self.N, 1309151649)
            t = self.func_k(t, u, v, w, x[o + 4], self.K, 4149444226)
            w = self.func_k(w, t, u, v, x[o + 11], self.L, 3174756917)
            v = self.func_k(v, w, t, u, x[o + 2], self.M, 718787259)
            u = self.func_k(u, v, w, t, x[o + 9], self.N, 3951481745)
            t = self.func_c(t, p)
            u = self.func_c(u, q)
            v = self.func_c(v, r)
            w = self.func_c(w, s)
            o += 16
        O = self.func_m(t) + self.func_m(u) + self.func_m(v) + self.func_m(w)
        return O.lower()

    def func_b(self, a, b):
        return a << b | c_uint(a).value >> 32 - b

    def func_c(self, a, b):
        e = 2147483648 & a
        f = 2147483648 & b
        c = 1073741824 & a
        d = 1073741824 & b
        g = (1073741823 & a) + (1073741823 & b)
        if c & d:
            r = c_int(2147483648 ^ g ^ e ^ f).value
        elif c | d:
            if 1073741824 & g:
                r = c_int(3221225472 ^ g ^ e ^ f).value
            else:
                r = c_int(1073741824 ^ g ^ e ^ f).value
        else:
            r = c_int(g ^ e ^ f).value
        return r

    def func_d(self, a, b, c):
        return a & b | ~a & c

    def func_e(self, a, b, c):
        return a & c | b & ~c

    def func_f(self, a, b, c):
        return a ^ b ^ c

    def func_g(self, a, b, c):
        return b ^ (a | ~c)

    def func_h(self, a, e, f, g, h, i, j):
        a = self.func_c(a, self.func_c(self.func_c(self.func_d(e, f, g), h), j))
        return self.func_c(self.func_b(a, i), e)

    def func_i(self, a, d, f, g, h, i, j):
        a = self.func_c(a, self.func_c(self.func_c(self.func_e(d, f, g), h), j))
        return self.func_c(self.func_b(a, i), d)

    def func_j(self, a, d, e, g, h, i, j):
        a = self.func_c(a, self.func_c(self.func_c(self.func_f(d, e, g), h), j))
        return self.func_c(self.func_b(a, i), d)

    def func_k(self, a, d, e, f, h, i, j):
        a = self.func_c(a, self.func_c(self.func_c(self.func_g(d, e, f), h), j))
        return self.func_c(self.func_b(a, i), d)

    def func_m(self, a):
        d = ''
        c = 0
        while c <= 3:
            b = c_int(c_uint(a).value >> 8 * c & 255).value
            e = "0" + hex(b)[2:]
            d += e[len(e) - 2: len(e)]
            c += 1
        return d

    def func_n(self, a):
        a = a.replace(r'\r\n', r'\n')
        b = ''
        for c in a:
            d = ord(c)
            if 128 > d:
                b += chr(d)
            elif 2048 > d > 127:
                b += chr(d >> 6 | 192)
                b += chr(63 & d | 128)
            else:
                b += chr(d >> 12 | 224)
                b += chr(d >> 6 & 63 | 128)
                b += chr(63 & d | 128)
        return b

    def func_l(self, a):
        c = len(a)
        d = c + 8
        e = (d - d % 64) / 64
        f = 16 * (e + 1)
        g = [0] * f
        i = 0
        while c > i:
            b = (i - i % 4) / 4
            h = i % 4 * 8
            g[b] = g[b] | ord(a[i]) << h
            i += 1
        b = (i - i % 4) / 4
        h = i % 4 * 8
        g[b] = g[b] | 128 << h
        g[f - 2] = c << 3
        g[f - 1] = c_uint(c).value >> 29
        return g


def main():
    weitao = WeiTao()


if __name__ == '__main__':
    main()
