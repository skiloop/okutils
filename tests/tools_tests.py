import os.path
import struct
import unittest

from okutils.tools import mp_append_log


def pack(name: str, data: str):
    name = name.encode()
    data = data.encode()
    return struct.pack("I", len(name)) + name + struct.pack("I", len(data)) + data


class ToolTestCase(unittest.TestCase):
    def test_mp_append_log(self):
        data = b"hello world!"
        filename = "./log.txt"
        if os.path.exists(filename):
            os.remove(filename)
        size = mp_append_log(filename, data)
        self.assertEqual(size, 0, f"file size not 0, get {size}")  # add assertion here
        content = pack("item://19222", "How are you!\n I am fine!\nThank you!\nBye!\n")
        mp_append_log(filename, content)
        size = mp_append_log(filename, data)
        expected = len(data) + len(content)
        self.assertEqual(size, expected, f"file size {size}, expected: {expected}")  # add assertion here


if __name__ == '__main__':
    unittest.main()
