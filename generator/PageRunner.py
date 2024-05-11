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
        if self.running_thread is None:
            if len(args) == 2:
                self.running_thread = threading.Thread(target=target, args=args)
            else:
                self.running_thread = threading.Thread(target=target, args=args)
            self.running_thread.start()
        else:
            self.join_running_thread()
            self.start_running_thread(target, args)

    def join_running_thread(self):
        if self.running_thread is not None:
            self.process.wait()
            self.running_thread.join()
            self.running_thread = None


    @abstractmethod
    def run(self):
        pass

