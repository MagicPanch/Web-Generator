import os
import subprocess
import threading
from typing import List, Tuple, Dict
from telegram import Bot

import CONSTANTS
import psutil

from generator.PageRunner import PageRunner


class PageManager(object):

    _instance = None
    running_pages: Dict[Tuple[str, str], List[PageRunner]] = {}
    running_thread = None
    current_back_port = CONSTANTS.MIN_BACK_PORT
    current_front_port = CONSTANTS.MIN_FRONT_PORT
    bot = None

    @staticmethod
    def inc_port(current, max):
        current = current + 1
        if current > max:
            raise Exception("Se ha alcanzado el máximo número de páginas en ejecución")
        return current

    @staticmethod
    def dec_port(current, min):
        current = current - 1
        if current < min:
            current = min
        return current

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PageManager()
            cls.bot = Bot(token=CONSTANTS.TELEGRAM_BOT_TOKEN)
        return cls._instance

    def __init__(self) -> None:
        if PageManager._instance is None:
            PageManager._instance = self
        else:
            raise Exception("No se puede crear otra instancia de Generator")

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
    def start_running_thread(target, args):
        if PageManager.running_thread is None:
            PageManager.running_thread = threading.Thread(target(args[0], args[1]))
            PageManager.running_thread.start()
        else:
            PageManager.join_running_thread()
            PageManager.start_running_thread(target, args)

    @staticmethod
    def join_running_thread():
        if PageManager.running_thread is not None:
            PageManager.running_thread.join()
            PageManager.running_thread = None

    @staticmethod
    def create_project(user, page_name):
        #Crea el proyecto de la página
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        command = 'npx create-next-app ' + str(page_name) + ' --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        subprocess.Popen(command, shell=True)

    @staticmethod
    def build_project(user, page_name):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        command = 'npx next build '
        subprocess.Popen(command, shell=True)

    @staticmethod
    def run_project(user, page_name, port):
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        PageManager.running_thread.join()
        command = 'npm start -- --port ' + str(port)
        process = subprocess.Popen(command, shell=True)

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
        file = await self.bot.get_file(image_id)
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        PageManager.go_to_dir('img')
        path = os.getcwd() + '\\' + str(short_id) + '.jpg'
        print("path: " + str(path))
        await file.download_to_drive(path)
        print("Imagen descargada con éxito.")



