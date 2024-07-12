import unittest

from okutils.tools import mp_append_log


class ToolTestCase(unittest.TestCase):
    def test_mp_append_log(self):
        data = "hello world!"
        size = mp_append_log("./log.txt", data)
        self.assertEqual(size, 0, f"file size not 0, get {size}")  # add assertion here
        mp_append_log("./log.txt", data)
        size = mp_append_log("./log.txt", data)
        expected = 2 * len(data)
        self.assertEqual(size, expected, f"file size ｛size｝, expected: {expected}")  # add assertion here


if __name__ == '__main__':
    unittest.main()
