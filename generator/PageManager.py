import os
import random
import shutil
import socket
import subprocess
import threading
from typing import Tuple, Dict, List
from telegram import Bot
import CONSTANTS
import psutil
from generator.PageRunner import PageRunner
from generator.Front import Front


class PageManager(object):

    _instance = None
    _running_pages: Dict[Tuple[str, str], Front] = {}

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
        #Nos posiciona en el subdirectorio indicado. Si no existe, lo crea
        #print("dir actual: " + os.getcwd())
        os.makedirs(dir_name, exist_ok=True)
        os.chdir(dir_name)
        #print("nuevo dir: " + os.getcwd())

    @staticmethod
    def go_to_main_dir():
        while os.path.basename(os.getcwd()) != CONSTANTS.MAIN_DIR:
            os.chdir("..")

    @staticmethod
    def _run_process(command):
        return subprocess.Popen(command, shell=True)

    @staticmethod
    def get_path(user, page_name):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        return os.getcwd()

    @staticmethod
    def get_user_running_pages(user) -> List[Front]:
        pages = []
        for key in PageManager._running_pages.keys():
            if key[0] == user:
                # Agregar la pagina al resultado
                pages.append(PageManager._running_pages[key])
        return pages

    @staticmethod
    def _copy_dir(origen, destino):
        try:
            # Copiar el contenido del directorio origen al directorio destino
            print("antes de copiar")
            shutil.copytree(origen, destino, dirs_exist_ok=True)
            print("despues de copiar")
        except Exception as e:
            print(f"Error al copiar el contenido de '{origen}' a '{destino}': {e}")

    @staticmethod
    def create_project(user, page_name, page_port):
        print("----EN PageManager.create_project----")
        print("--------", threading.current_thread().getName())

        #Crea el proyecto de la página
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        command = 'npx create-next-app ' + str(page_name) + ' --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        PageManager._running_pages[(user, page_name)].set_process(PageManager._run_process(command))

    @staticmethod
    def copy_template(user, page_name, page_port):
        #Se copian los templates en el nuevo proyecto

        #Obtener directorio origen
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.TEMPLATE_DIR)
        origin_dir = os.getcwd()

        #Obtener directorio destino
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)

        #Copiar
        PageManager._copy_dir(origin_dir, os.getcwd())


    @staticmethod
    def run_dev(user, page_name, page_port):
        # Ejecuta la página en modo Dev para que el usuario visualice las modificaciones
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npm run dev -- --port=' + str(page_port)
        PageManager._running_pages[(user, page_name)].set_process(PageManager._run_process(command))

    @staticmethod
    def build_project(user, page_name, page_port):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npx next build '
        PageManager._running_pages[(user, page_name)].set_process(PageManager._run_process(command))

    @staticmethod
    def run_project(user, page_name, page_port):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npm start -- --port ' + str(page_port)
        PageManager._running_pages[(user, page_name)][1].set_process(PageManager._run_process(command))

    @staticmethod
    def add_page(user, page_name) -> Front:
        #Crear la entrada
        PageManager._running_pages[(user, page_name)] = None

        #Crear la pagina
        page = Front(user, page_name, PageManager.get_port(), False)

        #Agregarla a la coleccion
        PageManager._running_pages[(user, page_name)] = page
        return page

    @staticmethod
    def get_page(user, page_name) -> Front:
        return PageManager._running_pages[(user, page_name)]

    @staticmethod
    def stop_page(user, page_name):
        # Matar la página
        PageManager._running_pages[(user, page_name)].stop_exec()

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
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        PageManager.go_to_dir('img')
        file = await self.bot.get_file(image_id)
        path = os.getcwd() + '\\' + str(short_id) + '.jpg'
        await file.download_to_drive(path)



