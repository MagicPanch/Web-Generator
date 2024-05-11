import os
import random
import socket
import subprocess
import threading
from typing import Tuple, Dict, List
from telegram import Bot
import CONSTANTS
import psutil
from generator import DBManager
from generator.PageRunner import PageRunner
from generator.Front import Front


class PageManager(object):

    _instance = None
    running_pages: Dict[Tuple[str, str], List[PageRunner]] = {}

    @staticmethod
    def _is_port_in_use(port) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
            except OSError as e:
                if e.errno == socket.errno.EADDRINUSE:
                    return True  # El puerto está ocupado
                else:
                    # Otro error
                    raise
            return False  # El puerto está disponible

    @staticmethod
    def get_port() -> int:
        port = random.randint(CONSTANTS.MIN_PORT, CONSTANTS.MAX_PORT)
        if not PageManager._is_port_in_use(port):
            return port
        else:
            return PageManager.get_port()

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PageManager()
        return cls._instance

    def __init__(self) -> None:
        if PageManager._instance is None:
            PageManager._instance = self
            self.running_pages = {}
            self.bot = Bot(token=CONSTANTS.TELEGRAM_BOT_TOKEN)
        else:
            raise Exception("No se puede crear otra instancia de PageManager")

    @staticmethod
    def go_to_dir(dir_name):
        #Nos posiciona en el directorio indicado. Si no existe, lo crea
        #print("dir actual: " + os.getcwd())
        os.makedirs(dir_name, exist_ok=True)
        os.chdir(dir_name)
        #print("nuevo dir: " + os.getcwd())

    @staticmethod
    def go_to_main_dir():
        #print("dir actual: " + os.getcwd())
        #Nos posiciona en el directorio user-pages
        if os.path.basename(os.getcwd()) == CONSTANTS.MAIN_DIR:
            os.chdir(CONSTANTS.USER_PAGES_DIR)
        elif (os.path.basename(os.getcwd()) == CONSTANTS.GENERATOR_DIR) or (os.path.basename(os.getcwd()) == CONSTANTS.CHATBOT_DIR):
            os.chdir("..")
            os.makedirs(CONSTANTS.USER_PAGES_DIR, exist_ok=True)
            os.chdir(CONSTANTS.USER_PAGES_DIR)
        else:
            while os.path.basename(os.getcwd()) != CONSTANTS.USER_PAGES_DIR:
                os.chdir("..")
        #print("nuevo dir: " + os.getcwd())

    @staticmethod
    def _run_process(command):
        return subprocess.Popen(command, shell=True)

    @staticmethod
    def get_path(user, page_name):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        return os.getcwd()

    @staticmethod
    def get_user_pages(user):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        return os.listdir(os.getcwd())

    @staticmethod
    def get_running_user_pages(user):
        pages = []
        for key in PageManager.running_pages.keys():
            if key[0] == user:
                # Agregar la lista correspondiente al resultado
                pages.append(PageManager.running_pages[key][1])
        return pages

    @staticmethod
    def create_project(user, page_name):
        #Crea el proyecto de la página
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        command = 'npx create-next-app ' + str(page_name) + ' --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        PageManager.running_pages[(user, page_name)][1].set_process(PageManager._run_process(command))

    @staticmethod
    def run_dev(user, page_name, port):
        # Ejecuta la página en modo Dev para que el usuario visualice las modificaciones
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npm run dev -- --port=' + str(port)
        PageManager.running_pages[(user, page_name)][1].set_process(PageManager._run_process(command))

    @staticmethod
    def build_project(user, page_name):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npx next build '
        PageManager.running_pages[(user, page_name)][1].set_process(PageManager._run_process(command))

    @staticmethod
    def run_project(user, page_name, port):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npm start -- --port ' + str(port)
        PageManager.running_pages[(user, page_name)][1].set_process(PageManager._run_process(command))

    @staticmethod
    def start_page(target, args) -> str:
        print("----EN START PAGE----")

        # Crear back y front
        PageManager.running_pages[(args[0], args[1])] = [None, None]
        # Generator.running[(args[0], args[1])][0] = Back(args[0], args[1], PageManager.current_back_port)
        PageManager.running_pages[(args[0], args[1])][1] = Front(args[0], args[1], PageManager.get_port(), "")  # running[(user, page_name)][0].get_app_adress())
        print("----OBJETO FRONT CREADO----")

        # Iniciar la ejecucion de los hilos
        # running[(user, page_name)][0].start()
        PageManager.running_pages[(args[0], args[1])][1].set_target(target)
        PageManager.running_pages[(args[0], args[1])][1].start()
        # Agregar ruta
        # running[(user, page_name)][0].agregar_ruta('/get-producto', GenericRoutes.get_product, ['GET'])

        return PageManager.running_pages[(args[0], args[1])][1].get_page_adress()

    @staticmethod
    def stop_page(user, page_name):
        # Matar la página
        PageManager.running_pages[(user, page_name)][1].stop()

    @staticmethod
    def get_pid(port):
        """
        Esta función toma un puerto como argumento y retorna el ID de proceso (PID)
        del proceso que escucha en ese puerto, si se encuentra alguno.

        :param port: El puerto a buscar.
        :return: El ID de proceso (PID) del proceso que escucha en el puerto dado,
                 o None si no se encuentra ningún proceso que escuche en ese puerto.
        """
        # Iterar sobre todos los procesos en ejecución
        for process in psutil.process_iter(['pid']):
            try:
                # Obtener las conexiones de red del proceso
                connections = process.connections()

                # Iterar sobre las conexiones y verificar si alguna está en el puerto objetivo
                for conn in connections:
                    # Verificar si la conexión está en el puerto objetivo y en estado de escucha
                    if conn.status == 'LISTEN' and conn.laddr.port == port:
                        # Retornar el PID del proceso que escucha en el puerto
                        return process.pid

            except psutil.NoSuchProcess:
                # El proceso puede haber terminado durante la iteración
                pass

        # Si no se encontró ningún proceso que escuche en el puerto
        return None

    @staticmethod
    def kill_project(port):
        process = psutil.Process(PageManager.get_pid(port))
        process.terminate()
        process.wait()

    async def download_telegram_image(self, user, page_name, image_id, short_id):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        PageManager.go_to_dir('img')
        print("path actual: " + os.getcwd())
        file = await self.bot.get_file(image_id)
        path = os.getcwd() + '\\' + str(short_id) + '.jpg'
        print("path de la imagen con nombre: " + str(path))
        await file.download_to_drive(path)
        print("Imagen descargada con éxito.")



