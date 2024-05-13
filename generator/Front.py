import threading

import CONSTANTS
from generator import PageManager
from generator.PageRunner import PageRunner

class Front(PageRunner):
    # Clase encargada de la ejecución del front-end.
    # En ella se deben definir los métodos para la gestión de estas páginas.

    def _generate_page_address(self) -> str:
        # Método para acceder a la API que nos dará la dirección de la página
        return CONSTANTS.ADDRESS

    def __init__(self, user, page_name, page_port):
        super().__init__(user, page_name, page_port)
        self._running = False
        self._page_adress = self._generate_page_address()

    def get_page_address(self) -> str:
        return "http://localhost:" + str(self._page_port)

    def is_running(self) -> bool:
        return self._running

    def set_running(self, is_running: bool):
        self._running = is_running