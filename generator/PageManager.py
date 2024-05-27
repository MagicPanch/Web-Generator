import os
import random
import shutil
import subprocess
import threading
from typing import Tuple, Dict, List

import requests

from resources import CONSTANTS, utils
import psutil
from database.DBManager import DBManager
from generator.objects.pages.Front import Front
from generator.ReactGenerator import ReactGenerator
import socket
from generator.objects.sections.EcommerceSection import EcommerceSection
from generator.objects.sections.InformativeSection import InformativeSection


class PageManager(object):

    class Entry():
        def __init__(self, page:Front, thread_exec, thread_tunnel):
            self._page = page
            self._thread_exec = thread_exec
            self._thread_tunnel = thread_tunnel

        def set_page(self, page:Front):
            self._page = page

        def get_page(self) -> Front:
            return self._page

        def set_thread_exec(self, thread):
            self._thread_exec = thread

        def get_thread_exec(self):
            return self._thread_exec

        def set_thread_tunnel(self, thread):
            self._thread_tunnel = thread

        def get_thread_tunnel(self):
            return self._thread_tunnel


    _instance = None
    _running_pages: Dict[Tuple[str, str], Entry]= {}
    _tunnel_pwd:str = None

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
    def get_tunnel_password() -> str:
        if not PageManager._tunnel_pwd:
            try:
                # Realizar la solicitud HTTP GET
                response = requests.get(CONSTANTS.LOCAL_TUNNEL_PASSWORD_URL)
                # Verificar si la solicitud fue exitosa (código de estado 200)
                if response.status_code == 200:
                    # Extraer la dirección IP del cuerpo de la respuesta
                    ip = response.text.strip()
                    PageManager._tunnel_pwd = ip
                else:
                    print("(" + threading.current_thread().getName() + ") " + f"Error: Código de estado {response.status_code}")
            except requests.exceptions.RequestException as e:
                print("(" + threading.current_thread().getName() + ") " + f"Error al realizar la solicitud: {e}")
        return str(PageManager._tunnel_pwd)

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PageManager()
        return cls._instance

    def __init__(self) -> None:
        if PageManager._instance is None:
            PageManager._instance = self
            self._running_pages = {}
        else:
            raise Exception("No se puede crear otra instancia de PageManager")

    @staticmethod
    def _get_tunnel_address(page, dev=False):
        print("(" + threading.current_thread().getName() + ") " + "----EN GET TUNNEL ADDRESS----")
        page.clear_address_event()
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
        page.set_addres_event()

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
    def _create_project(user, page_name):
        #Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)
        os.chdir(path)

        #Iniciar la creacion del proyecto y esperar a que termine
        command = 'npx create-next-app . --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        process = PageManager._run_process(command)

        #Capturar su salida
        it = True
        while it:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                decoded_output = output.decode().strip()
                if "Success" in decoded_output:
                    it = False
                print("(" + threading.current_thread().getName() + ") " + decoded_output)

        process.wait()
        process.terminate()

        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(None)

        #Copiar los templates al proyecto creado
        PageManager._copy_template(user, page_name)
        dataHeader = {"titulo": page_name,
            "address": path,
            "addressLogo": "./logo.png",
            "colorTitulo": "#12D7BF"
        }
        ReactGenerator.generarHeader(dataHeader)
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
        utils.go_to_main_dir()

        #Obtener directorio destino
        destino = PageManager.get_page_path(user, page_name)
        #print("(" + threading.current_thread().getName() + ") " + "--------destino: " + destino)

        #Copiar template al nuevo proyecto
        utils.copy_dir(CONSTANTS.TEMPLATE_DIR, destino)

    @staticmethod
    def _run_dev(user, page_name, page_port):
        # Ejecuta la página en modo Dev para que el usuario visualice las modificaciones
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._run_dev----")

        path = PageManager.get_page_path(user, page_name)

        # Posicionarse en el path donde se ejecutará el proyecto
        utils.go_to_dir_from_main(path)

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

        #Iniciar tunel de la página
        thread_tunnel = threading.Thread(target=PageManager._get_tunnel_address, args=(page, True))
        PageManager._running_pages[(user, page_name)].set_thread_tunnel(thread_tunnel)
        thread_tunnel.start()

        #Si la página tiene sección e-commerce, asignar la dirección
        page_path = PageManager.get_page_path(user, page_name)
        if page.has_ecomm_section():
            ReactGenerator.set_address(page_path=page_path, address=PageManager.get_page(user, page_name).get_page_address())

        #Iniciar la ejecución de la página
        thread_exec = threading.Thread(target=PageManager._run_dev, args=(user, page_name, page.get_port()))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread_exec)
        thread_exec.start()
        page.wait_for_ready()
        page.set_running_dev(True)

    @staticmethod
    def _add_ecommerce(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._add_ecommerce----")

        #Posicionarse en el directorio de la página
        page_path = PageManager.get_page_path(user, page_name)
        utils.go_to_dir_from_main(page_path)

        #Instalar dependencias
        command = 'npm install mongodb'
        process = PageManager._run_process(command)
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_exec_process(process)
        process.wait()
        process.terminate()
        page.set_exec_process(None)

        command = 'npm install --save-dev @types/mongodb'
        process = PageManager._run_process(command)
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_exec_process(process)
        process.wait()
        process.terminate()
        page.set_exec_process(None)

        command = 'npm install mongoose dotenv'
        process = PageManager._run_process(command)
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_exec_process(process)
        process.wait()
        process.terminate()
        page.set_exec_process(None)

        # Copiar template al nuevo proyecto
        destino = PageManager.get_page_path(user, page_name)
        utils.go_to_main_dir()
        utils.copy_dir(CONSTANTS.TEMPLATE_ECOMMERCE_DIR, destino)

        # Asignar el nombre de su colección en la base de datos
        ReactGenerator.set_collection(page_path=destino, collection=(user + "-" + page_name))

    @staticmethod
    def add_ecommerce(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.add_ecommerce----")
        page = PageManager._running_pages[(user, page_name)].get_page()

        if page.is_running():
            PageManager.switch_dev(user, page_name)

        # Instalar sus dependencias y copiar template
        PageManager._add_ecommerce(user, page_name)

    @staticmethod
    def _build_project(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._build_project----")

        #Posicionarse en el path donde se creara el proyecto
        path = PageManager.get_page_path(user, page_name)

        utils.go_to_dir_from_main(path)

        command = 'npx next build '
        process = PageManager._run_process(command)

        # Capturar su salida
        it = True
        while it:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                decoded_output = output.decode().strip()
                if "(Static)" in decoded_output:
                    it = False
                print("(" + threading.current_thread().getName() + ") " + decoded_output)

        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(process)
        process.wait()
        process.terminate()
        PageManager._running_pages[(user, page_name)].get_page().set_exec_process(None)

    @staticmethod
    def build_project(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.build_project----")
        page = PageManager._running_pages[(user, page_name)].get_page()

        # Iniciar tunel de la página
        thread_tunnel = threading.Thread(target=PageManager._get_tunnel_address, args=(page, False))
        PageManager._running_pages[(user, page_name)].set_thread_tunnel(thread_tunnel)
        thread_tunnel.start()

        # Si la página tiene sección e-commerce, asignar la dirección
        page_path = PageManager.get_page_path(user, page_name)
        if page.has_ecomm_section():
            ReactGenerator.set_address(page_path=page_path, address=PageManager.get_page(user, page_name).get_page_address())

        # Iniciar la compilación de la página
        thread_exec = threading.Thread(target=PageManager._build_project, args=(user, page_name))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread_exec)
        thread_exec.start()

    @staticmethod
    def _run_project(user, page_name, page_port):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager._run_project----")

        #Posicionarse en el path de la página
        path = PageManager.get_page_path(user, page_name)
        utils.go_to_dir_from_main(path)

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

        # Verificar si la página tiene un tunel activo
        thread_tunnel = PageManager._running_pages[(user, page_name)].get_thread_tunnel()
        if thread_tunnel is None:
            # Iniciar el tunel de la página
            thread_tunnel = threading.Thread(target=PageManager._get_tunnel_address, args=(page, False))
            PageManager._running_pages[(user, page_name)].set_thread_tunnel(thread_tunnel)
            thread_tunnel.start()

        # Iniciar la ejecución de la página
        thread_exec = threading.Thread(target=PageManager._run_project, args=(user, page_name, page.get_port()))
        PageManager._running_pages[(user, page_name)].set_thread_exec(thread_exec)
        thread_exec.start()
        page.set_running(True)
        page.wait_for_ready()

    @staticmethod
    def join_thread_exec(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.join_thread_exec----")
        thread_exec = PageManager._running_pages[(user, page_name)].get_thread_exec()
        if thread_exec is not None:
            print("(" + threading.current_thread().getName() + ") " + "--------hilo a esperar: ", thread_exec.getName())
            thread_exec.join()
            PageManager._running_pages[(user, page_name)].set_thread_exec(None)
        print("(" + threading.current_thread().getName() + ") " + "----finalizo la espera de ", thread_exec.getName())

    @staticmethod
    def join_thread_tunnel(user, page_name):
        print("(" + threading.current_thread().getName() + ") " + "----PageManager.join_thread_tunnel----")
        thread_tunnel = PageManager._running_pages[(user, page_name)].get_thread_tunnel()
        if thread_tunnel is not None:
            print("(" + threading.current_thread().getName() + ") " + "--------hilo a esperar: ", thread_tunnel.getName())
            thread_tunnel.join()
            PageManager._running_pages[(user, page_name)].set_thread_tunnel(None)
        print("(" + threading.current_thread().getName() + ") " + "----finalizo la espera de ", thread_tunnel.getName())

    @staticmethod
    def add_page(user, page_name) -> Front:
        #Crear la pagina
        page = Front(user, page_name, PageManager.get_port())

        #Recuperar sus componentes
        dbm = DBManager.get_instance()
        sections = dbm.get_page_sections(user, page_name)
        for section in sections:
            print(section)
            if section.type == "informativa":
                s = InformativeSection(section.title)
                s.set_text(section.text)
                page.add_section(s)
            elif section.type == "ecommerce":
                s = EcommerceSection()
                page.add_section(s)

        #Crea sus directorios
        utils.go_to_main_dir()
        utils.go_to_dir(CONSTANTS.USER_PAGES_DIR)
        utils.go_to_dir(user)
        utils.go_to_dir(page_name)
        utils.go_to_main_dir()
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
    def is_alive(user, page_name) -> bool:
        entry = PageManager._running_pages.get((user, page_name))
        if entry:
            return entry.get_page().is_running()
        else:
            return False

    @staticmethod
    def switch_dev(user, page_name):
        #Detener la ejecucion de la pagina
        PageManager.stop_page(user, page_name)
        PageManager.stop_tunnel(user, page_name)

        #Iniciar la ejecucion en modo dev
        PageManager.run_dev(user, page_name)

    @staticmethod
    def stop_tunnel(user, page_name):
        page = PageManager._running_pages[(user, page_name)].get_page()

        #Detener el proceso con el http tunnel
        tunnel_process = page.get_tunnel_process()
        tunnel_process.terminate()
        tunnel_process.wait()

        #Detener el hilo
        PageManager.join_thread_tunnel(user, page_name)

    @staticmethod
    def stop_page(user, page_name):
        # Matar la página
        print("(" + threading.current_thread().getName() + ") " + "----EN STOP_PAGE----")
        page = PageManager._running_pages[(user, page_name)].get_page()
        page.set_running(False)
        page.set_running_dev(False)


        #Detener el proceso con la ejecucion de la pagina
        PageManager.kill_project(page.get_port())

        #Esperar por la finalizacion del hilo
        PageManager.join_thread_exec(user, page_name)

    @staticmethod
    def pop_page(user, page_name):
        PageManager._running_pages.pop(user, page_name)

    @staticmethod
    def kill_project(port):
        process = utils.get_process(port)
        process.terminate()
        process.wait()


