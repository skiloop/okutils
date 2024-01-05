import json

from okutils.hash.hashbase import HashBase


class JsonHash(HashBase):
    def __init__(self, filename: str):
        self._filename = filename
        self._cache = self.__load()

    def __load(self) -> dict:
        with open(self.filename) as fin:
            return json.loads(fin.read())

    def __save(self):
        with open(self._filename, 'w') as fout:
            fout.write(json.dumps(self._cache, ensure_ascii=False, indent=4))

    def set(self, name: (str, bytes), value):
        self._cache[name] = value

    def get(self, name: (str, bytes)):
        return self._cache.get(name)

    def has(self, name: (str, bytes)) -> bool:
        return name in self._cache
