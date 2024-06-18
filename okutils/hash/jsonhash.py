import json
import os.path
import time

from okutils.hash.hashbase import HashBase


class JsonHash(HashBase):
    def __init__(self, filename: str):
        self._filename = filename
        self._cache = self.__load()
        self.auto_save = False
        self.interval = 30 * 60 * 1000
        self.__last_save = self.time()

    @staticmethod
    def time():
        return int(time.time() * 1000)

    def __load(self):
        if not os.path.exists(self._filename):
            return {}
        with open(self._filename, 'r') as fin:
            content = fin.read()
        if content == "":
            return {}
        return json.loads(content)

    def save(self):
        with open(self._filename, 'w') as fout:
            fout.write(json.dumps(self._cache, ensure_ascii=False, indent=4))
        self.__last_save = self.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def set(self, name, value):
        self._cache[name] = value
        now = self.time()
        if self.auto_save and now - self.__last_save > self.interval:
            self.save()

    def get(self, name):
        return self._cache.get(name)

    def has(self, name):
        return name in self._cache
