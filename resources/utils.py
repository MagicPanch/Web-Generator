import os
import shutil

import psutil

from resources import CONSTANTS

def go_to_dir(dir_name):
    # Nos posiciona en el subdirectorio indicado. Si no existe, lo crea
    os.makedirs(dir_name, exist_ok=True)
    os.chdir(dir_name)

def go_to_main_dir():
    while os.path.basename(os.getcwd()) != CONSTANTS.MAIN_DIR:
        os.chdir("..")

def go_to_dir_from_main(dir_name):
    go_to_main_dir()
    go_to_dir(dir_name)

def copy_dir(origen, destino):
    # Copiar el contenido del directorio origen al directorio destino
    shutil.copytree(origen, destino, dirs_exist_ok=True)

def write_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)
        file.close()

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


def get_process(port):
    pid = get_pid(port)
    print("pid:", pid)
    return psutil.Process(pid)
