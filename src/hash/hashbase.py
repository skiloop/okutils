import abc


class HashBase(object):
    @abc.abstractmethod
    def set(self, name: (str, bytes), value):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def get(self, name: (str, bytes)):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def has(self, name: (str, bytes)) -> bool:
        raise NotImplementedError('virtual function called')
