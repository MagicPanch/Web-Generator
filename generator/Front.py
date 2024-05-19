import threading

import CONSTANTS
from generator import PageManager
from generator.PageRunner import PageRunner

class Front(PageRunner):
    # Clase encargada de la ejecución del front-end.
    # En ella se deben definir los métodos para la gestión de estas páginas.

    def __init__(self, user, page_name, page_port):
        super().__init__(user, page_name, page_port)
        self._running = False
        self._page_adress = None
        self._tunnel_process = None

    def set_page_address(self, address):
        with self._output_ready:
            self._page_adress = address
            self._output_ready.notify_all()

    def get_page_address(self) -> str:
        with self._output_ready:
            while self._page_adress is None:
                self._output_ready.wait()
            return self._page_adress

    def is_running(self) -> bool:
        return self._running

    def set_running(self, is_running: bool):
        self._running = is_running

    def set_tunnel_process(self, process):
        with self._output_ready:
            self._tunnel_process = process
            self._output_ready.notify_all()

    def get_tunnel_process(self):
        with self._output_ready:
            while self._tunnel_process is None:
                self._output_ready.wait()
            return self._tunnel_process