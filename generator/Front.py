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
        self._dev = False
        self._page_adress = None
        self._address_event = threading.Event()
        self._tunnel_process = None

    def set_page_address(self, address):
        with self._output_ready:
            self._page_address = address
            self._address_event.set()  # Indica que el valor está listo
            self._address_event.clear()  # Reinicia el evento para futuras esperas

    def get_page_address(self) -> str:
        self._address_event.wait()  # Espera hasta que el evento esté listo
        with self._output_ready:
            return self._page_address

    def is_running(self) -> bool:
        return self._running

    def is_running_dev(self) -> bool:
        return self._dev

    def set_running(self, is_running: bool):
        self._running = is_running

    def set_running_dev(self, dev: bool):
        self._dev = dev

    def set_tunnel_process(self, process):
        with self._output_ready:
            self._tunnel_process = process
            self._output_ready.notify_all()

    def get_tunnel_process(self):
        with self._output_ready:
            while self._tunnel_process is None:
                self._output_ready.wait()
            return self._tunnel_process