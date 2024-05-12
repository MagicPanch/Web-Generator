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

    def __init__(self, user, page_name, page_port, running):
        super().__init__(user, page_name, page_port)
        self._running = running
        self._page_adress = self._generate_page_address()

    def get_page_address(self) -> str:
        return "http://localhost:" + str(self._page_port)

    def build(self):
        PageManager.PageManager.build_project(self._user, self._page_name)

    def run(self):
        while not self._stop_event.is_set():
            self._restarted.wait()  # Esperar a que se reinicie
            self._restarted.clear()
            self._target(user=self._user, page_name=self._page_name, page_port=self._page_port)

    def stop_exec(self):
        if self._running:
            PageManager.PageManager.kill_project(self._page_port)
            self._running = False