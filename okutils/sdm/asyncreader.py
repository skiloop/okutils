import asyncio
import os
import struct
from typing import Callable, Tuple, Any, AsyncGenerator

import aiofiles

from .decoders import gzip_decompress_by_zlib


class AsyncReader:
    def __init__(self, fn, decoder=gzip_decompress_by_zlib):
        self._fsz = float(os.path.getsize(fn))
        self._nread = 0
        self.fn = fn
        self.lock = asyncio.Lock()
        self.decoder = decoder
        self.fd = None

    async def open(self):
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

    async def _readone_i(self, key_only=False, decoder=None):
        if decoder is None:
            decoder = self.decoder
        sz0 = await self.fd.read(4)
        if len(sz0) == 0:
            return None, None
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        fn = await self.fd.read(sz)
        if len(fn) != sz:
            raise IOError('invalid file')
        self._nread += sz + 4

        sz0 = await self.fd.read(4)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        if key_only:
            await self.fd._file.seek(sz, 1)
            return fn, None
        conn = await self.fd.read(sz)
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

    async def readone(self, key_only=False, decoder: "Callable" = None) -> Tuple[bytes, Any]:
        """
        read a document from file
        :param key_only: just return document key,and content set to none,
                file pointer set to next document
        :param decoder: content decoder, if None use default decoder
        :return: (key, content), content type is the same decoder return type
        """
        async with self.lock:
            return await self._readone_i(key_only, decoder)

    async def readone_at(self, pos) -> Tuple[bytes, Any]:
        """
        read document at specified position
        :param pos: document position
        :return:  (key, content)
        """
        with self.lock:
            self.fd._file.seek(pos)
            return await self._readone_i()

    async def iter(self, key_only=False) -> AsyncGenerator[Tuple[bytes, Any], None]:
        """
        Iterate over the binary file asynchronously.
        :param key_only: Read key only, ignore content.
        :return: Async generator of (key, content).
        """
        try:
            while True:
                key, value = await self.readone(key_only)
                if key is None:
                    break
                yield key, value
        except Exception as e:
            # Log or handle the exception if needed
            raise e

    async def apply(self, action):
        """

        :param action: func to handle doc, parameters are like (key:str, value:bytes)

        :return:
        """
        async for key, value in self.iter():
            action(key.decode(), value)
