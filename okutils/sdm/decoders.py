import gzip
import io
import zlib


def gzip_decompress(gz_content):
    with io.BytesIO(gz_content) as fin:
        with gzip.GzipFile(fileobj=fin, mode='rb') as f:
            return f.read()


def is_gzip_data(data):
    # 检查 gzip 的头部标识
    if len(data) < 2:
        return False
    return data[0] == 0x1F and data[1] == 0x8B


def gzip_decompress_by_zlib(gz_content):
    if is_gzip_data(gz_content):
        gz_content = gz_content[10:-8]
    return zlib.decompress(gz_content, wbits=-zlib.MAX_WBITS)
