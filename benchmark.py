import os
import random
import tempfile
import timeit

from okutils.sdm import Reader, Writer
from okutils.sdm.decoders import gzip_decompress, gzip_decompress_by_zlib, brotli_decompress
from okutils.sdm.encoders import gzip_compress, gzip_compress_by_zlib, brotli_compress


def random_string(size: int = 10):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ;:."
    return "".join(random.choices(chars, k=size))


def check_read(reader: Reader):
    for _ in reader.iter():
        pass


def check_writer(writer: Writer):
    key, value = random_string(10), random_string(500)
    writer.append(key, value)


count = 10000
doc_count = 10000

# 测试模块函数性能
with tempfile.NamedTemporaryFile(prefix="okutils_") as rf:
    _readfile_ = rf.name
    wt = Writer(_readfile_)

    for _ in range(doc_count):
        check_writer(wt)

    _reader = Reader(_readfile_, decoder=gzip_decompress)
    execution_time = timeit.timeit("check_read(_reader)", globals=globals(), number=count)

    print(f"gzip decompress time: {execution_time:.6f} seconds")

    _reader = Reader(_readfile_, decoder=gzip_decompress_by_zlib)
    execution_time = timeit.timeit("check_read(_reader)", globals=globals(), number=count)

    print(f"zlib decompress time: {execution_time:.6f} seconds")

with tempfile.NamedTemporaryFile(prefix="okutils_", suffix=".br.bin") as wf:
    _readfile_ = wf.name
    wt = Writer(_readfile_, encoder=brotli_compress)
    for _ in range(doc_count):
        check_writer(wt)

    _reader = Reader(_readfile_, decoder=brotli_decompress)
    execution_time = timeit.timeit("check_read(_reader)", globals=globals(), number=count)
    print(f"brotli compress time: {execution_time:.6f} seconds")

with tempfile.NamedTemporaryFile(prefix="okutils_") as wf:
    _writefile_ = wf.name

    _writer = Writer(_writefile_, encoder=gzip_compress)
    execution_time = timeit.timeit("check_writer(_writer)", globals=globals(), number=count)

    print(f"gzip compress time: {execution_time:.6f} seconds")

    os.remove(_writefile_)
    _writer = Writer(_writefile_, encoder=gzip_compress_by_zlib)
    execution_time = timeit.timeit("check_writer(_writer)", globals=globals(), number=count)
    print(f"zlib compress time: {execution_time:.6f} seconds")

with tempfile.NamedTemporaryFile(prefix="okutils_", suffix=".br.bin") as wf:
    _writefile_ = wf.name

    _writer = Writer(_writefile_, encoder=brotli_compress)
    execution_time = timeit.timeit("check_writer(_writer)", globals=globals(), number=count)

    print(f"brotli compress time: {execution_time:.6f} seconds")
