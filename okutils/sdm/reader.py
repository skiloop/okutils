import os
import struct
import threading

from okutils.sdm.decoders import brotli_decompress, gzip_decompress_by_zlib


def get_decompresser(filename: str):
    if filename.endswith(".br.bin"):
        return brotli_decompress
    return gzip_decompress_by_zlib


class Reader:
    def __init__(self, fn, decoder=None):
        self._fsz = float(os.path.getsize(fn))
        self._nread = 0
        self.fn = fn
        self.fd = open(fn, 'rb')
        self.lock = threading.Lock()
        self.decoder = get_decompresser(fn) if decoder is None else decoder

    def __del__(self):
        self.fd.close()

    def _readone_i(self, key_only=False):
        sz0 = self.fd.read(4)
        if len(sz0) == 0:
            return None, None
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        fn = self.fd.read(sz)
        if len(fn) != sz:
            raise IOError('invalid file')
        self._nread += sz + 4

        sz0 = self.fd.read(4)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        if key_only:
            self.fd.seek(sz, 1)
            return fn, None
        conn = self.fd.read(sz)
        if len(conn) != sz:
            raise IOError('invalid file')
        self._nread += sz + 4
        if self.decoder:
            conn = self.decoder(conn)
        return fn, conn

    def progress(self):
        if self._fsz == 0.0:
            return 1.0
        return float(self._nread) / self._fsz

    def readone(self, key_only=False):
        with self.lock:
            return self._readone_i(key_only)

    def readone_at(self, pos):
        with self.lock:
            self.fd.seek(pos)
            return self._readone_i()

    def iter(self, key_only=False):
        while True:
            key, value = self.readone(key_only)
            if key is None:
                break
            yield key, value

    def apply(self, action):
        """

        :param action: func to handle doc, parameters are like (key:str, value:bytes)

        :return:
        """
        for key, value in self.iter():
            action(key.decode(), value)


class BrotliReader(Reader):
    """
    for convinionous
    """

    def __init__(self, filename: str, path: str = None):
        fn = os.path.join(path or ".", filename + ".br.bin")
        super().__init__(fn, brotli_decompress)
