import random
import tempfile
import unittest

from okutils.sdm import Reader
from okutils.sdm.decoders import gzip_decompress, gzip_decompress_by_zlib, brotli_decompress
from okutils.sdm.encoders import gzip_compress, gzip_compress_by_zlib, brotli_compress
from utils import random_string, write_items


def check_coders(test: unittest.TestCase, name, encoder, decoder):
    items = [
        (f"item://{random_string(10)}".encode(), random_string(random.randint(50, 200)).encode()) for _ in
        range(random.randint(4, 10))
    ]
    with tempfile.NamedTemporaryFile(delete=True, prefix="okutils_", suffix=".gz.bin") as temp_file:
        positions = write_items(temp_file.name, encoder, items)
        test.assertEqual(len(positions), len(items), "writer result size not equal")
        reader = Reader(temp_file.name, decoder=decoder)
        idx = random.choice(range(len(items)))
        key, value = reader.readone_at(positions[idx])
        item = items[idx]
        test.assertEqual(key, item[0], "read error, key not match")
        test.assertEqual(value, item[1], "read error, value not match")


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


if __name__ == '__main__':
    unittest.main()
