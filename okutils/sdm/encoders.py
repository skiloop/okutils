import gzip
import io
import struct
import time
import zlib


def gzip_compress(raw: bytes):
    with io.BytesIO() as fo:
        with gzip.GzipFile(fileobj=fo, mode='wb') as f:
            f.write(raw)
        return fo.getvalue()


def gzip_compress_by_zlib_with_header(data: bytes, filename: str = None):
    header = b'\x1f\x8b\x08\x00'  # 基础 gzip 头 (不包含文件名)
    mtime = struct.pack("<I", int(time.time()))  # 修改时间（4 字节，当前时间）
    xfl_os = b'\x00\x03'  # XFL=0x00 (无特定压缩选项), OS=0x03 (Unix)
    header += mtime + xfl_os

    # 如果提供了文件名，更新头信息
    if filename:
        header = header[:3] + b'\x08' + header[4:]  # 设置 FLG=0x08
        header += filename.encode('utf-8') + b'\x00'  # 添加文件名和结尾的 0x00

    # 压缩数据
    compressed_data = zlib.compress(data)

    # 构造 gzip 文件尾 (CRC32 和原始数据长度)
    crc32 = struct.pack("<I", zlib.crc32(data))  # 计算 CRC32
    isize = struct.pack("<I", len(data))  # 原始数据长度（4 字节，低字节在前）
    footer = crc32 + isize

    # 返回完整 gzip 数据
    return header + compressed_data[2:-4] + footer


def gzip_compress_by_zlib(data: bytes):
    # 压缩数据
    # 创建 zlib 的压缩对象，指定 wbits=16+15 生成 gzip 格式
    compress = zlib.compressobj(wbits=16 + 15)

    # 压缩数据并关闭流
    gzip_data = compress.compress(data) + compress.flush()
    return gzip_data
