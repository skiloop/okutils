import asyncio
import os.path
import random
import tempfile
import tracemalloc
import unittest

from okutils.sdm import Reader, Writer, AsyncReader
from okutils.sdm.decoders import gzip_decompress, gzip_decompress_by_zlib, brotli_decompress
from okutils.sdm.encoders import gzip_compress, gzip_compress_by_zlib, brotli_compress
from tests.utils import random_string, write_items

tracemalloc.start()


def get_temple_file(prefix=None, suffix=None):
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as temp_file:
        return temp_file.name


def remove_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def create_bin(filename, data):
    writer = Writer(filename)
    for key, value in data:
        writer.append(key, value)

def create_random_bin(filename):
    count = random.randint(10, 20)
    data = [(random_string(10).encode(), random_string(random.randint(50, 200)).encode()) for _ in range(count)]
    writer = Writer(filename)
    for key, value in data:
        writer.append(key, value)
    return count

def check_coders(test: unittest.TestCase, name, encoder, decoder):
    items = [
        (f"item://{random_string(10)}".encode(), random_string(random.randint(50, 200)).encode()) for _ in
        range(random.randint(4, 10))
    ]
    filename = get_temple_file(prefix="okutils_", suffix=".gz.bin")
    positions = write_items(filename, encoder, items)
    test.assertEqual(len(positions), len(items), "writer result size not equal")
    reader = Reader(filename, decoder=decoder)
    idx = random.choice(range(len(items)))
    key, value = reader.readone_at(positions[idx])
    item = items[idx]
    test.assertEqual(key, item[0], "read error, key not match")
    test.assertEqual(value, item[1], "read error, value not match")
    remove_file(filename)


class SDMTestCase(unittest.TestCase):

    def test_gzip_coder(self):
        check_coders(self, "gzip", gzip_compress, gzip_decompress)

    def test_gzip_mix_coder(self):
        check_coders(self, "gzip-zlib", gzip_compress, gzip_decompress_by_zlib)
        check_coders(self, "zlib-gzip", gzip_compress_by_zlib, gzip_decompress)

    def test_zlib_coder(self):
        check_coders(self, "zlib", gzip_compress_by_zlib, gzip_decompress_by_zlib)

    def test_brotli_coder(self):
        check_coders(self, "brotli", brotli_compress, brotli_decompress)

    async def _async_read(self):
        data = [(random_string(10).encode(), random_string(100).encode()) for _ in range(10)]
        filename = get_temple_file()
        create_bin(filename, data)
        kv_iter = iter(data)
        async with AsyncReader(filename) as reader:
            async for key, value in reader:
                k, v = next(kv_iter)
                self.assertEqual(key, k)
                self.assertEqual(value, v)
        remove_file(filename)
    
    def test_seek_next(self):
        filename = get_temple_file()
        count = create_random_bin(filename)
        reader = Reader(filename)
        for _ in range(random.randint(1, count)):
            pos = reader.fd.tell()
            key, value = reader.readone()
        print(f"pos: {pos}, key: {key}, value: {value}")
        reader.fd.seek(pos - 13)
        doc_pos = reader.seek_next(max_key_size=15)
        self.assertIsNotNone(doc_pos)
        doc_key, doc_value = reader.readone_at(doc_pos)
        self.assertEqual(doc_pos, pos)
        self.assertEqual(doc_key, key)
        self.assertEqual(doc_value, value)
        # test read next on wrong position
        reader.fd.seek(pos - 23)
        doc_key, doc_value = reader.readone()
        self.assertEqual(doc_key, key, "failed to read on wrong position, key not match")
        self.assertEqual(doc_value, value, "failed to read on wrong position, value not match")
        remove_file(filename)


    def test_async_read(self):
        asyncio.run(self._async_read())


if __name__ == '__main__':
    unittest.main()
