import abc


class HashBase(object):
    @abc.abstractmethod
    def set(self, name, value):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def get(self, name):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def has(self, name):
        raise NotImplementedError('virtual function called')
