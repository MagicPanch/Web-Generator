import os
import subprocess
import CONSTANTS
import psutil

class Generator(object):

    _instance = None
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = Generator()
        return cls._instance

    def __init__(self) -> None:
        if Generator._instance is None:
            Generator._instance = self
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
    def get_user_pages(user):
        Generator.go_to_main_dir()
        Generator.go_to_dir(user)
        return os.listdir(os.getcwd())

    @staticmethod
    def create_project(user, page_name):
        #Crea el proyecto de la página
        Generator.go_to_main_dir()
        Generator.go_to_dir(user)
        command = 'npx create-next-app ' + page_name + ' --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        process = subprocess.Popen(command, shell=True)
        process.wait()

    @staticmethod
    def build_project(user, page_name):
        Generator.go_to_main_dir()
        Generator.go_to_dir(user)
        Generator.go_to_dir(page_name)

        command = 'npx next build '
        process = subprocess.Popen(command, shell=True)
        process.wait()

    @staticmethod
    def run_project(user, page_name, port):
        Generator.go_to_main_dir()
        Generator.go_to_dir(user)
        Generator.go_to_dir(page_name)

        command = 'npm start -- --port ' + str(port)
        process = subprocess.Popen(command, shell=True)
        process.terminate()

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
        process = psutil.Process(Generator.get_pid(port))
        process.terminate()
        process.wait()


