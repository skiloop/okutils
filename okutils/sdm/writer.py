import json
import os
import struct
from pathlib import Path

from okutils.sdm.encoders import gzip_compress_by_zlib
from okutils.tools import mp_append_log


class Writer:
    """
    Writer to package small files into SDM file
    """

    def compress_item(self, name, value):
        if isinstance(name, (str,)):
            name = name.encode()
        if isinstance(value, (str,)):
            value = value.encode()
        elif isinstance(value, (dict,)):
            value = json.dumps(value, ensure_ascii=False).encode()
        if self.encoder:
            r = self.encoder(value)
        else:
            r = value
        return struct.pack("I", len(name)) + name + struct.pack("I", len(r)) + r

    def __mkdir__(self):
        path = Path(os.path.dirname(self._fn))
        path.mkdir(parents=True, exist_ok=True)

    def __init__(self, fn, encoder=gzip_compress_by_zlib):
        self._fn = fn
        self.encoder = encoder
        self.__mkdir__()

    def append(self, name, value):
        a = self.compress_item(name, value)
        pos = mp_append_log(self._fn, a)
        if pos < 0:
            raise IOError("unable to write bin file.")
        return pos

    def append_file(self, filepath: str, name: str = None):
        """
        read file and append
        :param filepath: file path
        :param name: name in SDM file, if None the filepath will be used
        :return:
        """
        if name is None:
            name = filepath
        with open(filepath, 'rb') as fin:
            content = fin.read()
        self.append(name, content)

    def filename(self):
        return self._fn

    def getsize(self):
        filename = os.path.abspath(self.filename())
        size = os.path.getsize(filename)
        return size
