import os
import sys
import wexpect


import CONSTANTS

def go_to_dir(dir_name):
    #Nos posiciona en el directorio indicado. Si no existe, lo crea
    print(os.getcwd(), dir_name)
    os.makedirs(dir_name, exist_ok=True)
    os.chdir(dir_name)
    print(os.getcwd())

def go_to_main_dir():
    #Nos posiciona en el directorio user-pages
    print(os.getcwd())
    if os.path.basename(os.getcwd()) == CONSTANTS.MAIN_DIR:
        os.chdir(CONSTANTS.USER_PAGES_DIR)
    elif os.path.basename(os.getcwd()) == CONSTANTS.GENERATOR_DIR:
        os.chdir("..")
        os.chdir(CONSTANTS.USER_PAGES_DIR)
    else:
        while os.path.basename(os.getcwd()) != CONSTANTS.USER_PAGES_DIR:
            os.chdir("..")
            print(os.getcwd())

def create_project(name):
    print(os.getcwd())
    command = 'npx create-next-app ' + name + ' --typescript --eslint --tailwind'
    print(command)

    process = wexpect.spawn(command)
    print('despues de spawn')
    process.logfile_read = sys.stdout
    process.logfile = sys.stderr
    # Interactuar con el proceso
    try:
        # Esperar a que el proceso solicite una respuesta
        while True:
            # Esperar hasta que el proceso muestre una salida específica o finalice
            i = process.expect([
                wexpect.EOF,  # Fin del proceso
                wexpect.TIMEOUT,  # Tiempo de espera agotado
                'Would you like to use `src/` directory?',
                'Would you like to use App Router? (recommended)',
                'Would you like to customize the default import alias (@/*)?'
            ])
            print(i)

            # Proporcionar respuestas automáticas
            if i == 0:  # Proceso finalizado
                print('El proceso ha finalizado.')
                break
            elif i == 1:  # Tiempo de espera agotado
                print('Tiempo de espera agotado.')
                break
            elif i == 2:
                process.send('\x1b[C')
                process.sendline()
            elif i == 3:  # Responder a otra pregunta específica
                process.sendline()
            elif i == 4:
                process.sendline()
    except wexpect.ExceptionWexpect as e:

        print(f"Error: {e}")

    # Cerrar el proceso
    process.close()

go_to_main_dir()
go_to_dir('user_prueba')
go_to_dir('page_prueba')
create_project('page_prueba')
