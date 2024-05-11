import threading

import CONSTANTS
from generator import PageManager
from generator.PageRunner import PageRunner

class Front(PageRunner):
    # Clase encargada de la ejecución del front-end.
    # En ella se deben definir los métodos para la gestión de estas páginas.

    page_adress:str
    back_address:str

    def generate_page_adress(self) -> str:
        # Método para acceder a la API que nos dará la dirección de la página
        return CONSTANTS.ADRESS

    def __init__(self, user, page_name, page_port, back_adress):
        super().__init__(user, page_name, page_port)
        self.back_address = back_adress
        self.page_adress = self.generate_page_adress()

    def get_page_adress(self) -> str:
        return "http://localhost:" + str(self.page_port)

    def build(self):
        PageManager.PageManager.build_project(self.user, self.page_name)

    def run(self):
        print("----EN FRONT.RUN()----")
        self.start_running_thread(target=self.target, args=(self.user, self.page_name, self.page_port))

    def stop(self):
        PageManager.PageManager.kill_project(self.page_port)