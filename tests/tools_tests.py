import unittest

from okutils.tools import mp_append_log


class ToolTestCase(unittest.TestCase):
    def test_mp_append_log(self):
        size = mp_append_log("/tmp/log.txt", "hello world!")
        self.assertEqual(size > 0, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
