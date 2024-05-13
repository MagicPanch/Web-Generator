import threading
from abc import abstractmethod


class PageRunner():
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.
    @abstractmethod
    def __init__(self, user, page_name, page_port):
        super().__init__()
        self._user = user
        self._page_name = page_name
        self._page_port = page_port
        self._process = None
        pass

    def get_user(self) -> str:
        return self._user

    def get_name(self) -> str:
        return self._page_name

    def get_port(self) -> int:
        return self._page_port

    def set_process(self, process):
        self._process = process

    def get_process(self):
        return self._process

