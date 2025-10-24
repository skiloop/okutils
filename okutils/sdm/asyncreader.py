import asyncio
import os
import struct
from typing import Callable, Tuple, Any, AsyncGenerator

import aiofiles
import re
import brotli
import zlib
import sys
from .decoders import gzip_decompress_by_zlib
from .errors import InvalidFileError, KeyNotMatchPatternError, ReaderError

class AsyncReader:
    """async reader for bin file

    Args:
        fn: bin file name
        decoder: decoder function

    Attributes:
        VERBOSE: verbose mode
        DEFAULT_MAX_KEY_SIZE: default max key size
        DEFAULT_MAX_VALUE_SIZE: default max value size
    """
    VERBOSE = False
    DEFAULT_MAX_KEY_SIZE = 1024
    DEFAULT_MAX_VALUE_SIZE = 0
    def __init__(self, fn, decoder=gzip_decompress_by_zlib):
        self._fsz = float(os.path.getsize(fn))
        self._nread = 0
        self.fn = fn
        self.lock = asyncio.Lock()
        self.decoder = decoder
        self.fd = None

    async def open(self):
        """
        open file
        :return:
        """
        if self.fd is not None:
            return
        self.fd = await aiofiles.open(self.fn, mode='rb')

    async def __aenter__(self):
        await self.open()
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        key, value = await self.readone()
        if key is None:
            raise StopAsyncIteration
        return key, value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            await self.fd.close()

    @staticmethod
    def log(msg, *args, **kwargs):
        if AsyncReader.VERBOSE:
            print(msg.format(*args, **kwargs), file=sys.stderr)

    async def _readone_i(self, key_only=False, decoder=None, pattern=None):
        if decoder is None:
            decoder = self.decoder
        sz0 = await self.fd.read(4)
        if len(sz0) == 0:
            return None, None
        if len(sz0) != 4:
            raise InvalidFileError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        fn = await self.fd.read(sz)
        if len(fn) != sz:
            raise InvalidFileError('invalid file')
        self._nread += sz + 4
        try:
            if pattern is not None and not pattern.match(fn.decode()):
                raise KeyNotMatchPatternError('key not match pattern')
        except UnicodeDecodeError as e:
            raise InvalidFileError('invalid file') from e
        sz0 = await self.fd.read(4)
        if len(sz0) != 4:
            raise InvalidFileError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        if key_only:
            await self.fd.seek(sz, 1)
            return fn, None
        conn = await self.fd.read(sz)
        if len(conn) != sz:
            raise InvalidFileError('invalid file')
        self._nread += sz + 4
        if decoder:
            conn = decoder(conn)
        return fn, conn

    async def seek_next(self, **kwargs):
        """
        seek to next document
        :param kwargs:
        :return:
        """
        original_pos = await self.fd.tell()
        try:
            return await self._seek_next_i(**kwargs)
        finally:
            await self.fd.seek(original_pos)

    async def _seek_next_i(self, **kwargs):
        """
        seek to next document
        :param kwargs:
        :return:
        """
        offset = kwargs.get('offset')
        if offset is not None:
            await self.fd.seek(offset)
        current_pos = await self.fd.tell()
        found = False
        max_key_size = kwargs.get('max_key_size', self.DEFAULT_MAX_KEY_SIZE)
        max_value_size = kwargs.get(
            'max_value_size', self.DEFAULT_MAX_VALUE_SIZE)
        pattern = kwargs.get('pattern', None)
        if pattern is not None and not isinstance(pattern, re.Pattern):
            pattern = re.compile(pattern)
        decoder = kwargs.get('decoder', self.decoder)
        self.log("start seek_next from position: {}", current_pos)
        while True:
            try:
                key = await self._check_if_next_is_key(max_key_size, pattern)
                if key is not None:
                    self.log("found key, current_pos: {}, key: {}", current_pos, key)
                    value = await self._check_if_next_is_value(max_value_size, decoder)
                    if value is not None:
                        found = True
                        self.log("found, current_pos: {}, key: {}, value: {}", current_pos, key, value[:30])
                        break
            except (brotli.error, zlib.error, UnicodeDecodeError) as e:
                self.log("seek error: {}, seek to next document", e)
            current_pos += 1
            if current_pos % 1000 == 0:
                self.log("current_pos: {}, _fsz: {}", current_pos, self._fsz)
            if current_pos > self._fsz:
                self.log("end of file, current_pos: {}, _fsz: {}", current_pos, self._fsz)
                break
            await self.fd.seek(current_pos)
        if not found:
            return None
        return current_pos

    async def _check_if_next_is_key(self, max_key_size: int, key_pattern: re.Pattern):
        sz0 = await self.fd.read(4)
        if len(sz0) == 0 or len(sz0) != 4:
            return None
        (sz,) = struct.unpack("I", sz0)
        if sz > max_key_size:
            return None
        fn = await self.fd.read(sz)
        if len(fn) != sz:
            return None
        fn = fn.decode()
        if key_pattern is not None and not key_pattern.match(fn):
            return None
        return fn

    async def _check_if_next_is_value(self, max_value_size: int, decoder: "Callable"):
        sz0 = await self.fd.read(4)
        if len(sz0) == 0 or len(sz0) != 4:
            return None
        (sz,) = struct.unpack("I", sz0)
        if sz > max_value_size > 0:
            return None
        conn = await self.fd.read(sz)
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

    async def readone(self, **kwargs) -> Tuple[bytes, Any]:
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
        if pattern is not None and not isinstance(pattern, re.Pattern):
            pattern = re.compile(pattern)
        async with self.lock:
            original_pos = await self.fd.tell()
            try:
                return await self._readone_i(key_only, decoder, pattern)
            except (IOError, zlib.error, ReaderError) as e:
                print(f"read error: {e}, seek to next document")
                pos = await self._seek_next_i(offset=original_pos, pattern=pattern)
                if pos is None:
                    print("no next document, return None")
                    return None, None
                print(f"next document found at position: {pos}")
                await self.fd.seek(pos)
                self._nread = pos
                return await self._readone_i(key_only, decoder, pattern)
            except Exception as e:
                raise e

    async def readone_at(self, pos, **kwargs) -> Tuple[bytes, Any]:
        """
        read document at specified position
        :param pos: document position
        :param pattern: pattern to match key, if None use default pattern
        :return:  (key, content)
        """
        async with self.lock:
            await self.fd.seek(pos)
            key_only = kwargs.get('key_only', False)
            decoder = kwargs.get('decoder', None)
            pattern = kwargs.get('pattern', None)
            if pattern is not None and not isinstance(pattern, re.Pattern):
                pattern = re.compile(pattern)
            return await self._readone_i(key_only, decoder, pattern)
    async def iter(self, **kwargs) -> AsyncGenerator[Tuple[bytes, Any], None]:
        """
        Iterate over the binary file asynchronously.
        :param key_only: Read key only, ignore content.
        :param pattern: pattern to match key, if None use default pattern
        :return: Async generator of (key, content).
        """
        try:
            while True:
                key, value = await self.readone(**kwargs)
                if key is None:
                    break
                yield key, value
        except Exception as e:
            # Log or handle the exception if needed
            raise e

    async def apply(self, action, **kwargs):
        """

        :param action: func to handle doc, parameters are like (key:str, value:bytes)

        :return:
        """
        async for key, value in self.iter(**kwargs):
            if asyncio.iscoroutinefunction(action):
                await action(key.decode(), value)
            else:
                action(key.decode(), value)
