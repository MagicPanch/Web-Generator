import threading

import CONSTANTS
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
        return "http://" + self.page_adress + ":" + str(self.page_port)

    def init_page(self):
        #Metodo encargado de iniciar la ejecucion de una pagina
        print("Pagina ejecutando")

    def run(self):
        print("Hilo correspondiente al front de la pagina" + self.page_name + " del usuario " + self.user + ". Thread ID: " + threading.currentThread().getName())
        self.init_page()