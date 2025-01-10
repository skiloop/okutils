import os
import timeit

from okutils.sdm import Reader, Writer
from okutils.sdm.decoders import gzip_decompress, gzip_decompress_by_zlib
from okutils.sdm.encoders import gzip_compress, gzip_compress_by_zlib
from tests.utils import random_string

# 测试模块函数性能
reader_test_setup_code = "from math import sqrt"
test_code = "sqrt(16)"
_readfile_ = "read.bin"
_writefile_ = "write.bin"


def check_read(reader: Reader):
    for _ in reader.iter():
        pass


def check_writer(writer: Writer):
    key, value = random_string(10), random_string(500)
    writer.append(key, value)


wt = Writer(_readfile_)

for _ in range(10000):
    check_writer(wt)

_reader = Reader(_readfile_, decoder=gzip_decompress)
execution_time = timeit.timeit("check_read(_reader)", globals=globals(), number=1000000)

print(f"gzip解压执行时间: {execution_time:.6f} 秒")

_reader = Reader(_readfile_, decoder=gzip_decompress_by_zlib)
execution_time = timeit.timeit("check_read(_reader)", globals=globals(), number=1000000)

print(f"zlib解压执行时间: {execution_time:.6f} 秒")

_writer = Writer(_writefile_, encoder=gzip_compress)
execution_time = timeit.timeit("check_writer(_writer)", globals=globals(), number=1000000)

print(f"gzip压缩执行时间: {execution_time:.6f} 秒")

os.remove(_writefile_)
_writer = Writer(_writefile_, encoder=gzip_compress_by_zlib)
execution_time = timeit.timeit("check_writer(_writer)", globals=globals(), number=1000000)
print(f"zlib压缩执行时间: {execution_time:.6f} 秒")
