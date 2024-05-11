import threading
from abc import abstractmethod


class PageRunner(threading.Thread):
    #Clase encargada de la ejecución de las páginas web. En ella se deben definir los métodos para la gestión de estas páginas.
    user:str
    page_name:str
    page_port:int
    running_thread:threading.Thread
    target:any
    process:any

    @abstractmethod
    def __init__(self, user, page_name, page_port):
        super().__init__()
        self.user = user
        self.page_name = page_name
        self.page_port = page_port
        self.running_thread = None
        self.target = None
        self.process = None
        pass

    def set_target(self, target):
        self.target = target

    def set_process(self, process):
        self.process = process

    def start_running_thread(self, target, args):
        print("----EN START RUNNING THREAD----")
        print("THREAD ID: " + threading.currentThread().getName())
        print("target: " + str(target))
        print("cant args: " + str(len(args)))
        print("args: " + str(args))
        if self.running_thread is None:
            print("el hilo es None")
            if len(args) == 2:
                self.running_thread = threading.Thread(target=target, args=args)
            else:
                self.running_thread = threading.Thread(target=target, args=args)
            print("despues de crear el nuevo hilo")
            self.running_thread.start()
            print("THREAD ID: " + threading.currentThread().getName())
        else:
            print("el hilo no es None")
            self.join_running_thread()
            self.start_running_thread(target, args)

    def join_running_thread(self):
        print("----EN JOIN RUNNING THREAD----")
        if self.running_thread is not None:
            print("el hilo no es None")
            self.process.wait()
            self.running_thread.join()
            print("despues de join()")
            self.running_thread = None
            print("despues de asignar None")
        else:
            print("el hilo es None")


    @abstractmethod
    def run(self):
        pass

