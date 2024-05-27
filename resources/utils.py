import os
import shutil

from resources import CONSTANTS

def go_to_dir(dir_name):
    # Nos posiciona en el subdirectorio indicado. Si no existe, lo crea
    os.makedirs(dir_name, exist_ok=True)
    os.chdir(dir_name)

def go_to_main_dir():
    while os.path.basename(os.getcwd()) != CONSTANTS.MAIN_DIR:
        os.chdir("..")

def copy_dir(origen, destino):
    # Copiar el contenido del directorio origen al directorio destino
    shutil.copytree(origen, destino, dirs_exist_ok=True)