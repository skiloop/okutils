import os
import re
import struct
import sys
import threading
from typing import Callable, Tuple, Any, Iterable
import zlib
import brotli

from .decoders import brotli_decompress, get_decompresser


class Reader:
    DEFAULT_MAX_KEY_SIZE = 1024
    DEFAULT_MAX_VALUE_SIZE = 0
    VERBOSE = False

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
    
    @staticmethod
    def log(msg, *args, **kwargs):
        if Reader.VERBOSE:
            print(msg, *args, **kwargs)

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

    def seek_next(self, **kwargs):
        """
        seek to next document
        :param kwargs:
        :return:
        """
        original_pos = self.fd.tell()
        try:
            return self._seek_next_i(**kwargs)
        finally:
            self.fd.seek(original_pos)

    def _seek_next_i(self, **kwargs):
        """
        seek to next document
        :param kwargs:
        :return:
        """
        offset = kwargs.get('offset')
        if offset is not None:
            self.fd.seek(offset)
        current_pos = self.fd.tell()
        found = False
        max_key_size = kwargs.get('max_key_size', self.DEFAULT_MAX_KEY_SIZE)
        max_value_size = kwargs.get(
            'max_value_size', self.DEFAULT_MAX_VALUE_SIZE)
        pattern = kwargs.get('pattern', None)
        if pattern is not None and not isinstance(pattern, re.Pattern):
            pattern = re.compile(pattern)
        decoder = kwargs.get('decoder', self.decoder)
        self.log("start seek_next from position: ", current_pos, file=sys.stderr)
        while True:
            try:
                key = self._check_if_next_is_key(max_key_size, pattern)
                if key is not None:
                    self.log("found key, current_pos: %d, key: %s", current_pos, key, file=sys.stderr)
                    value = self._check_if_next_is_value(max_value_size, decoder)
                    if value is not None:
                        found = True
                        self.log("found, current_pos: %d, key: %s, value: %s", current_pos, key, value[:30], file=sys.stderr)
                        break
            except (brotli.error, zlib.error, UnicodeDecodeError) as e:
                self.log("seek error: %s, seek to next document", e, file=sys.stderr)
            current_pos += 1
            if current_pos % 1000 == 0:
                self.log("current_pos: %d, _fsz: %d", current_pos, self._fsz, file=sys.stderr)
            if current_pos > self._fsz:
                self.log("end of file, current_pos: %d, _fsz: %d", current_pos, self._fsz, file=sys.stderr)
                break
            self.fd.seek(current_pos)
        if not found:
            return None
        return current_pos

    def _check_if_next_is_key(self, max_key_size: int, key_pattern: re.Pattern):
        sz0 = self.fd.read(4)
        if len(sz0) == 0 or len(sz0) != 4:
            return None
        (sz,) = struct.unpack("I", sz0)
        if sz > max_key_size:
            return None
        fn = self.fd.read(sz)
        if len(fn) != sz:
            return None
        if key_pattern is not None and not key_pattern.match(fn):
            return None
        return fn

    def _check_if_next_is_value(self, max_value_size: int, decoder: "Callable"):
        sz0 = self.fd.read(4)
        if len(sz0) == 0 or len(sz0) != 4:
            return None
        (sz,) = struct.unpack("I", sz0)
        if sz > max_value_size > 0:
            return None
        conn = self.fd.read(sz)
        if len(conn) != sz:
            return None
        if decoder is not None:
            conn = decoder(conn)
        return conn

    def progress(self) -> float:
        """
        current reading progress
        :return:
        """
        if self._fsz == 0.0:
            return 1.0
        return float(self._nread) / self._fsz

    def readone(self, **kwargs) -> Tuple[bytes, Any]:
        """
        read a document from file
        :param key_only: just return document key,and content set to none,
                file pointer set to next document
        :param decoder: content decoder, if None use default decoder
        :param pattern: pattern to match key, if None use default pattern
        :return: (key, content), content type is the same decoder return type
        """
        key_only = kwargs.get('key_only', False)
        decoder = kwargs.get('decoder', None)
        pattern = kwargs.get('pattern', None)
        with self.lock:
            original_pos = self.fd.tell()
            try:
                return self._readone_i(key_only, decoder)
            except (IOError, zlib.error) as e:
                print(f"read error: {e}, seek to next document", file=sys.stderr)
                pos = self._seek_next_i(offset=original_pos, pattern=pattern)
                if pos is None:
                    print("no next document, return None", file=sys.stderr)
                    return None, None
                print(f"next document found at position: {pos}", file=sys.stderr)
                self.fd.seek(pos)
                self._nread = pos
                return self._readone_i(key_only, decoder)
            except Exception as e:
                raise e

    def readone_at(self, pos) -> Tuple[bytes, Any]:
        """
        read document at specified position
        :param pos: document position
        :return:  (key, content)
        """
        with self.lock:
            self.fd.seek(pos)
            return self._readone_i()

    def iter(self, **kwargs) -> Iterable[Tuple[bytes, Any]]:
        """
        iter bin file
        :param key_only: read key only, ignore content
        :param pattern: pattern to match key, if None use default pattern
        :return: iterable of (key, content)
        """
        while True:
            key, value = self.readone(**kwargs)
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
