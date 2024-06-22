import io
import os
import shutil

import psutil
import requests

from resources import CONSTANTS
from imgurpython import ImgurClient

imgur_client = ImgurClient(CONSTANTS.IMGUR_CLIENT_ID, CONSTANTS.IMGUR_API_SECRET)

def upload_image(image_source_url) -> str:
    response = requests.get(image_source_url)
    if response.status_code == 200:
        image_data = response.content
        headers = { 'Authorization': f'Client-ID {CONSTANTS.IMGUR_CLIENT_ID}'}
        imgur_response = requests.post('https://api.imgur.com/3/upload', headers=headers, files={'image': image_data})
        if imgur_response.status_code == 200:
            response_data = imgur_response.json()
            image_url = response_data['data']['link']
            print(f"Imagen subida correctamente. Enlace: {image_url}")
            return image_url
        else:
            print(f"Error subiendo la imagen a Imgur: {imgur_response.status_code}")
            print(imgur_response.json())
    else:
        print(f"Error descargando la imagen de Telegram: {response.status_code}")
        print(response.json())
    return ""

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
    return psutil.Process(pid)
