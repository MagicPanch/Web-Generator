import threading
from typing import List

from generator.objects.pages.PageRunner import PageRunner
from generator.objects.sections.Section import Section


class Front(PageRunner):
    # Clase encargada de la ejecución del front-end.
    # En ella se deben definir los métodos para la gestión de estas páginas.

    def __init__(self, user, page_name, page_port):
        super().__init__(user, page_name, page_port)
        self._running = False
        self._dev = False
        self._address_event = threading.Event()
        self._tunnel_process = None
        self._page_address = None
        self._sections = []

    def set_page_address(self, address):
        self._address_event.clear()  # Reinicia el evento para futuras esperas
        self._page_address = address
        self._address_event.set()

    def get_page_address(self) -> str:
        self._address_event.wait()  # Espera hasta que el evento esté listo
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

    def add_section(self, section:Section):
        self._sections.append(section)

    def get_section(self, section_title) -> Section:
        for section in self._sections:
            if section.get_title() == section_title:
                return section
        else:
            return None

    def has_ecomm_section(self) -> bool:
        for section in self._sections:
            if section.get_title() == "ecommerce":
                return True
        else:
            return False