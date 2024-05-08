import threading
from abc import ABC, abstractmethod

class PageRunner(threading.Thread):
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.
    user:str
    page_name:str
    page_port:int

    @abstractmethod
    def __init__(self, user, page_name, page_port):
        super().__init__()
        self.user = user
        self.page_name = page_name
        self.page_port = page_port
        pass

    @abstractmethod
    def run(self):
        pass

