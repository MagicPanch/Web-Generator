import os
import wexpect
import CONSTANTS

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
        os.makedirs(dir_name, exist_ok=True)
        os.chdir(dir_name)

    @staticmethod
    def go_to_main_dir():
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

    @staticmethod
    def create_project(user, page_name):
        #Crea el proyecto de la página
        Generator.go_to_main_dir()
        Generator.go_to_dir(user)
        command = 'npx create-next-app ' + page_name + ' --typescript --eslint --tailwind --app --src-dir --no-import-alias'
        wexpect.run(command)



