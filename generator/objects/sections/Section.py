from abc import abstractmethod

class Section():

    @abstractmethod
    def __init__(self, type):
        self._type = type
        pass

    def get_type(self):
        return self._type