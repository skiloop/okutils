import os
import struct
import threading
from typing import Callable, Tuple, Any, Iterable

from .decoders import brotli_decompress, get_decompresser


class Reader:
    def __init__(self, fn, decoder=None):
        self._fsz = float(os.path.getsize(fn))
        self._nread = 0
        self.fn = fn
        self.fd = open(fn, 'rb')
        # lock to avaid file pointer chaos
        self.lock = threading.Lock()
        self.decoder = get_decompresser(fn) if decoder is None else decoder

    def __del__(self):
        self.fd.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()

    def __enter__(self):
        return self

    def _readone_i(self, key_only=False, decoder=None):
        if decoder is None:
            decoder = self.decoder
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
        if decoder:
            conn = decoder(conn)
        return fn, conn

    def progress(self) -> float:
        """
        current reading progress
        :return:
        """
        if self._fsz == 0.0:
            return 1.0
        return float(self._nread) / self._fsz

    def readone(self, key_only=False, decoder: "Callable" = None) -> Tuple[bytes, Any]:
        """
        read a document from file
        :param key_only: just return document key,and content set to none,
                file pointer set to next document
        :param decoder: content decoder, if None use default decoder
        :return: (key, content), content type is the same decoder return type
        """
        with self.lock:
            return self._readone_i(key_only, decoder)

    def readone_at(self, pos) -> Tuple[bytes, Any]:
        """
        read document at specified position
        :param pos: document position
        :return:  (key, content)
        """
        with self.lock:
            self.fd.seek(pos)
            return self._readone_i()

    def iter(self, key_only=False) -> Iterable[Tuple[bytes, Any]]:
        """
        iter bin file
        :param key_only: read key only, ignore content
        :return: iterable of (key, content)
        """
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
