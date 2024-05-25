from abc import abstractmethod

class Section():

    @abstractmethod
    def __init__(self, type, title):
        self._type = type
        self._title = title
        pass

    def get_type(self):
        return self._type

    def get_title(self):
        return self._title

    def set_title(self, title):
        self._title = title