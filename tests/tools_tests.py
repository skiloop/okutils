import unittest

from okutils.tools import mp_append_log


class ToolTestCase(unittest.TestCase):
    def test_mp_append_log(self):
        data = "hello world!"
        size = mp_append_log("/tmp/log.txt", data)
        self.assertEqual(size == 0, True)  # add assertion here
        size = mp_append_log("/tmp/log.txt", data)
        self.assertEqual(size == len(data), True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
