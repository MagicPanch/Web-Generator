import threading

class PageRunner(threading.Thread):
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.

    user:str
    page_name:str

    def __init__(self, user, page_name):
        super().__init__()
        self.user = user
        self.page_name = page_name

    def init_page(self):
        #Metodo encargado de iniciar la ejecucion de una pagina
        print("Pagina ejecutando")

    def run(self):
        print("Hilo correspondiente a la página " + self.page_name + " del usuario " + self.user + ". Thread ID: " + threading.currentThread().getName())
        self.init_page()

