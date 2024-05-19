import os
import random
import shutil
import socket
import subprocess
import threading
from typing import Tuple, Dict, List

import requests
from telegram import Bot
import CONSTANTS
import psutil
from generator.Front import Front
import socket


class PageManager(object):

    class Entry():
        def __init__(self, page, thread_exec, thread_tunnel):
            self._page = page
            self._thread_exec = thread_exec
            self._thread_tunnel = thread_tunnel

        def set_page(self, page):
            self._page = page

        def get_page(self):
            return self._page

        def set_thread_exec(self, thread):
            self._thread = thread

        def get_thread_exec(self):
            return self._thread

        def set_thread_tunnel(self, thread):
            self._thread = thread

        def get_thread_tunnel(self):
            return self._thread


    _instance = None
    _running_pages: Dict[Tuple[str, str], Entry]= {}

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

    @staticmethod
    def get_tunnel_password():
        try:
            # Realizar la solicitud HTTP GET
            response = requests.get(CONSTANTS.LOCAL_TUNNEL_PASSWORD_URL)
            # Verificar si la solicitud fue exitosa (código de estado 200)
            if response.status_code == 200:
                # Extraer la dirección IP del cuerpo de la respuesta
                ip = response.text.strip()
                return ip
            else:
                print(f"Error: Código de estado {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud: {e}")

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PageManager()
        return cls._instance

    def __init__(self) -> None:
        if PageManager._instance is None:
            PageManager._instance = self
            self._running_pages = {}
            self._bot = Bot(token=CONSTANTS.TELEGRAM_BOT_TOKEN)
        else:
            raise Exception("No se puede crear otra instancia de PageManager")

    @staticmethod
    def go_to_dir(dir_name):
        #Nos posiciona en el subdirectorio indicado. Si no existe, lo crea
        os.makedirs(dir_name, exist_ok=True)
        os.chdir(dir_name)
        #print("(" + threading.current_thread().getName() + ") " + "nuevo dir: " + os.getcwd())

    @staticmethod
    def go_to_main_dir():
        while os.path.basename(os.getcwd()) != CONSTANTS.MAIN_DIR:
            os.chdir("..")
        #print("(" + threading.current_thread().getName() + ") " + "nuevo dir: " + os.getcwd())

    @staticmethod
    def _get_tunnel_address(page, dev=False):
        print("(" + threading.current_thread().getName() + ") " + "----EN GET NGROK ADDRESS----")
        #Ejecutar el proceso
        if dev:
            command = 'lt --port ' + str(page.get_port())
        else:
            command = 'lt --port ' + str(page.get_port()) + " --subdomain " + page.get_name()
        process = PageManager._run_process(command)
        page.set_tunnel_process(process)
        address = None

        it = True
        #Capturar su salida
        while it:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                decoded_output = output.decode().strip()
                print("(" + threading.current_thread().getName() + ") " + decoded_output)
                if "https:" in decoded_output:
                    it = False
                    address = decoded_output[decoded_output.index("https")::]
        page.set_page_address(address)

    @staticmethod
    def _run_process(command):
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.getcwd(), shell=True)
        #return subprocess.Popen(command, shell=True)

    @staticmethod
    def get_user_running_pages(user) -> List[Front]:
        pages = []
        for key in PageManager._running_pages.keys():
            if key[0] == user:
                # Agregar la pagina al resultado
                pages.append(PageManager._running_pages[key].get_page())
        return pages

    @staticmethod
    def _copy_dir(origen, destino):
        # Copiar el contenido del directorio origen al directorio destino
        shutil.copytree(origen, destino, dirs_exist_ok=True)

    @staticmethod
    def _create_project(user, page_name):
        #Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)
        os.chdir(path)

        #Iniciar la creacion del proyecto y esperar a que termine
        command = 'npx create-next-app . --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        process = PageManager._run_process(command)
        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(process)
        process.wait()
        process.terminate()
        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(None)

        #Copiar los templates al proyecto creado
        PageManager._copy_template(user, page_name)
        print("(" + threading.current_thread().getName() + ") " + "----Ejecucion finalizada----")

    @staticmethod
    def create_project(user, page_name):
        #print("(" + threading.current_thread().getName() + ") " + "----PageManager.create_project----")
        thread = threading.Thread(target= PageManager._create_project, args=(user, page_name))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread)
        thread.start()

    @staticmethod
    def _copy_template(user, page_name):
        #Se copian los templates en el nuevo proyecto
        #print("(" + threading.current_thread().getName() + ") " + "----PageManager._copy_template----")
        #print("(" + threading.current_thread().getName() + ") " + "--------origen: " + CONSTANTS.TEMPLATE_DIR)
        PageManager.go_to_main_dir()

        #Obtener directorio destino
        destino = PageManager.get_page_path(user, page_name)
        #print("(" + threading.current_thread().getName() + ") " + "--------destino: " + destino)

        #Copiar template al nuevo proyecto
        PageManager._copy_dir(CONSTANTS.TEMPLATE_DIR, destino)

    @staticmethod
    def _run_dev(user, page_name, page_port):
        # Ejecuta la página en modo Dev para que el usuario visualice las modificaciones
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._run_dev----")

        #Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)
        os.chdir(path)

        #Ejecutar el proceso
        command = 'npm run dev -- --port=' + str(page_port)
        process = PageManager._run_process(command)
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_exec_process(process)

        #Capturar su salida
        it = True
        while it:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                decoded_output = output.decode().strip()
                it = page.append_output(decoded_output)
                print("(" + threading.current_thread().getName() + ") " + decoded_output)

    @staticmethod
    def run_dev(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.run_dev----")
        page = PageManager._running_pages[(user, page_name)].get_page()
        thread_exec = threading.Thread(target=PageManager._run_dev, args=(user, page_name, page.get_port()))
        thread_tunnel = threading.Thread(target=PageManager._get_tunnel_address, args=(page, True))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread_exec)
        PageManager._running_pages[(user, page_name)].set_thread_tunnel(thread_tunnel)
        thread_exec.start()
        thread_tunnel.start()

    @staticmethod
    def _build_project(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._build_project----")

        #Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)
        PageManager.go_to_main_dir()
        os.chdir(path)

        command = 'npx next build '
        process = PageManager._run_process(command)
        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(process)
        process.wait()
        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(None)

    @staticmethod
    def build_project(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.build_project----")
        thread = threading.Thread(target=PageManager._build_project, args=(user, page_name))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread)
        thread.start()

    @staticmethod
    def _run_project(user, page_name, page_port):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._run_project----")
        page = PageManager._running_pages[(user, page_name)].get_page()

        #Posicionarse en el path donde se creara el proyecto
        # Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)
        PageManager.go_to_main_dir()
        os.chdir(path)


        command = 'npm start -- --port ' + str(page_port)
        process = PageManager._run_process(command)
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_exec_process(process)

        # Capturar su salida
        it = True
        while it:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                decoded_output = output.decode().strip()
                it = page.append_output(decoded_output)
                print("(" + threading.current_thread().getName() + ") " + decoded_output)

    @staticmethod
    def run_project(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.run_project----")
        page = PageManager._running_pages[(user, page_name)].get_page()
        thread_exec = threading.Thread(target=PageManager._run_project, args=(user, page_name, page.get_port()))
        thread_tunnel = threading.Thread(target=PageManager._get_tunnel_address, args=(page, False))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread_exec)
        PageManager._running_pages[(user, page_name)].set_thread_tunnel(thread_tunnel)
        thread_exec.start()
        thread_tunnel.start()
        page.set_running(True)

    @staticmethod
    def join_thread(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.join_thread----")
        thread_exec = PageManager._running_pages[(user, page_name)].get_thread_exec()
        if thread_exec:
            print("(" + threading.current_thread().getName() + ") " + "--------hilo a esperar: ", thread_exec.getName())
            thread_exec.join()
            print("(" + threading.current_thread().getName() + ") " + "--------finalizo la espera de ", thread_exec.getName())
            PageManager._running_pages[(user, page_name)].set_thread_exec(None)
        thread_tunnel = PageManager._running_pages[(user, page_name)].get_thread_tunnel()
        if thread_tunnel:
            print("(" + threading.current_thread().getName() + ") " + "--------hilo a esperar: ", thread_tunnel.getName())
            thread_tunnel.join()
            print("(" + threading.current_thread().getName() + ") " + "--------finalizo la espera de ", thread_tunnel.getName())
            PageManager._running_pages[(user, page_name)].set_thread_tunnel(None)

    @staticmethod
    def add_page(user, page_name) -> Front:
        #Crear la pagina
        page = Front(user, page_name, PageManager.get_port())

        #Crea sus directorios
        PageManager.go_to_main_dir()
        PageManager.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        PageManager.go_to_dir(user)
        PageManager.go_to_dir(page_name)
        PageManager.go_to_main_dir()

        #Agregarla a la coleccion
        PageManager._running_pages[(user, page_name)] = PageManager.Entry(page, None, None)
        return page

    @staticmethod
    def get_page(user, page_name) -> Front:
        entry = PageManager._running_pages.get((user, page_name))
        if entry:
            return entry.get_page()
        else:
            return None

    @staticmethod
    def get_thread_exec(user, page_name) -> threading.Thread:
        return PageManager._running_pages[(user, page_name)].get_thread_exec()

    @staticmethod
    def get_thread_tunnel(user, page_name) -> threading.Thread:
        return PageManager._running_pages[(user, page_name)].get_thread_tunnel()

    @staticmethod
    def get_page_path(user, page_name) -> str:
        path = CONSTANTS.USER_PAGES_DIR + "\\" + user + "\\" + page_name
        return path

    @staticmethod
    def is_running(user, page_name) -> bool:
        entry = PageManager._running_pages.get((user, page_name))
        if entry:
            return entry.get_page().is_running()
        else:
            return False

    @staticmethod
    def stop_page(user, page_name):
        # Matar la página
        print("(" + threading.current_thread().getName() + ") " + "----EN STOP_PAGE----")
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_running(False)


        #Detener el proceso con la ejecucion de la pagina
        PageManager.kill_project(page.get_port())

        #Detener el proceso con el http tunnel
        tunnel_process = page.get_tunnel_process()
        tunnel_process.terminate()
        tunnel_process.wait()

        #Esperar por la finalizacion del hilo
        thread_exec = PageManager._running_pages[(user, page_name)].get_thread_exec()
        thread_exec.join()
        thread_tunnel = PageManager._running_pages[(user, page_name)].get_thread_tunnel()
        thread_tunnel.join()

        #Eliminar la entrada de la pagina
        PageManager._running_pages.pop((user, page_name))

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
        page_path = PageManager.get_page_path(user, page_name)
        file = await self._bot.get_file(image_id)
        PageManager.go_to_dir("components")
        path = os.getcwd() + "\\" + page_path + '\\components\\' + str(short_id) + '.png'
        print("path to save: ", os.getcwd() + '\\' + str(short_id) + '.png')
        print("current path: ", os.getcwd())
        await file.download_to_drive(custom_path=os.getcwd()+ '\\' + str(short_id) + '.png')
        PageManager.go_to_main_dir()


