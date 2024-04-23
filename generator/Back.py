import threading
from flask import Flask, request

import CONSTANTS
from generator.PageRunner import PageRunner

class Back(PageRunner):
    # Clase encargada de la ejecución de la API Flask asociado a una página web.
    # En ella se deben definir los métodos para la gestión de estas páginas.

    app:Flask

    def __init__(self, user, page_name, page_port):
        super().__init__(user, page_name, page_port)
        self.app = Flask(__name__)

        # Define las rutas de la aplicación
        self.app.route('/')(self.home)
        self.app.route('/saludo')(self.saludo)

    def agregar_ruta(self, route, function, methods=None):
        # Agrega una ruta de forma dinámica
        self.app.add_url_rule(route, view_func=function, methods=methods)

    def home(self):
        # Define la vista para la ruta '/'
        return "¡Bienvenido a la aplicación Flask!"

    def saludo(self):
        # Define la vista para la ruta '/saludo'
        return "¡Hola! Este es un saludo desde Flask."

    def init_page(self):
        #Metodo encargado de iniciar la ejecucion de una pagina
        self.app.run(host=CONSTANTS.ADRESS, port=self.page_port)
        print("Pagina ejecutando")

    def get_app_adress(self):
        return CONSTANTS.ADRESS + ":" + str(self.page_port)

    def run(self):
        print("Hilo correspondiente al back de la pagina " + self.page_name + " del usuario " + self.user + ". Thread ID: " + threading.currentThread().getName())
        print("puerto: " + str(self.page_port))
        self.init_page()